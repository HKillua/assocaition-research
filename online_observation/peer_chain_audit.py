"""Audit the original MTAD peer publications without running a prediction arm."""

from __future__ import annotations

import argparse
from collections import Counter
import gzip
from itertools import pairwise
import json
import math
from pathlib import Path
from time import perf_counter

from .continuous_tracker import FRESH_S
from .evaluation_data import read_labels
from .peer_chain_intervals import endpoint_status, false_chains, frame_cuts, frozen_frames
from .peer_chain_lineage import edge_lineage, indirect_report_tags
from .peer_experiment import BOUNDARY_S, MANIFEST, _native_events, _scene_roster
from .peer_replay import replay_frames

ARMS = ("state_20s", "frechet_penalty_20s", "frechet_masked_20s")
FOCUS = ("4827", "3062", "4409")
PLAN = "IDEA-ONLINE-PEER-CHAIN-LINEAGE-20261114-v1.3"
DEVELOPMENT_PLAN = "IDEA-ONLINE-PEER-ADAPTATION-20261114-v1.2"


def _read_json(path):
    with path.open(encoding="utf-8") as source:
        return json.load(source)


def _read_frames(path):
    with gzip.open(path, "rt", encoding="utf-8") as source:
        return tuple(frozen_frames(map(json.loads, source)))


def _equal(value, expected):
    if not math.isclose(value, expected, rel_tol=0, abs_tol=1e-7):
        raise ValueError(f"duration does not reconcile: {value} vs {expected}")


def _check_frozen(frames, expected_stamps, expected_reports, stop):
    if (tuple(frame.stamp for frame in frames) != expected_stamps
            or tuple(frame.reports for frame in frames) != expected_reports
            or not frames or frames[-1].stamp != stop):
        raise ValueError("frozen release clocks or member report supports differ")
    if any(not math.isclose(right - left, 20, rel_tol=0, abs_tol=1e-9)
           for left, right in pairwise(expected_stamps)):
        raise ValueError("expected the original 20 second release clock")


def _chain_stats(chains):
    long_chains = [chain for chain in chains if chain.end > chain.start + FRESH_S]
    return dict(
        count=len(chains), pair_seconds=math.fsum(chain.end - chain.start for chain in chains),
        long_count=len(long_chains), long_seconds=math.fsum(chain.end - chain.start for chain in long_chains),
        longest_seconds=max((chain.end - chain.start for chain in chains), default=0.0),
        ends=dict(Counter(chain.reason for chain in chains)),
    )


def _check_chains(chains, score):
    stats = _chain_stats(chains)
    if (stats["count"] != score["chains"] or stats["long_count"] != score["over_60_seconds"]["chains"]
            or stats["ends"] != score["ends"]):
        raise ValueError("reconstructed wrong-chain counts differ from original score")
    _equal(stats["pair_seconds"], score["pair_seconds"])
    _equal(stats["long_seconds"], score["over_60_seconds"]["pair_seconds"])
    _equal(stats["longest_seconds"], score["duration_seconds"]["max"] or 0.0)
    return stats


def _live_edges(frame, stamp):
    return {
        (key, peer) for key, peer in frame.partners.items()
        if key < peer and stamp < min(frame.reports[key], frame.reports[peer]) + FRESH_S
    }


def _compare(reference, other, reference_chains, other_chains, labels, stop, lineage_frames):
    source_long = {chain.edge: [] for chain in reference_chains if chain.end > chain.start + FRESH_S}
    for chain in reference_chains:
        if chain.edge in source_long and chain.end > chain.start + FRESH_S:
            source_long[chain.edge].append(chain)
    other_long = {}
    for chain in other_chains:
        if chain.end > chain.start + FRESH_S:
            other_long.setdefault(chain.edge, []).append(chain)

    endpoint_seconds, joint_seconds, overlap_seconds = Counter(), Counter(), Counter()
    gains, losses = Counter(), Counter()
    categories = {}
    timing_support = {}
    tags, indirect_tags = {}, {}
    lineage_detail = {}
    first_change = set()
    onset_support = {}
    prior_relations = {}
    changed = {}
    per_chain = {
        (chain.edge, chain.start): dict(
            start=chain.start, end=chain.end, reason=chain.reason, endpoint_seconds=Counter(),
            first_change=None, first_true_replacement=None,
        )
        for chains in source_long.values() for chain in chains
    }

    def lineage(edge, windows, role, seconds, seen):
        if edge not in seen:
            tally = categories.setdefault(role, Counter())
            support_tags = tags.setdefault(role, set())
            if all(key in windows[-1] for key in edge):
                support = edge_lineage(edge, windows)
                seen[edge] = support.category
                support_tags.update(support.report_tags)
                lineage_detail.setdefault(role, Counter())[(support.common_grids, support.distinct_tag_pairs)] += 1
                intermediate = indirect_report_tags(edge, lineage_frames[max(0, index - 2):index + 1], support)
                indirect_tags.setdefault(role, set()).update(intermediate)
            else:
                seen[edge] = "missing_at_boundary"
            tally[seen[edge]] += 1
        timing_support.setdefault(role, Counter())[seen[edge]] += seconds
        return seen[edge]

    for index, (first, second) in enumerate(zip(reference, other)):
        end = reference[index + 1].stamp if index + 1 < len(reference) else stop
        cuts = frame_cuts(first, second, end)
        windows = [frame.reports for frame in reference[max(0, index - 2):index + 1]]
        per_boundary = {}
        current_long = {
            edge: chain for edge in first.partners.items()
            if edge[0] < edge[1] and edge in source_long
            for chain in source_long[edge] if chain.start <= first.stamp < chain.end
        }
        for start, end in pairwise(cuts):
            seconds = end - start
            if seconds <= 0:
                continue
            old = _live_edges(first, start)
            new = _live_edges(second, start)
            for action, edges, counter in (("new", new - old, gains), ("removed", old - new, losses)):
                for edge in edges:
                    truth = labels[edge[0]] == labels[edge[1]]
                    value = "true" if truth else "false"
                    counter[value] += seconds
                    lineage(edge, windows, f"all_{action}_{value}", seconds,
                            per_boundary.setdefault(f"all_{action}_{value}", {}))
            for edge in old & new:
                if labels[edge[0]] == labels[edge[1]]:
                    lineage(edge, windows, "unchanged_true", seconds,
                            per_boundary.setdefault("unchanged_true", {}))
            novel_replacements = set()
            for edge in old & current_long.keys():
                chain = current_long[edge]
                if not (chain.start <= start < chain.end):
                    continue
                chain_key = (edge, chain.start)
                if edge in new:
                    other_kind = "short_same_edge"
                    if any(c.start <= start < c.end for c in other_long.get(edge, ())):
                        other_kind = "long_same_edge"
                    overlap_seconds[other_kind] += seconds
                    relationship = ("same_false", "same_false")
                    prior_relations.pop(chain_key, None)
                    lineage(edge, windows, "retained_long_false", seconds,
                            per_boundary.setdefault("retained_long_false", {}))
                else:
                    overlap_seconds["absent_same_edge"] += seconds
                    relationship = tuple(endpoint_status(second, key, peer, labels, start)
                                         for key, peer in (edge, edge[::-1]))
                    base_category = lineage(edge, windows, "changed_old_long_false", seconds,
                                            per_boundary.setdefault("changed_old_long_false", {}))
                    replacements = {}
                    for key, status in zip(edge, relationship):
                        if status in ("other_true", "other_false"):
                            new_edge = tuple(sorted((key, second.partners[key])))
                            novel_replacements.add((new_edge, status))
                            replacements[new_edge] = status
                    detail = per_chain[chain_key]
                    if detail["first_true_replacement"] is None and "other_true" in replacements.values():
                        true_support = sorted({edge_lineage(pair, windows).category
                                               for pair, status in replacements.items() if status == "other_true"})
                        detail["first_true_replacement"] = dict(
                            seconds_from_start=start - chain.start, support=true_support,
                        )
                        for support in true_support:
                            onset_support.setdefault("first_true_replacement", Counter())[support] += 1
                    if chain_key not in first_change:
                        first_change.add(chain_key)
                        support_by_truth = {
                            status: sorted({
                                edge_lineage(pair, windows).category
                                for pair, outcome in replacements.items() if outcome == status
                            })
                            for status in ("other_true", "other_false")
                        }
                        grade = "+".join(relationship)
                        onset_support.setdefault(grade, Counter())[base_category] += 1
                        for status, supports in support_by_truth.items():
                            for support in supports:
                                onset_support.setdefault(f"first_{status}", Counter())[support] += 1
                        per_chain[chain_key]["first_change"] = dict(
                            seconds_from_start=start - chain.start, statuses=relationship,
                            old_support=base_category, replacement_support=support_by_truth,
                        )
                joint_seconds["+".join(relationship)] += seconds
                for status in relationship:
                    endpoint_seconds[status] += seconds
                    per_chain[chain_key]["endpoint_seconds"][status] += seconds
                if edge in new:
                    continue
                changed[chain_key] = changed.get(chain_key, 0.0) + seconds
                previous = prior_relations.get(chain_key)
                if previous != relationship:
                    detail = per_chain[chain_key]
                    detail["replacement_changes"] = detail.get("replacement_changes", 0) + 1
                prior_relations[chain_key] = relationship
            for edge, outcome in novel_replacements:
                role = f"replacement_{outcome}"
                lineage(edge, windows, role, seconds, per_boundary.setdefault(role, {}))
    chained = math.fsum(chain.end - chain.start for chains in source_long.values() for chain in chains)
    _equal(math.fsum(joint_seconds.values()), chained)
    _equal(math.fsum(overlap_seconds.values()), chained)
    _equal(math.fsum(endpoint_seconds.values()), 2 * chained)
    _equal(gains["false"] - losses["false"],
           math.fsum(c.end - c.start for c in other_chains) - math.fsum(c.end - c.start for c in reference_chains))
    return dict(
        long_chain_count=len(per_chain), long_seconds=chained,
        endpoint_seconds=dict(endpoint_seconds), joint_seconds=dict(joint_seconds),
        same_edge_overlap_seconds=dict(overlap_seconds),
        net_selected_pair_seconds={kind: gains[kind] - losses[kind] for kind in ("true", "false")},
        added_pair_seconds=dict(gains), removed_pair_seconds=dict(losses),
        changed_long_chains=len(first_change), lineage_windows=categories, lineage_seconds=timing_support,
        unique_latest_tags={role: len(values) for role, values in tags.items()},
        unique_indirect_tags={role: len(values) for role, values in indirect_tags.items()},
        lineage_grid_counts={role: {f"{grid}/{tag_pair}": n for (grid, tag_pair), n in tally.items()}
                             for role, tally in lineage_detail.items()},
        first_change_lineage=onset_support,
        chains=[dict(detail, changed_seconds=changed.get(key, 0.0)) for key, detail in per_chain.items()],
    )


def _scene(archive, manifest, frozen, scene):
    directory = frozen / f"scene-{scene}"
    score = _read_json(frozen / f"{scene}.json")
    stop = score["stop"]
    frames = {name: _read_frames(directory / f"{name}.jsonl.gz") for name in ARMS}
    stamps = tuple(frame.stamp for frame in frames[ARMS[0]])
    reports = tuple(frame.reports for frame in frames[ARMS[0]])
    for values in frames.values():
        _check_frozen(values, stamps, reports, stop)
    lineage_frames = tuple(replay_frames(_native_events(archive, manifest, scene), interval_seconds=BOUNDARY_S))
    if tuple(frame.stamp for frame in lineage_frames) != stamps or any(
            {key: observation.observed_at for key, observation in frame.observations.items()} != report
            for frame, report in zip(lineage_frames, reports)):
        raise ValueError("frozen reports do not reconcile with the original MTAD prefix")
    labels = read_labels(archive, manifest, scene)
    if any(key not in labels for report in reports for key in report):
        raise ValueError("frozen member has no MTAD label")
    for before, after in pairwise(reports):
        if any(key in before and report < before[key] for key, report in after.items()):
            raise ValueError("latest report time moves backwards")
    chains = {name: false_chains(values, labels, stop) for name, values in frames.items()}
    stats = {name: _check_chains(values, score["arms"][name]["false_chains"]) for name, values in chains.items()}
    comparisons = {}
    for a, b in ((ARMS[0], ARMS[1]), (ARMS[0], ARMS[2]), (ARMS[1], ARMS[2])):
        for reference, other in ((a, b), (b, a)):
            key = f"{reference}->{other}"
            audit = _compare(frames[reference], frames[other], chains[reference], chains[other], labels, stop, lineage_frames)
            if scene not in FOCUS:
                audit.pop("chains")
            comparisons[key] = audit
    return dict(
        releases=len(stamps), population=score["arms"][ARMS[0]]["population"],
        arms=stats, comparisons=comparisons,
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", nargs="+", required=True, type=Path)
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--frozen", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    started = perf_counter()
    scenes, components = _scene_roster(args.manifest)
    config = _read_json(args.frozen / "configuration.json")
    complete = _read_json(args.frozen / "complete.json")
    if config["plan"] != DEVELOPMENT_PLAN or config["scenes"] != scenes or complete["scenes"] != scenes:
        raise ValueError("expected the completed original peer experiment with its frozen 28 scenes")
    args.output.mkdir(parents=True)
    for scene in scenes:
        if perf_counter() - started >= 1800:
            raise TimeoutError("frozen audit exceeded its 30 minute budget")
        result = _scene(args.archive, args.manifest, args.frozen, scene)
        with (args.output / f"{scene}.json").open("x", encoding="utf-8") as destination:
            json.dump(result, destination, ensure_ascii=False, allow_nan=False)
            destination.write("\n")
        print(f"Audited frozen scene {scene}", flush=True)
    with (args.output / "complete.json").open("x", encoding="utf-8") as destination:
        json.dump(dict(plan=PLAN, scenes=scenes, components=len(set(components.values())),
                       elapsed_seconds=perf_counter() - started), destination, indent=2)
        destination.write("\n")


if __name__ == "__main__":
    main()
