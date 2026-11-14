"""Replay the fixed 28-scene MTAD development comparison, then score frozen outputs."""

from __future__ import annotations

import argparse
from collections import Counter, deque
from contextlib import ExitStack
from dataclasses import dataclass
from datetime import datetime, timezone
import gzip
import json
import math
from pathlib import Path
import platform
from time import perf_counter

from .continuous_assignment import solve_global
from .continuous_tracker import NULL_COST, RADIUS_M
from .evaluation_data import read_labels, read_references
from .frechet_trajectory import search_frechet_slots
from .measurements import read_archive_rows
from .peer_identity import CandidateGroup, IdentityReader
from .peer_lindenmaier import LindenmaierArm, PROXY_SETTINGS
from .peer_replay import replay_frames
from .peer_score import score_peer_replay
from .positions import event_batches

ROSTER = Path(__file__).with_name("nemot_roster.json")
MANIFEST = Path(__file__).with_name("data") / "mtad-level1-scene3000.json"
BOUNDARY_S = 20.0
WINDOW_GRIDS = 3
CUTOFF_M = RADIUS_M
CARDINALITY_M = CUTOFF_M / math.sqrt(2)
SEARCH_SEED = 20
SEARCH_SWEEPS = 2
WALL_BUDGET_S = 7200
PLAN_ID = "IDEA-ONLINE-PEER-ADAPTATION-20261114-v1.2"


def _state_position(observation):
    return observation.state.mean[0], observation.state.mean[2]


def _group(frame, members, position):
    stamps = tuple(frame.observations[key].observed_at for key in members)
    return CandidateGroup(members, position, stamps)


def _finish_groups(frame, groups, position):
    used = {key for group in groups for key in group.members}
    groups.extend(
        _group(frame, (key,), position(observation))
        for key, observation in frame.observations.items()
        if key not in used
    )
    return groups


class GeometryArm:
    """Use the same position-only null assignment and ID reader across clocks."""

    def __init__(self, *, predicted):
        self._position = _state_position if predicted else lambda observation: observation.raw_location
        self._identity = IdentityReader()
        self.diagnostics = Counter()

    def publish(self, frame):
        positions = {key: self._position(obs) for key, obs in frame.observations.items()}
        by_source = {}
        for key in positions:
            by_source.setdefault(key[0], []).append(key)
        groups = []
        if len(by_source) == 2:
            left, right = by_source.values()
            costs = [[math.dist(positions[a], positions[b]) ** 2 for b in right] for a in left]
            result = solve_global(costs, [NULL_COST] * len(left), [NULL_COST] * len(right))
            for row, col in result.pairs:
                a, b = left[row], right[col]
                mean = tuple((u + v) / 2 for u, v in zip(positions[a], positions[b]))
                groups.append(_group(frame, (a, b), mean))
            self.diagnostics["ambiguous_vertices"] += len(result.ambiguous_rows) + len(result.ambiguous_columns)
        self.diagnostics["paired_groups"] += len(groups)
        return self._identity.publish(frame.stamp, _finish_groups(frame, groups, self._position))


class FrechetArm:
    """Read the present end of a three-grid trajectory consensus."""

    def __init__(self, *, unknown_mask):
        self._identity = IdentityReader()
        self._frames = deque(maxlen=WINDOW_GRIDS)
        self._grid = 0
        self._unknown_mask = unknown_mask
        self.diagnostics = Counter()

    def publish(self, frame):
        self._grid += 1
        self._frames.append((self._grid, frame))
        trajectories = {
            key: {index: _state_position(old.observations[key]) for index, old in self._frames
                  if key in old.observations}
            for key in frame.observations
        }
        by_source = {}
        for key, trajectory in trajectories.items():
            by_source.setdefault(key[0], {}).setdefault(tuple(trajectory.items()), []).append(key)
        groups = []
        if len(by_source) == 2:
            # Geometric histories give a canonical order. Identical histories in
            # one source carry no evidence for a fragment-specific cross-link.
            sources = sorted(by_source.values(), key=lambda items: sorted(items))
            left, right = [
                [(history, key) for history, keys in sorted(source.items()) for key in keys]
                for source in sources
            ]
            fit = search_frechet_slots(
                [dict(history) for history, _ in left],
                [dict(history) for history, _ in right],
                cutoff=CUTOFF_M, cardinality_penalty=CARDINALITY_M,
                seed=SEARCH_SEED, max_sweeps=SEARCH_SWEEPS, unknown_mask=self._unknown_mask,
            )
            for (a, b), center in zip(fit.slots, fit.centers):
                if a is None or b is None:
                    continue
                left_history, first_key = left[a]
                right_history, second_key = right[b]
                if len(sources[0][left_history]) != 1 or len(sources[1][right_history]) != 1:
                    self.diagnostics["indistinguishable_history_pairs"] += 1
                    continue
                if self._grid not in center:
                    self.diagnostics["no_current_center_pairs"] += 1
                    continue
                active = first_key, second_key
                overlap = trajectories[active[0]].keys() & trajectories[active[1]].keys()
                self.diagnostics["paired_common_grids"] += len(overlap)
                groups.append(_group(frame, active, center[self._grid]))
        self.diagnostics["paired_groups"] += len(groups)
        return self._identity.publish(frame.stamp, _finish_groups(frame, groups, _state_position))


@dataclass(frozen=True)
class Arm:
    name: str
    interval: float | None
    runner: object


def _arms():
    return [
        Arm("raw_event", None, GeometryArm(predicted=False)),
        Arm("state_event", None, GeometryArm(predicted=True)),
        Arm("lindenmaier_diffuse_event", None, LindenmaierArm(feedback=False)),
        Arm("lindenmaier_feedback_event", None, LindenmaierArm(feedback=True)),
        Arm("state_20s", BOUNDARY_S, GeometryArm(predicted=True)),
        Arm("lindenmaier_feedback_20s", BOUNDARY_S, LindenmaierArm(feedback=True)),
        Arm("frechet_penalty_20s", BOUNDARY_S, FrechetArm(unknown_mask=False)),
        Arm("frechet_masked_20s", BOUNDARY_S, FrechetArm(unknown_mask=True)),
    ]


def _scene_roster(manifest_path):
    roster = json.loads(ROSTER.read_text(encoding="utf-8"))
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    scenes = roster["splits"]["held"]
    components = {scene: manifest["components"][scene] for scene in scenes}
    if (len(scenes) != 28 or len(components) != 28 or len(set(components.values())) != 28
            or not set(scenes) <= set(manifest["splits"]["T_core"])
            or any(components[scene] != roster["components"][scene] for scene in scenes)):
        raise ValueError("expected the original 28 scenes in distinct T_core components")
    return scenes, components


def _native_events(archive, manifest, scene):
    events = tuple(event_batches(read_archive_rows(archive, manifest, scene, required_split="T_core")))
    if not events or events[0][0] < 0:
        raise ValueError(f"scene {scene} requires a nonempty, nonnegative report clock")
    if len({key[0] for _, reports in events for key in reports}) > 2:
        raise ValueError(f"scene {scene} exceeds the two-source consensus protocol")
    return events


def _publication(frame, arm):
    start = perf_counter()
    identified = arm.runner.publish(frame)
    service = perf_counter() - start
    tracks = [
        dict(track_id=group.track_id, members=group.candidate.members,
             position_m=group.candidate.position, observed_at=group.candidate.observed_at,
             measurement_time=max(group.candidate.observed_at))
        for group in identified
    ]
    return dict(arm=arm.name, query_time=frame.stamp, tracks=tracks, service_seconds=service)


def _fixed_horizon(events):
    start, last = events[0][0], events[-1][0]
    count = 1 + math.floor((last - start) / BOUNDARY_S)
    boundary = start + BOUNDARY_S * count
    while boundary <= last:
        count += 1
        boundary = start + BOUNDARY_S * count
    while count > 1 and start + BOUNDARY_S * (count - 1) > last:
        count -= 1
        boundary = start + BOUNDARY_S * count
    return boundary


def _predict_scene(events, destination, deadline):
    stop = _fixed_horizon(events)
    destination.mkdir()
    arms = _arms()
    with ExitStack() as stack:
        outputs = {
            arm.name: stack.enter_context(gzip.open(
                destination / f"{arm.name}.jsonl.gz", "xt", encoding="utf-8", compresslevel=1))
            for arm in arms
        }
        for interval in (None, BOUNDARY_S):
            current = [arm for arm in arms if arm.interval == interval]
            for frame in replay_frames(events, interval_seconds=interval):
                if perf_counter() >= deadline:
                    raise TimeoutError("prediction exceeded the frozen wall budget")
                if frame.stamp > stop:
                    break
                for arm in current:
                    line = json.dumps(_publication(frame, arm), separators=(",", ":"), allow_nan=False)
                    outputs[arm.name].write(line + "\n")
    _write_json(destination / "predictions.json", dict(
        stop=stop, diagnostics={arm.name: dict(arm.runner.diagnostics) for arm in arms},
    ))


def _score_scene(events, prediction, labels, reference, destination, deadline):
    protocol = json.loads((prediction / "predictions.json").read_text(encoding="utf-8"))
    stop = protocol["stop"]
    scores = {}
    for name in protocol["diagnostics"]:
        if perf_counter() >= deadline:
            raise TimeoutError("scoring exceeded the frozen wall budget")
        with gzip.open(prediction / f"{name}.jsonl.gz", "rt", encoding="utf-8") as source:
            scores[name] = score_peer_replay(events, map(json.loads, source), labels, stop=stop,
                                             reference=reference, include_birth_details=True)
    _write_json(destination, dict(arms=scores, **protocol))



COMPARISONS = (
    ("raw_event", "state_event"),
    ("state_event", "lindenmaier_feedback_event"),
    ("lindenmaier_diffuse_event", "lindenmaier_feedback_event"),
    ("state_20s", "lindenmaier_feedback_20s"),
    ("state_20s", "frechet_penalty_20s"),
    ("state_20s", "frechet_masked_20s"),
    ("frechet_penalty_20s", "frechet_masked_20s"),
    ("lindenmaier_feedback_20s", "frechet_penalty_20s"),
    ("lindenmaier_feedback_20s", "frechet_masked_20s"),
)


def _scene_summary(score):
    native = score["native_births"]
    counts = score["integer_grid"]["counts"]
    pairs = score["integer_grid"]["pairs"]["cross_source"]
    chains = score["false_chains"]
    result = {
        **native["first_decisions"],
        "births": native["births"],
        "wrong_before_true_peer": native["first_wrong_without_true_peer_at_release"],
        "wrong_no_true_peer_at_birth": native["first_wrong_without_true_peer_at_birth"],
        "confirmed": native["ever_confirmed"],
        "confirmed_within_seconds": native["confirmed_within_seconds"],
        "wait_seconds": native["confirmation_wait_seconds"],
        "unique_target_seconds": counts["uniquely_tracked_target_seconds"],
        "supported_target_seconds": counts["report_supported_target_seconds"],
        "id_switches": counts["id_switches_consecutive"] + counts["id_switches_after_gap"],
        "same_id_reacquisitions": counts["reacquired_same_id"],
        "true_pair_seconds": pairs["truth_pairs"],
        "correct_pair_seconds": pairs["correct_pairs"],
        "false_pair_seconds": pairs["false_pairs"],
        "missed_pair_seconds": pairs["missed_pairs"],
        "long_chains": chains["over_60_seconds"]["chains"],
        "long_chain_seconds": chains["over_60_seconds"]["pair_seconds"],
        "longest_chain_seconds": chains["duration_seconds"]["max"] or 0.0,
        "censored_chains": chains["ends"].get("right_censored", 0),
        "service_seconds": score["service_seconds"],
        "position": score["position"],
    }
    return result


def _paired_births(control, candidate):
    before = {tuple(row["fragment"]): row for row in control["birth_details"]}
    after = {tuple(row["fragment"]): row for row in candidate["birth_details"]}
    if before.keys() != after.keys():
        raise ValueError("paired arms must evaluate the same births")
    kept = lost = gained = 0
    for key, old in before.items():
        was_correct = old["first_decision"] == "correct"
        is_correct = after[key]["first_decision"] == "correct"
        kept += was_correct and is_correct
        lost += was_correct and not is_correct
        gained += not was_correct and is_correct
    return dict(kept=kept, lost=lost, gained=gained)


def _summarize(output, scenes, components):
    reports = {}
    for scene in scenes:
        raw = json.loads((output / f"{scene}.json").read_text(encoding="utf-8"))
        scores = raw["arms"]
        populations = [score["population"] for score in scores.values()]
        if any(population != populations[0] for population in populations):
            raise ValueError("scene population differs between arms")
        reports[scene] = dict(
            component=components[scene], population=populations[0], diagnostics=raw["diagnostics"],
            arms={name: _scene_summary(score) for name, score in scores.items()},
            paired_first=[
                dict(control=control, candidate=candidate, **_paired_births(scores[control], scores[candidate]))
                for control, candidate in COMPARISONS
            ],
        )
    _write_json(output / "scene_summary.json", reports)

def _write_json(path, value):
    with path.open("x", encoding="utf-8") as output:
        json.dump(value, output, ensure_ascii=False, indent=2, allow_nan=False)
        output.write("\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", required=True, nargs="+", type=Path, help="Level1 ZIP, or its ordered byte parts")
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--output", required=True, type=Path, help="new private result directory")
    args = parser.parse_args(argv)
    started = perf_counter()
    deadline = started + WALL_BUDGET_S
    scenes, components = _scene_roster(args.manifest)
    args.output.mkdir(parents=True, exist_ok=False)
    _write_json(args.output / "configuration.json", dict(
        plan=PLAN_ID, scenes=scenes, components=components, wall_budget_seconds=WALL_BUDGET_S,
        archive=[str(part.resolve()) for part in args.archive], manifest=str(args.manifest.resolve()),
        arms={arm.name: arm.interval for arm in _arms()}, lindenmaier=PROXY_SETTINGS,
        frechet=dict(window_grids=WINDOW_GRIDS, cutoff_m=CUTOFF_M, cardinality_m=CARDINALITY_M,
                     seed=SEARCH_SEED, max_sweeps=SEARCH_SWEEPS),
        started_at=datetime.now(timezone.utc).isoformat(), python=platform.python_version(),
        platform=platform.platform(),
    ))
    for number, scene in enumerate(scenes, 1):
        print(f"Predicting {number}/{len(scenes)} scene {scene}", flush=True)
        events = _native_events(args.archive, args.manifest, scene)
        _predict_scene(events, args.output / f"scene-{scene}", deadline)
    _write_json(args.output / "predictions_complete.json", dict(scenes=scenes))
    for number, scene in enumerate(scenes, 1):
        print(f"Scoring {number}/{len(scenes)} scene {scene}", flush=True)
        events = _native_events(args.archive, args.manifest, scene)
        labels = read_labels(args.archive, args.manifest, scene)
        reference = read_references(args.archive, args.manifest, scene)
        _score_scene(events, args.output / f"scene-{scene}", labels, reference, args.output / f"{scene}.json", deadline)
    if perf_counter() >= deadline:
        raise TimeoutError("scoring exceeded the frozen wall budget")
    _summarize(args.output, scenes, components)
    _write_json(args.output / "complete.json", dict(
        scenes=scenes, ended_at=datetime.now(timezone.utc).isoformat(), elapsed_seconds=perf_counter() - started,
    ))


if __name__ == "__main__":
    main()
