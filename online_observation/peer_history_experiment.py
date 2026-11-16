"""Run the fixed 28-scene MTAD Fréchet history ablation and score frozen releases."""

from __future__ import annotations

import argparse
from contextlib import ExitStack
from datetime import datetime, timezone
import gzip
from itertools import zip_longest
import json
from pathlib import Path
import platform
from time import perf_counter

from .evaluation_data import read_labels, read_references
from .peer_chain_audit import _read_frames
from .peer_experiment import (
    Arm, BOUNDARY_S, CARDINALITY_M, CUTOFF_M, FrechetArm, MANIFEST,
    SEARCH_SEED, SEARCH_SWEEPS, WINDOW_GRIDS, _fixed_horizon, _native_events,
    _publication, _scene_roster, _score_scene, _summarize, _write_json,
)
from .peer_replay import replay_frames

PLAN = "IDEA-ONLINE-PEER-HISTORY-20261114-v1.5"
CONFLICT_PLAN = "IDEA-ONLINE-CONFLICT-HISTORY-20261116-v1"
WALL_BUDGET_S = 1800
STATE = "state_20s"
MASKED = "frechet_masked_20s"
CURRENT = "frechet_current_20s"
UNIQUE = "frechet_unique_20s"
DECAY = "frechet_decay_20s"
CONFLICT_DECAY = "frechet_conflict_decay_20s"
HISTORIES = {MASKED: "full", CURRENT: "current", UNIQUE: "unique"}
WEIGHTED_HISTORIES = {DECAY: "decay", CONFLICT_DECAY: "conflict_decay"}
FOCUS = {"4827", "4979", "3062", "4409"}
FIT_FOCUS = {"3062", "4409"}
COMPARISONS = ((MASKED, CURRENT), (MASKED, UNIQUE), (CURRENT, UNIQUE))
CONFLICT_COMPARISONS = (*COMPARISONS, (UNIQUE, CONFLICT_DECAY), (DECAY, CONFLICT_DECAY))


def _gzip(path, mode):
    return gzip.open(path, mode, encoding="utf-8", compresslevel=1)


def _snapshot(frame, arms):
    snapshots = {arm.name: arm.runner.snapshot for arm in arms}
    full = snapshots[MASKED]
    if full is None:
        return dict(stamp=frame.stamp, keys=[[], []], tags=[[], []], slots={}, trajectories={})
    if any(row["keys"] != full["keys"] or row["tags"] != full["tags"] for row in snapshots.values()):
        raise ValueError("arm candidate order or native tags differ")
    return dict(stamp=frame.stamp, keys=full["keys"], tags=full["tags"],
                slots={name: row["slots"] for name, row in snapshots.items()},
                trajectories={name: row["trajectories"] for name, row in snapshots.items()})


def _assert_publication_parity(current_line, frozen_line, arm, stamp):
    current = json.loads(current_line)
    frozen = json.loads(frozen_line)
    del current["service_seconds"], frozen["service_seconds"]
    if current != frozen:
        raise ValueError(f"{arm} publication parity failed at {stamp}")


def _predict(events, destination, frozen, scene, deadline, *, frozen_history=None):
    destination.mkdir()
    stop = _fixed_horizon(events)
    capture = scene in FIT_FOCUS
    histories = HISTORIES if frozen_history is None else {**HISTORIES, **WEIGHTED_HISTORIES}
    arms = [Arm(name, BOUNDARY_S, FrechetArm(unknown_mask=True, history=history,
                                            capture_fit=capture and name in HISTORIES))
            for name, history in histories.items()]
    fit_arms = [arm for arm in arms if arm.name in HISTORIES]
    release_count = 0
    with ExitStack() as stack:
        outputs = {name: stack.enter_context(_gzip(destination / f"{name}.jsonl.gz", "wt"))
                   for name in histories}
        original = stack.enter_context(_gzip(frozen / f"{MASKED}.jsonl.gz", "rt"))
        controls = {name: stack.enter_context(_gzip(frozen_history / f"{name}.jsonl.gz", "rt"))
                    for name in HISTORIES} if frozen_history is not None else {}
        fit_stream = stack.enter_context(_gzip(destination / "fits.jsonl.gz", "wt")) if capture else None
        frames = replay_frames(events, interval_seconds=BOUNDARY_S)
        for frame, old_line, *control_lines in zip_longest(frames, original, *controls.values()):
            if perf_counter() >= deadline:
                raise TimeoutError("history ablation exceeded the wall budget")
            if frame is None or old_line is None or any(line is None for line in control_lines):
                raise ValueError("replay release count differs from a frozen history arm")
            release_count += 1
            expected_members = {tuple(key): observation.observed_at
                                for key, observation in frame.observations.items()}
            controls_at_release = dict(zip(controls, control_lines, strict=True))
            for arm in arms:
                publication = _publication(frame, arm)
                tracks = publication["tracks"]
                members = {tuple(key): report for row in tracks
                           for key, report in zip(row["members"], row["observed_at"], strict=True)}
                if (publication["query_time"] != frame.stamp or members != expected_members
                        or len(members) != sum(len(row["members"]) for row in tracks)
                        or len({row["track_id"] for row in tracks}) != len(tracks)):
                    raise ValueError("publication differs from common replay or repeats a member or ID")
                if (frozen_history is not None
                        and arm.runner.candidate_order != arms[0].runner.candidate_order):
                    raise ValueError("arm candidate order differs from the original masked arm")
                line = json.dumps(publication, separators=(",", ":"), allow_nan=False)
                if arm.name == MASKED:
                    _assert_publication_parity(line, old_line, "v1.2 masked", frame.stamp)
                if arm.name in controls_at_release:
                    _assert_publication_parity(line, controls_at_release[arm.name], f"v1.5 {arm.name}", frame.stamp)
                outputs[arm.name].write(line + "\n")
            if fit_stream is not None:
                snapshot = _snapshot(frame, fit_arms)
                fit_stream.write(json.dumps(snapshot, separators=(",", ":"), allow_nan=False) + "\n")
    diagnostics = {arm.name: dict(arm.runner.diagnostics) for arm in arms}
    if len({row.get("eligible_pairs", 0) for row in diagnostics.values()}) != 1:
        raise ValueError("candidate totals differ between arms")
    _write_json(destination / "predictions.json",
                dict(stop=stop, diagnostics=diagnostics, parity_releases=release_count))


def _audit(scene, prediction, frozen, labels, stop, deadline, *, additional_arms=()):
    from .peer_history_audit import audit_focus

    frames = {name: _read_frames((frozen if name == STATE else prediction) / f"{name}.jsonl.gz")
              for name in (STATE, *HISTORIES, *additional_arms)}
    result = audit_focus(scene, frames, labels, stop, additional_arms=additional_arms)
    if scene in FIT_FOCUS:
        from .peer_history_attribution import attribute_disputes

        with _gzip(prediction / "fits.jsonl.gz", "rt") as source:
            snapshots = list(map(json.loads, source))
        if [frame.stamp for frame in frames[MASKED]] != [row["stamp"] for row in snapshots]:
            raise ValueError("focal fit snapshots differ from the frozen release clock")
        result["cost_attribution"] = attribute_disputes(result["disputes"], snapshots, labels)
    if perf_counter() >= deadline:
        raise TimeoutError("history audit exceeded the wall budget")
    _write_json(prediction / "focus.json", result)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", required=True, nargs="+", type=Path)
    parser.add_argument("--manifest", type=Path, default=MANIFEST)
    parser.add_argument("--frozen", required=True, type=Path, help="original private v1.2 results")
    parser.add_argument("--frozen-history", type=Path, help="v1.5 results for the five-arm conflict-history run")
    parser.add_argument("--output", required=True, type=Path, help="new private result directory")
    args = parser.parse_args(argv)
    started = perf_counter()
    deadline = started + WALL_BUDGET_S
    scenes, components = _scene_roster(args.manifest)
    original = json.loads((args.frozen / "configuration.json").read_text(encoding="utf-8"))
    if (original["plan"] != "IDEA-ONLINE-PEER-ADAPTATION-20261114-v1.2"
            or original["scenes"] != scenes or original["components"] != components
            or not (args.frozen / "complete.json").is_file()):
        raise ValueError("expected complete original v1.2 publications for the 28 development scenes")
    if args.frozen_history is not None:
        history = json.loads((args.frozen_history / "configuration.json").read_text(encoding="utf-8"))
        expected = dict(plan=PLAN, scenes=scenes, components=components, histories=HISTORIES,
                        interval=BOUNDARY_S, window=WINDOW_GRIDS, cutoff_m=CUTOFF_M,
                        cardinality_m=CARDINALITY_M, seed=SEARCH_SEED, sweeps=SEARCH_SWEEPS)
        if (any(history.get(key) != value for key, value in expected.items())
                or not (args.frozen_history / "complete.json").is_file()):
            raise ValueError("expected complete v1.5 histories for the frozen 28 development scenes")
    args.output.mkdir(parents=True)
    config = dict(
        plan=PLAN, scenes=scenes, components=components, histories=HISTORIES, interval=BOUNDARY_S,
        archive=[str(path.resolve()) for path in args.archive], manifest=str(args.manifest.resolve()),
        frozen=str(args.frozen.resolve()), wall_budget_seconds=WALL_BUDGET_S, window=WINDOW_GRIDS,
        cutoff_m=CUTOFF_M, cardinality_m=CARDINALITY_M, seed=SEARCH_SEED, sweeps=SEARCH_SWEEPS,
        started_at=datetime.now(timezone.utc).isoformat(), python=platform.python_version(),
        platform=platform.platform(),
    )
    if args.frozen_history is not None:
        config.update(plan=CONFLICT_PLAN, histories={**HISTORIES, **WEIGHTED_HISTORIES},
                      frozen_history=str(args.frozen_history.resolve()))
    _write_json(args.output / "configuration.json", config)
    for number, scene in enumerate(scenes, 1):
        print(f"Predicting history {number}/{len(scenes)} scene {scene}", flush=True)
        path = f"scene-{scene}"
        events = _native_events(args.archive, args.manifest, scene)
        if args.frozen_history is None:
            _predict(events, args.output / path, args.frozen / path, scene, deadline)
        else:
            _predict(events, args.output / path, args.frozen / path, scene, deadline,
                     frozen_history=args.frozen_history / path)
    _write_json(args.output / "predictions_complete.json", dict(scenes=scenes))
    audit_options = {"additional_arms": tuple(WEIGHTED_HISTORIES)} if args.frozen_history is not None else {}
    for number, scene in enumerate(scenes, 1):
        print(f"Scoring history {number}/{len(scenes)} scene {scene}", flush=True)
        events = _native_events(args.archive, args.manifest, scene)
        labels = read_labels(args.archive, args.manifest, scene)
        reference = read_references(args.archive, args.manifest, scene)
        prediction = args.output / f"scene-{scene}"
        scored_path = args.output / f"{scene}.json"
        _score_scene(events, prediction, labels, reference, scored_path, deadline)
        if scene in FOCUS:
            _audit(scene, prediction, args.frozen / f"scene-{scene}", labels, _fixed_horizon(events), deadline,
                   **audit_options)
    comparisons = COMPARISONS if args.frozen_history is None else CONFLICT_COMPARISONS
    _summarize(args.output, scenes, components, comparisons=comparisons)
    _write_json(args.output / "complete.json", dict(
        scenes=scenes, ended_at=datetime.now(timezone.utc).isoformat(), elapsed_seconds=perf_counter() - started,
    ))


if __name__ == "__main__":
    main()
