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
WALL_BUDGET_S = 1800
STATE = "state_20s"
MASKED = "frechet_masked_20s"
CURRENT = "frechet_current_20s"
UNIQUE = "frechet_unique_20s"
HISTORIES = {MASKED: "full", CURRENT: "current", UNIQUE: "unique"}
FOCUS = {"4827", "4979", "3062", "4409"}
FIT_FOCUS = {"3062", "4409"}
COMPARISONS = ((MASKED, CURRENT), (MASKED, UNIQUE), (CURRENT, UNIQUE))


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


def _predict(events, destination, frozen, scene, deadline):
    destination.mkdir()
    stop = _fixed_horizon(events)
    capture = scene in FIT_FOCUS
    arms = [Arm(name, BOUNDARY_S, FrechetArm(unknown_mask=True, history=history, capture_fit=capture))
            for name, history in HISTORIES.items()]
    release_count = 0
    with ExitStack() as stack:
        outputs = {name: stack.enter_context(_gzip(destination / f"{name}.jsonl.gz", "wt"))
                   for name in HISTORIES}
        original = stack.enter_context(_gzip(frozen / f"{MASKED}.jsonl.gz", "rt"))
        fit_stream = stack.enter_context(_gzip(destination / "fits.jsonl.gz", "wt")) if capture else None
        for frame, old_line in zip_longest(replay_frames(events, interval_seconds=BOUNDARY_S), original):
            if perf_counter() >= deadline:
                raise TimeoutError("history ablation exceeded the wall budget")
            if frame is None or old_line is None:
                raise ValueError("replay release count differs from original masked arm")
            release_count += 1
            expected_members = {tuple(key): observation.observed_at
                                for key, observation in frame.observations.items()}
            old = json.loads(old_line)
            del old["service_seconds"]
            for arm in arms:
                publication = _publication(frame, arm)
                members = {tuple(key): report for row in publication["tracks"]
                           for key, report in zip(row["members"], row["observed_at"])}
                if members != expected_members:
                    raise ValueError("published members differ from common replay")
                line = json.dumps(publication, separators=(",", ":"), allow_nan=False)
                if arm.name == MASKED:
                    duplicate = json.loads(line)
                    del duplicate["service_seconds"]
                    if duplicate != old:
                        raise ValueError(f"original masked publication parity failed at {frame.stamp}")
                outputs[arm.name].write(line + "\n")
            if fit_stream is not None:
                fit_stream.write(json.dumps(_snapshot(frame, arms), separators=(",", ":"), allow_nan=False) + "\n")
    diagnostics = {arm.name: dict(arm.runner.diagnostics) for arm in arms}
    if len({row.get("eligible_pairs", 0) for row in diagnostics.values()}) != 1:
        raise ValueError("candidate totals differ between arms")
    _write_json(destination / "predictions.json",
                dict(stop=stop, diagnostics=diagnostics, parity_releases=release_count))


def _audit(scene, prediction, frozen, labels, stop, deadline):
    from .peer_history_audit import audit_focus

    frames = {name: _read_frames((frozen if name == STATE else prediction) / f"{name}.jsonl.gz")
              for name in (STATE, *HISTORIES)}
    result = audit_focus(scene, frames, labels, stop)
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
    args.output.mkdir(parents=True)
    _write_json(args.output / "configuration.json", dict(
        plan=PLAN, scenes=scenes, components=components, histories=HISTORIES, interval=BOUNDARY_S,
        archive=[str(path.resolve()) for path in args.archive], manifest=str(args.manifest.resolve()),
        frozen=str(args.frozen.resolve()), wall_budget_seconds=WALL_BUDGET_S, window=WINDOW_GRIDS,
        cutoff_m=CUTOFF_M, cardinality_m=CARDINALITY_M, seed=SEARCH_SEED, sweeps=SEARCH_SWEEPS,
        started_at=datetime.now(timezone.utc).isoformat(), python=platform.python_version(),
        platform=platform.platform(),
    ))
    for number, scene in enumerate(scenes, 1):
        print(f"Predicting history {number}/{len(scenes)} scene {scene}", flush=True)
        path = f"scene-{scene}"
        events = _native_events(args.archive, args.manifest, scene)
        _predict(events, args.output / path, args.frozen / path, scene, deadline)
    _write_json(args.output / "predictions_complete.json", dict(scenes=scenes))
    for number, scene in enumerate(scenes, 1):
        print(f"Scoring history {number}/{len(scenes)} scene {scene}", flush=True)
        events = _native_events(args.archive, args.manifest, scene)
        labels = read_labels(args.archive, args.manifest, scene)
        reference = read_references(args.archive, args.manifest, scene)
        prediction = args.output / f"scene-{scene}"
        scored_path = args.output / f"{scene}.json"
        _score_scene(events, prediction, labels, reference, scored_path, deadline)
        if scene in FOCUS:
            _audit(scene, prediction, args.frozen / f"scene-{scene}", labels, _fixed_horizon(events), deadline)
    _summarize(args.output, scenes, components, comparisons=COMPARISONS)
    _write_json(args.output / "complete.json", dict(
        scenes=scenes, ended_at=datetime.now(timezone.utc).isoformat(), elapsed_seconds=perf_counter() - started,
    ))


if __name__ == "__main__":
    main()
