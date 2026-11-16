"""Reduce the completed five-arm development run to a public aggregate."""

from __future__ import annotations

import argparse
from collections import Counter
import json
import math
from pathlib import Path
from statistics import median

from .peer_experiment import _paired_births, _scene_summary, _write_json
from .peer_score import DEADLINES, FIRST_DECISIONS, _distribution

ARMS = {
    "A": "frechet_masked_20s",
    "B": "frechet_current_20s",
    "C": "frechet_unique_20s",
    "D": "frechet_decay_20s",
    "E": "frechet_conflict_decay_20s",
}
FOCUS = {
    "false_extension_case_1": "4409",
    "false_extension_case_2": "3062",
    "true_replacement_case_1": "4827",
    "true_replacement_case_2": "4979",
}
OUTCOMES = ("same_false", "other_false", "same_true", "different_true", "singleton", "expired", "partner_expired")
DIAGNOSTICS = ("eligible_pairs", "active_fragments", "weighted_tracks", "conflict_frames", "conflict_components")
TOTAL_FIELDS = (
    "births", "confirmed", "unique_target_seconds",
    "supported_target_seconds", "id_switches", "same_id_reacquisitions", "true_pair_seconds", "correct_pair_seconds",
    "false_pair_seconds", "missed_pair_seconds", "long_chains", "censored_chains",
)
TOLERANCE = 1e-7


def _read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _aggregate(rows, arm):
    scores = [row["arms"][arm] for row in rows]
    metrics = [_scene_summary(score) for score in scores]
    births = [birth for score in scores for birth in score["birth_details"]]
    count = len(births)
    result = {key: sum(score[key] for score in metrics) for key in TOTAL_FIELDS}
    decisions = {key: sum(score[key] for score in metrics) for key in FIRST_DECISIONS}
    confirmed_waits = _distribution(
        birth["confirmed_after_seconds"] for birth in births if birth["confirmed_after_seconds"] is not None
    )
    if count != result["births"] or result["confirmed"] != confirmed_waits["n"]:
        raise ValueError("birth details do not reconcile with the score")
    result.update(
        first_decisions=decisions,
        correct_first_report_coverage=decisions["correct"] / count,
        incorrect_first_reports_without_true_peer_ever_seen_at_birth=sum(
            score["wrong_no_true_peer_at_birth"] for score in metrics
        ),
        incorrect_first_reports_without_true_peer_ever_seen_at_release=sum(
            score["wrong_before_true_peer"] for score in metrics
        ),
        first_report_opportunities_without_true_peer_ever_seen_at_release=sum(
            birth["opportunity_at_release"] == "never_observed" for birth in births
        ),
        sparse_births=sum(birth["sparse"] for birth in births),
        final_confirmation_coverage=result["confirmed"] / count,
        confirmation_wait_seconds_among_confirmed=confirmed_waits,
        longest_false_chain_seconds=max(score["longest_chain_seconds"] for score in metrics),
        long_chain_pair_seconds=math.fsum(score["long_chain_seconds"] for score in metrics),
        false_chain_pair_seconds=math.fsum(score["false_chains"]["pair_seconds"] for score in scores),
        unique_pure_id_coverage=result["unique_target_seconds"] / result["supported_target_seconds"],
    )
    deadlines = {}
    for deadline in map(str, DEADLINES):
        counts = Counter()
        for score in metrics:
            counts.update(score["confirmed_within_seconds"][deadline])
        deadlines[deadline] = dict(confirmed=counts["confirmed"], censored=counts["censored"],
                                   unconfirmed=counts["unconfirmed"], coverage_of_all_births=counts["confirmed"] / count)
    result["confirmation_by_deadline_seconds"] = deadlines
    timing = [score["service_seconds"] for score in metrics if score["service_seconds"] is not None]
    result["timing"] = {
        field: dict(scenes=len(timing), median_scene_p95_seconds=median(row[field]["p95"] for row in timing),
                    max_seconds=max(row[field]["max"] for row in timing))
        for field in ("service", "queue_wait", "release_to_ready")
    } if timing else None
    result["diagnostics"] = {
        key: sum(row["diagnostics"][arm].get(key, 0) for row in rows) for key in DIAGNOSTICS
    }
    return result


def _paired(rows, control):
    first = Counter()
    confirmation = Counter(dict.fromkeys(("both", "candidate_only", "control_only", "neither",
                                         "candidate_earlier", "equal", "candidate_later"), 0))
    differences = []
    for row in rows:
        before = row["arms"][control]
        after = row["arms"]["E"]
        first.update(_paired_births(before, after))
        candidate_waits = {tuple(birth["fragment"]): birth["confirmed_after_seconds"] for birth in after["birth_details"]}
        for birth in before["birth_details"]:
            original = birth["confirmed_after_seconds"]
            candidate = candidate_waits[tuple(birth["fragment"])]
            if original is not None and candidate is not None:
                confirmation["both"] += 1
                delta = candidate - original
                differences.append(delta)
                order = "candidate_earlier" if delta < 0 else "candidate_later" if delta > 0 else "equal"
                confirmation[order] += 1
            elif original is not None:
                confirmation["control_only"] += 1
            elif candidate is not None:
                confirmation["candidate_only"] += 1
            else:
                confirmation["neither"] += 1
    return dict(
        correct_first_report_events=dict(first),
        confirmation_events=dict(confirmation),
        candidate_minus_control_wait_seconds_among_both_confirmed=_distribution(differences),
    )


def _first_report_retention(rows):
    totals = {}
    for candidate in ("B", "C", "D", "E"):
        counts = Counter()
        for row in rows:
            counts.update(_paired_births(row["arms"]["A"], row["arms"][candidate]))
        totals[candidate] = dict(counts)
    return totals


def _long_chain_contrast(rows, control, components, excluded):
    per_component = {component: [] for component in components.values()}
    directions = Counter(dict(decreased=0, unchanged=0, increased=0))
    without_focal = []
    for scene, row in rows.items():
        candidate = row["arms"]["E"]["false_chains"]["over_60_seconds"]["pair_seconds"]
        baseline = row["arms"][control]["false_chains"]["over_60_seconds"]["pair_seconds"]
        delta = candidate - baseline
        per_component[components[scene]].append(delta)
        direction = "unchanged" if abs(delta) <= TOLERANCE else "decreased" if delta < 0 else "increased"
        directions[direction] += 1
        if scene != excluded:
            without_focal.append(delta)
    observed = {name: deltas for name, deltas in per_component.items() if deltas}
    sums = {name: math.fsum(deltas) for name, deltas in observed.items()}
    remaining = {
        omitted: math.fsum(delta for name, delta in sums.items() if name != omitted) for omitted in sums
    }
    return dict(
        candidate_minus_control_long_chain_pair_seconds=math.fsum(sums.values()),
        scene_directions=dict(directions),
        by_anonymous_component={
            name: dict(scenes=len(observed[name]), candidate_minus_control_pair_seconds=delta,
                       difference_without_component_pair_seconds=remaining[name]) for name, delta in sums.items()
        },
        leave_one_component_out_range_pair_seconds=dict(min=min(remaining.values()), max=max(remaining.values())),
        without_true_replacement_case_1_pair_seconds=math.fsum(without_focal),
    )


def _focus(raw, case):
    forward = case.startswith("true_replacement")
    if raw["focus"] != ("state_to_mask" if forward else "mask_to_state"):
        raise ValueError("focal audit direction differs from the design")
    weight = raw["focal_endpoint_seconds"]
    comparison = raw["comparison_endpoint_seconds"]
    outcomes = {"A": {"same_true" if forward else "same_false": weight}}
    for arm in ("B", "C", "D", "E"):
        outcomes[arm] = comparison[ARMS[arm]]
    results = {}
    for arm, values in outcomes.items():
        endpoint_seconds = {key: values.get(key, 0.0) for key in OUTCOMES}
        if not math.isclose(math.fsum(endpoint_seconds.values()), weight, rel_tol=0, abs_tol=TOLERANCE):
            raise ValueError("focal statuses do not cover the frozen endpoint seconds")
        results[arm] = dict(endpoint_seconds=endpoint_seconds,
                            true_replacement_endpoint_seconds=values.get("same_true", 0.0)
                            + values.get("different_true", 0.0))
        if forward:
            results[arm]["same_true_partner_retention"] = endpoint_seconds["same_true"] / weight
    return dict(focal_pair_seconds=raw["focal_pair_seconds"], focal_endpoint_seconds=weight, arms=results)


def _decisions(sparse, contrasts, focus):
    candidate, control = sparse["E"], sparse["C"]
    first, second = (focus[f"false_extension_case_{number}"]["arms"] for number in (1, 2))
    checks = {
        **{f"sparse_long_chain_lower_than_{arm}":
           contrast["candidate_minus_control_long_chain_pair_seconds"] < -TOLERANCE
           and contrast["without_true_replacement_case_1_pair_seconds"] < -TOLERANCE
           for arm, contrast in contrasts.items()},
        "false_extension_case_1_more_true_replacement":
            first["E"]["true_replacement_endpoint_seconds"] > first["C"]["true_replacement_endpoint_seconds"],
        "false_extension_case_2_no_more_other_false":
            second["E"]["endpoint_seconds"]["other_false"] <= second["C"]["endpoint_seconds"]["other_false"],
        **{f"{case}_at_least_95_percent_preserved": row["arms"]["E"]["same_true_partner_retention"] >= 0.95
           for case, row in focus.items() if case.startswith("true_replacement")},
        "sparse_correct_first_report_coverage_maintained":
            candidate["correct_first_report_coverage"] >= control["correct_first_report_coverage"],
        "sparse_final_confirmation_coverage_maintained":
            candidate["final_confirmation_coverage"] >= control["final_confirmation_coverage"],
        "sparse_unique_pure_id_coverage_maintained": candidate["unique_pure_id_coverage"] >= control["unique_pure_id_coverage"],
        **{f"sparse_{key}_not_increased": candidate[key] <= control[key]
           for key in ("false_pair_seconds", "missed_pair_seconds", "id_switches")},
    }
    for deadline in map(str, DEADLINES):
        checks[f"sparse_confirmation_coverage_maintained_at_{deadline}_seconds"] = (
            candidate["confirmation_by_deadline_seconds"][deadline]["coverage_of_all_births"]
            >= control["confirmation_by_deadline_seconds"][deadline]["coverage_of_all_births"]
        )
    return dict(all_preregistered_development_criteria_met=all(checks.values()), individual=checks)


def summarize(run):
    configuration = _read(run / "configuration.json")
    scenes = configuration["scenes"]
    private_components = configuration["components"]
    if (configuration["plan"] != "IDEA-ONLINE-CONFLICT-HISTORY-20261116-v1"
            or _read(run / "complete.json")["scenes"] != scenes or set(private_components) != set(scenes)
            or len(scenes) != 28 or len(set(scenes)) != 28 or len(set(private_components.values())) != 28):
        raise ValueError("expected the completed 28-component development run")
    components = {scene: f"component_{index:02d}" for index, scene in enumerate(scenes, 1)}
    all_rows, sparse_rows = {}, {}
    for scene in scenes:
        raw = _read(run / f"{scene}.json")
        if set(raw["arms"]) != set(ARMS.values()):
            raise ValueError("expected exactly the five frozen score arms")
        arms = {arm: raw["arms"][name] for arm, name in ARMS.items()}
        population = arms["C"]["population"]
        if any(score["population"] != population for score in arms.values()):
            raise ValueError("scene population differs between arms")
        row = dict(arms=arms, releases=raw["parity_releases"],
                   diagnostics={arm: raw["diagnostics"][name] for arm, name in ARMS.items()})
        all_rows[scene] = row
        if population["is_sparse_scene"]:
            sparse_rows[scene] = row
    if len(sparse_rows) != 24:
        raise ValueError("expected the frozen 24-scene sparse subset")

    scopes = {}
    for name, rows in (("all_28_scenes", all_rows), ("sparse_24_scenes", sparse_rows)):
        arms = {arm: _aggregate(rows.values(), arm) for arm in ARMS}
        scopes[name] = dict(
            releases_per_arm=sum(row["releases"] for row in rows.values()),
            arms=arms,
            correct_first_report_events_vs_A=_first_report_retention(rows.values()),
            contrasts_E_vs={arm: dict(
                long_chain=_long_chain_contrast(rows, arm, components, excluded=FOCUS["true_replacement_case_1"]),
                **_paired(rows.values(), arm),
            ) for arm in ("C", "D")},
        )
    focus = {case: _focus(_read(run / f"scene-{scene}" / "focus.json"), case) for case, scene in FOCUS.items()}
    sparse = scopes["sparse_24_scenes"]
    contrasts = {arm: row["long_chain"] for arm, row in sparse["contrasts_E_vs"].items()}
    return dict(arm_definitions=ARMS, scopes=scopes, focal_audits=focus,
                decision_checks=_decisions(sparse["arms"], contrasts, focus))


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run", required=True, type=Path, help="completed private result directory")
    parser.add_argument("--output", required=True, type=Path, help="new public aggregate JSON file")
    args = parser.parse_args(argv)
    _write_json(args.output, summarize(args.run))


if __name__ == "__main__":
    main()
