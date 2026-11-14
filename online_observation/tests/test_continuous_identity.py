"""Check continuous identity publication and scoring."""
import math
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from online_observation import continuous_factorial as factorial
from online_observation.continuous_metrics import evaluate_publications
from online_observation.continuous_tracker import ContinuousTracker, LocalTrack
from online_observation.stream import EARTH_RADIUS_M


def point(metres):
    return 0.0, math.degrees(metres / EARTH_RADIUS_M)


def groups(snapshot):
    return {frozenset(track["members"]) for track in snapshot["tracks"]}


class ContinuousTrackerTests(unittest.TestCase):
    def test_global_competition_does_not_force_forbidden_or_unmatched_pairs(self):
        a, b, c, d = ("A", "a"), ("A", "b"), ("B", "c"), ("B", "d")
        event = {a: point(0), b: point(3000), c: point(1000), d: point(-2000)}
        local = ContinuousTracker("hold_local")
        global_ = ContinuousTracker("hold_global")
        local.ingest(0, event)
        global_.ingest(0, event)
        self.assertEqual(groups(local.publish(0)), {frozenset((a, c)), frozenset((b,)), frozenset((d,))})
        self.assertEqual(groups(global_.publish(0)), {frozenset((a, d)), frozenset((b, c))})

    def test_kalman_only_changes_old_position_on_irregular_events(self):
        initial = LocalTrack(1, (0.0, 0.0), (0.0, 0.0))
        updated = initial.updated(61, (600.0, 0.0))
        self.assertEqual(updated.position(61, True), (600.0, 0.0))
        self.assertGreater(updated.position(111, True)[0], 1000)
        self.assertEqual(updated.position(1000, True), updated.position(121, True))
        a, b, c = ("A", "a"), ("A", "b"), ("B", "c")
        events = [(0, {a: point(0), b: point(1100)}), (60, {a: point(600), b: point(1100)}),
                  (119, {c: point(1170)})]
        for arm, target in (("hold_local", b), ("kf_local", a)):
            tracker = ContinuousTracker(arm)
            for stamp, reports in events:
                tracker.ingest(stamp, reports)
            self.assertIn(frozenset((target, c)), groups(tracker.publish(119)))

    def test_dormant_identity_outlives_position_and_same_source_replacement(self):
        a, b, later = ("A", "old"), ("B", "other"), ("A", "new")
        tracker = ContinuousTracker("hold_global")
        tracker.ingest(0, {a: point(1)})
        identity = tracker.publish(0)["tracks"][0]["track_id"]
        self.assertFalse(tracker.publish(61)["tracks"])
        tracker.ingest(70, {b: point(2)})
        self.assertEqual(tracker.publish(70)["tracks"][0]["track_id"], identity)
        self.assertEqual(groups(tracker.publish(71)), {frozenset((b,))})
        tracker.ingest(80, {later: point(2)})
        self.assertEqual(groups(tracker.publish(80)), {frozenset((b, later))})
        with self.assertRaises(ValueError):
            tracker.ingest(79, {a: point(1)})

    def test_equal_geometry_stays_pending_under_source_permutations(self):
        tracker = ContinuousTracker("hold_global")
        tracker.ingest(0, {("A", "1"): point(0), ("B", "1"): point(20), ("A", "2"): point(40)})
        self.assertEqual(len(tracker.publish(0)["tracks"]), 3)
        renamed = ContinuousTracker("hold_global")
        renamed.ingest(0, {("ZZ", "2"): point(40), ("AA", "1"): point(20), ("ZZ", "1"): point(0)})
        self.assertEqual(len(renamed.publish(0)["tracks"]), 3)


class ScoringOrderTests(unittest.TestCase):
    def test_all_arms_and_scenes_predicted_before_labels(self):
        calls = []
        raw = [{"source": "A", "batch": "a", "time": "0", "lat": "0", "lon": "0"},
               {"source": "B", "batch": "b", "time": "1.2", "lat": "0", "lon": "0"}]
        mapping = {("A", "a"): "1-2", ("B", "b"): "1-2"}

        def measurements(_archive, _manifest, scene, *, required_split):
            calls.append(("prediction", scene))
            self.assertEqual(required_split, "T_core")
            return raw

        def labels(_archive, _manifest, scene):
            calls.append(("scoring", scene))
            return mapping

        with TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = root / "manifest.json"
            manifest.write_text('{"components":{"1":"x","2":"y"}}', encoding="utf-8")
            with (patch.object(factorial, "ROSTER", {"sample": ("1", "2")}),
                  patch.object(factorial, "read_archive_rows", side_effect=measurements),
                  patch.object(factorial, "read_labels", side_effect=labels)):
                result = factorial._run((), manifest, root)
        self.assertEqual(calls, [("prediction", "1"), ("prediction", "2"), ("scoring", "1"), ("scoring", "2")])
        for arm in result["aggregate"].values():
            self.assertEqual(arm["counts"]["ticks"], 6)
            self.assertEqual(arm["pairs"]["cross_source"]["correct_pairs"], 2)
            self.assertEqual(arm["births"]["first_correct_by_seconds"]["1"], 2)


def snapshot(query_time, *groups):
    return dict(query_time=query_time,
                tracks=[dict(track_id=track_id, members=members) for track_id, members in groups])


class ContinuousMetricsTests(unittest.TestCase):
    def test_membership_pairs_mixed_duplicates_and_first_clean_link(self):
        left, sibling, right, other = ("A", "left"), ("A", "sibling"), ("B", "right"), ("C", "other")
        events = [(0, (left, sibling, other)), (.5, (right,))]
        labels = {left: "one", sibling: "one", right: "one", other: "two"}
        report = evaluate_publications(events, [
            snapshot(0, ("x", (left, sibling)), ("y", (other,))),
            snapshot(1, ("x", (left, right, other)), ("z", (sibling,))),
            snapshot(2, ("x", (left, right)), ("z", (sibling,)), ("y", (other,))),
            snapshot(3, ("x", (left, sibling, right)), ("y", (other,))),
        ], labels)
        self.assertEqual(report["pairs"]["cross_source"],
                         dict(truth_pairs=6, correct_pairs=4, missed_pairs=2, false_pairs=2))
        self.assertEqual(report["pairs"]["same_source"],
                         dict(truth_pairs=4, correct_pairs=2, missed_pairs=2, false_pairs=0))
        counts = report["counts"]
        self.assertEqual(counts["report_supported_target_seconds"], 8)
        self.assertEqual(counts["pure_tracked_target_seconds"], 7)
        self.assertEqual(counts["uniquely_tracked_target_seconds"], 6)
        self.assertEqual(counts["mixed_output_seconds"], 1)
        self.assertEqual(counts["duplicate_target_seconds"], 1)
        self.assertEqual(counts["id_switches_consecutive"], 1)
        self.assertEqual(counts["id_switches_after_gap"], 1)
        self.assertEqual(counts["reacquired_same_id"], 1)
        self.assertEqual(counts["reacquired_changed_id"], 1)
        self.assertEqual(counts["reacquired_while_report_supported"], 2)
        self.assertEqual(report["target_seconds_by_active_source_count"], {1: 5, 2: 3})
        self.assertEqual(report["by_source"]["A"]["report_supported_fragment_seconds"], 8)
        births = report["births"]
        self.assertEqual(births["first_publication"], dict(correct=0, incorrect=1, rejected=3, unpublished=0))
        self.assertEqual(births["by_opportunity"]["never_observed"]["births"], 3)
        self.assertEqual(births["by_opportunity"]["fresh"]["births"], 1)
        self.assertEqual(births["ever_correct"], 3)
        self.assertEqual(births["unconfirmed_by_end"], 1)
        self.assertEqual(births["first_correct_delay_seconds"]["sum"], 6.5)
        self.assertEqual(births["first_correct_delay_seconds"]["ceil_seconds_histogram"], {2: 2, 3: 1})

    def test_age_boundary_support_gap_and_identity_transfer(self):
        left, right, third = ("A", "left"), ("B", "right"), ("A", "other")
        events = [(0, (left,)), (0, (right,)), (62, (left,)), (63, (third,))]
        published = {
            0: (("x", (left, right)),),
            60: (("x", (left, right)),),
            61: (("x", (left, right)),),
            62: (("new", (left,)),),
            63: (("new", (left,)), ("x", (third,))),
        }
        report = evaluate_publications(events, (snapshot(tick, *published.get(tick, ())) for tick in range(64)),
                                       {left: "one", right: "one", third: "two"})
        self.assertEqual(report["pairs"]["cross_source"]["truth_pairs"], 61)
        self.assertEqual(report["births"]["by_opportunity"]["fresh"]["births"], 2)
        self.assertEqual(report["births"]["first_correct_delay_seconds"]["ceil_seconds_histogram"], {0: 2})
        counts = report["counts"]
        self.assertEqual(counts["reacquired_while_report_supported"], 1)
        self.assertEqual(counts["reacquired_after_report_support_gap"], 1)
        self.assertEqual(counts["system_id_identity_transfers"], 1)
        self.assertEqual(counts["unsupported_output_seconds"], 1)
        self.assertEqual(counts["stale_membership_entries"], 2)

    def test_repeated_members_deduplicate_pairs_and_leave_unpublished_births(self):
        left, right, missing = ("A", "left"), ("B", "right"), ("A", "missing")
        events = [(0, (left, right, missing))]
        report = evaluate_publications(events, [
            snapshot(0, ("x", (left, left, right)), ("y", (left, right))),
        ], {left: "one", right: "one", missing: "two"})
        self.assertEqual(report["pairs"]["cross_source"]["correct_pairs"], 1)
        self.assertEqual(report["counts"]["duplicate_membership_entries"], 1)
        self.assertEqual(report["counts"]["repeated_member_seconds"], 2)
        self.assertEqual(report["counts"]["duplicate_pure_outputs"], 1)
        self.assertEqual(report["counts"]["uniquely_tracked_target_seconds"], 0)
        self.assertEqual(report["births"]["first_publication"],
                         dict(correct=2, incorrect=0, rejected=0, unpublished=1))

    def test_rejects_future_members_and_missing_ticks(self):
        future = ("A", "future")
        with self.assertRaisesRegex(ValueError, "before its first report"):
            evaluate_publications([(1, (future,))], [snapshot(0, ("x", (future,)))], {future: "one"})
        with self.assertRaisesRegex(ValueError, "every consecutive"):
            evaluate_publications([], [snapshot(0), snapshot(2)], {})
