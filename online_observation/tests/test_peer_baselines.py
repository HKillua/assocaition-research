"""Check the common input and current peer baseline kernels."""
import math
from math import sqrt
import unittest

from online_observation.evaluation_data import ReferenceData
from online_observation.frechet_trajectory import (
    fit_frechet_slots, frechet_centroid, search_frechet_slots, trajectory_distance,
)
from online_observation.lindenmaier_association import (
    DiagonalState, ExistenceMass, SensorModel, fuse_pair, pair_log_likelihood_ratio, update_existence,
)
from online_observation.peer_experiment import FrechetArm, _conflict_decay
from online_observation.peer_identity import CandidateGroup, IdentityReader
from online_observation.peer_lindenmaier import LindenmaierArm
from online_observation.peer_prefix import LocalPrefix, PrefixObservation
from online_observation.peer_replay import ReplayFrame, replay_frames
from online_observation.peer_score import score_peer_replay


class PeerScoreTests(unittest.TestCase):
    def test_exact_first_decisions_and_common_grid_score_different_clocks(self):
        a, b, c = ("A", "1"), ("B", "2"), ("B", "3")
        events = [(0.25, (a, b)), (0.75, (c,))]
        labels = {a: "one", b: "two", c: "one"}
        publications = [
            dict(query_time=0.25, tracks=[dict(track_id="1", members=(a, b))]),
            dict(query_time=0.75, tracks=[dict(track_id="1", members=(a, c)),
                                         dict(track_id="2", members=(b,))]),
        ]
        score = score_peer_replay(events, publications, labels, stop=1.0)
        native = score["native_births"]
        self.assertEqual(native["first_decisions"], dict(correct=1, incorrect=2, independent=0, unpublished=0))
        self.assertEqual(native["first_wrong_without_true_peer_at_release"], 2)
        self.assertEqual(native["confirmed_within_seconds"]["20"], dict(confirmed=2, censored=1, unconfirmed=0))
        self.assertTrue(score["population"]["is_sparse_scene"])
        self.assertEqual(native["confirmation_wait_seconds"]["max"], 0.5)
        self.assertEqual(score["integer_grid"]["pairs"]["cross_source"]["false_pairs"], 0)
        self.assertEqual(score["false_chains"]["pair_seconds"], 0.5)

    def test_frozen_membership_does_not_bridge_unpublished_report_updates(self):
        a, b = ("A", "1"), ("B", "2")
        labels = {a: "one", b: "two"}
        events = [(0.25, (a, b)), (30.25, (a, b)), (80.25, (a, b)), (90.25, (a, b))]
        publications = [dict(query_time=stamp, tracks=[dict(track_id="1", members=(a, b))])
                        for stamp in (0.25, 30.25, 110.25)]
        score = score_peer_replay(events, publications, labels, stop=130.25)
        chains = score["false_chains"]
        self.assertEqual(chains["chains"], 2)
        self.assertEqual(chains["ends"], {"expiry": 1, "right_censored": 1})
        self.assertEqual(chains["pair_seconds"], 110.0)
        self.assertEqual(chains["over_60_seconds"], dict(chains=1, pair_seconds=90.0))
        self.assertEqual(score["integer_grid"]["pairs"]["cross_source"]["false_pairs"], 110)

    def test_reference_denominator_counts_unpublished_targets(self):
        a, b = ("A", "1"), ("B", "2")
        labels = {a: "one", b: "two"}
        events = [(0.0, {a: (0.0, 0.0), b: (0.0, 0.0)})]
        publications = [dict(query_time=0.0, service_seconds=0.125,
                             tracks=[dict(track_id="1", members=(a,), position_m=(3.0, 4.0))])]
        samples = ((100.0, 0.0, 0.0, None, None), (101.0, 0.0, 0.0, None, None))
        reference = ReferenceData({"one": samples, "two": samples}, 100.0, 60.0)
        score = score_peer_replay(events, publications, labels, stop=1.0, reference=reference,
                                  include_birth_details=True)
        self.assertEqual(score["position"]["support"]["reference_supported_target_seconds"], 4)
        self.assertEqual(score["position"]["errors"]["all"]["count"], 2)
        self.assertEqual(score["position"]["errors"]["single_source"]["mae_m"], 5.0)
        self.assertEqual(score["service_seconds"]["release_to_ready"]["p95"], 0.125)
        self.assertEqual([row["first_decision"] for row in score["birth_details"]],
                         ["independent", "unpublished"])


class IdentityReaderTests(unittest.TestCase):
    def test_merge_keeps_closer_id_and_ambiguous_split_retires_it(self):
        reader = IdentityReader()
        a, b = ("A", "1"), ("B", "2")
        left = CandidateGroup((a,), (0.0, 0.0), (0.0,))
        right = CandidateGroup((b,), (10.0, 0.0), (1.0,))
        first, = reader.publish(0.0, [left])
        continued, independent = reader.publish(1.0, [right, left])
        self.assertEqual(first.track_id, continued.track_id)
        with self.assertRaisesRegex(ValueError, "only one group"):
            reader.publish(2.0, [left, left])
        joined, = reader.publish(2.0, [CandidateGroup((b, a), (2.0, 0.0), (1.0, 0.0))])
        self.assertEqual(joined.track_id, first.track_id)
        self.assertEqual(joined.candidate.members, (a, b))
        self.assertEqual(first.candidate.members, (a,))
        moved_right = CandidateGroup((b,), (4.0, 0.0), (3.0,))
        split = reader.publish(3.0, [left, moved_right])
        self.assertEqual(len({item.track_id for item in split}), 2)
        self.assertTrue({item.track_id for item in split}.isdisjoint((first.track_id, independent.track_id)))

    def test_geometry_abstains_for_fresh_same_source_and_tied_dormant_ids(self):
        reader = IdentityReader()

        def group(batch, x, observed):
            return CandidateGroup((("A", batch),), (x, 0.0), (observed,))

        old, other = reader.publish(0.0, [group("1", -100.0, 0.0), group("2", 100.0, 0.0)])
        blocked, = reader.publish(1.0, [group("3", 0.0, 1.0)])
        self.assertNotIn(blocked.track_id, (old.track_id, other.track_id))
        tied, = reader.publish(61.0, [group("4", 0.0, 61.0)])
        self.assertNotIn(tied.track_id, (old.track_id, other.track_id, blocked.track_id))
        returned, = reader.publish(62.0, [group("1", -100.0, 62.0)])
        self.assertEqual(returned.track_id, old.track_id)
        newer, = reader.publish(123.0, [group("5", -100.0, 123.0)])
        self.assertEqual(newer.track_id, old.track_id)
        expired, = reader.publish(724.0, [group("5", -100.0, 724.0)])
        self.assertNotEqual(expired.track_id, old.track_id)


class PeerReplayTests(unittest.TestCase):
    def test_fixed_boundary_includes_exact_arrivals_and_keeps_frozen_frames(self):
        left, right = ("A", "1"), ("B", "2")
        events = [
            (0.5, {left: (0.0, 0.0)}),
            (15.5, {left: (0.0, 0.001)}),
            (20.5, {right: (0.0, 0.0)}),
            (21.0, {right: (0.0, 0.001)}),
        ]
        frames = list(replay_frames(events, interval_seconds=20))
        self.assertEqual([frame.stamp for frame in frames], [20.5, 40.5])
        self.assertEqual(frames[0].arrivals,
                         ((0.5, (left,)), (15.5, (left,)), (20.5, (right,))))
        self.assertEqual(frames[0].observations[right].observed_at, 20.5)
        self.assertEqual(frames[1].observations[right].observed_at, 21.0)
        with self.assertRaises(TypeError):
            frames[0].observations[right] = frames[1].observations[right]

    def test_native_refresh_at_expiry_never_publishes_an_intermediate_drop(self):
        left, right = ("A", "1"), ("B", "2")
        refresh = math.nextafter(60.0, math.inf)
        frames = list(replay_frames([
            (0.0, {left: (0.0, 0.0), right: (0.0, 0.0)}),
            (refresh, {left: (0.0, 0.001)}),
        ]))
        self.assertEqual([frame.stamp for frame in frames],
                         [0.0, refresh, math.nextafter(refresh + 60.0, math.inf)])
        self.assertEqual(set(frames[1].observations), {left})
        self.assertEqual(frames[1].arrivals, ((refresh, (left,)),))
        self.assertEqual(dict(frames[2].observations), {})
        self.assertEqual(frames[2].arrivals, ())


class LocalPrefixTests(unittest.TestCase):
    def test_snapshot_predicts_from_posterior_without_absorbing_a_report(self):
        prefix = LocalPrefix()
        key = ("A", "1")
        prefix.ingest(0.25, {key: (0.0, 0.0)})
        prefix.ingest(30.25, {key: (0.0, 0.001)})
        posterior = prefix.snapshot(30.25)[key]
        ahead = prefix.snapshot(42.75)[key]

        self.assertEqual(posterior.observed_at, 30.25)
        self.assertEqual(ahead.observed_at, posterior.observed_at)
        self.assertEqual(ahead.raw_location, posterior.raw_location)
        east, east_speed, north, north_speed = posterior.state.mean
        self.assertGreater(east_speed, 0.0)
        self.assertLess(east, posterior.raw_location[0])
        self.assertAlmostEqual(ahead.state.mean[0], east + 12.5 * east_speed)
        self.assertEqual(ahead.state.mean[1:], (east_speed, north, north_speed))
        self.assertGreater(ahead.state.variances[0], posterior.state.variances[0])
        self.assertAlmostEqual(ahead.state.variances[1] - posterior.state.variances[1], 1.25)
        self.assertEqual(prefix.snapshot(42.75)[key], ahead)

    def test_cutoff_and_no_backdated_reads_or_releases(self):
        prefix = LocalPrefix()
        first, second = ("A", "1"), ("B", "2")
        self.assertEqual(prefix.snapshot(0.0), {})
        prefix.ingest(0.1, {first: (0.0, 0.0)})
        cutoff = 0.1 + 60.0
        at_cutoff = prefix.snapshot(cutoff)
        self.assertEqual(set(at_cutoff), {first})
        with self.assertRaises(ValueError):
            prefix.ingest(cutoff, {second: (0.0, 0.0)})
        self.assertEqual(prefix.snapshot(math.nextafter(cutoff, math.inf)), {})
        prefix.ingest(100.0, {second: (0.0, 0.0)})
        self.assertEqual(set(prefix.snapshot(100.0)), {second})
        self.assertEqual(set(at_cutoff), {first})
        with self.assertRaises(ValueError):
            prefix.snapshot(99.0)

    def test_memory_expires_only_after_full_interval(self):
        key = ("A", "1")
        for delay in (600.0, 600.01):
            with self.subTest(delay=delay):
                prefix = LocalPrefix()
                prefix.ingest(0.0, {key: (0.0, 0.0)})
                prefix.snapshot(delay - 0.001)
                prefix.ingest(delay, {key: (0.0, 0.001)})
                east_speed = prefix.snapshot(delay)[key].state.mean[1]
                if delay == 600.0:
                    self.assertGreater(east_speed, 0.0)
                else:
                    self.assertEqual(east_speed, 0.0)


class LindenmaierAssociationTests(unittest.TestCase):
    def setUp(self):
        self.left = DiagonalState((0.0, 0.0, 0.0, 0.0), (4.0,) * 4)
        self.right = DiagonalState((4.0, 0.0, 0.0, 0.0), (4.0,) * 4)
        self.sensor = SensorModel(50.0, 0.9, 0.002, 0.001)
        self.options = dict(state_volume=100.0, correlation=0.5, prior_gate=20.0, distance_gate=25.0)

    def score(self, **overrides):
        return pair_log_likelihood_ratio(
            self.left, self.right, self.sensor, self.sensor, **(self.options | overrides))

    def test_equal_variance_correlated_fusion(self):
        fused = fuse_pair(self.left, self.right, correlation=0.5)
        self.assertEqual(fused.mean, (2.0, 0.0, 0.0, 0.0))
        self.assertEqual(fused.variances, (3.0,) * 4)
        self.assertEqual(fused, fuse_pair(self.right, self.left, correlation=0.5))

    def test_informative_prior_enters_match_and_both_unassignment_terms(self):
        previous = DiagonalState((2.0, 0.0, 0.0, 0.0), (4.0,) * 4)
        fused_prior = 1 / 100 + 1 / (math.tau * 7) ** 2
        local_prior = 1 / 50 + math.exp(-0.25) / (math.tau * 8) ** 2
        null = (0.002 / 50 / local_prior) + local_prior / 50 / (local_prior + fused_prior) + 0.001
        expected = math.log(0.9**2 * fused_prior * math.exp(-2) / (math.tau * 4) ** 2 / null**2)
        self.assertAlmostEqual(self.score(confirmed_states=(previous,)), expected)

    def test_no_confirmed_states_nearby_restores_diffuse_prior(self):
        far = DiagonalState((100.0, 0.0, 0.0, 0.0), (4.0,) * 4)
        null = 0.002 + (1 / 50)**2 / (1 / 50 + 1 / 100) + 0.001
        expected = math.log(0.9**2 * (1 / 100) * math.exp(-2) / (math.tau * 4) ** 2 / null**2)
        self.assertAlmostEqual(self.score(), expected)
        self.assertEqual(self.score(), self.score(confirmed_states=(far,)))

    def test_equal_diffuse_priors_halve_spawning_contribution(self):
        expected_null = 0.002 + 1 / (2 * 50) + 0.001
        expected = math.log(0.9**2 * math.exp(-2) / (50 * (math.tau * 4) ** 2 * expected_null**2))
        self.assertAlmostEqual(self.score(state_volume=50.0), expected)

    def test_normalized_distance_at_gate_is_unscored(self):
        self.assertEqual(self.score(distance_gate=4.0), 0.0)
        self.assertNotEqual(self.score(distance_gate=4.01), 0.0)


class FrechetTrajectoryTests(unittest.TestCase):
    def test_only_new_report_inside_competing_component_enables_decay(self):
        def trajectory(*xs):
            return {grid: (x, 0) for grid, x in enumerate(xs, 1)}

        left = [trajectory(0, 0, 0), trajectory(1000, 1000, 1000), trajectory(9000, 9000, 9000)]
        right = [trajectory(0, 0, 1000), trajectory(1000, 1000, 0), trajectory(9000, 9000, 9000)]
        self.assertEqual(_conflict_decay((left, right), 3, {(0, 0)}),
                         (((True, True, False), (True, True, False)), 1))
        self.assertEqual(_conflict_decay((left, right), 3, {(0, 2)}),
                         (((False, False, False), (False, False, False)), 0))

    def test_history_arms_fix_candidate_order_and_keep_latest_native_grid(self):
        left, right = ("A", "1"), ("B", "1")
        events = [(0, {left: (0, 0), right: (10, 0)}),
                  (45, {left: (3, 0)}), (65, {right: (12, 0)})]
        arms = [FrechetArm(unknown_mask=True, history=policy, capture_fit=True)
                for policy in ("full", "current", "unique")]
        for frame in replay_frames(events, interval_seconds=20):
            for arm in arms:
                arm.publish(frame)
            snapshots = [arm.snapshot for arm in arms]
            self.assertTrue(all(row["keys"] == snapshots[0]["keys"] for row in snapshots))
            if frame.stamp == 60:
                self.assertEqual(snapshots[0]["tags"], [[{1: 0, 2: 0, 3: 45}], [{1: 0, 2: 0, 3: 0}]])
                self.assertEqual([list(side[0]) for side in snapshots[1]["trajectories"]], [[3], [3]])
                self.assertEqual([list(side[0]) for side in snapshots[2]["trajectories"]], [[2, 3], [3]])

    def test_distance_counts_missing_and_caps_large_residual(self):
        first = {0: (0, 0), 1: (0, 0), 3: (0, 0)}
        second = {0: (3, 4), 2: (0, 0), 3: (20, 0)}
        expected = sqrt((25 + 100 + 100 + 100) / 4)
        self.assertAlmostEqual(trajectory_distance(first, second, cutoff=10), expected)
        self.assertAlmostEqual(trajectory_distance(second, first, cutoff=10), expected)
        self.assertEqual(trajectory_distance(first, {}, cutoff=10), 10)
        self.assertEqual(trajectory_distance({}, {}, cutoff=10), 0)

    def test_overlap_uses_quadratic_minimum_and_deterministic_cap(self):
        first = {0: (0, 0)}
        close = {0: (3, 4)}
        self.assertEqual(frechet_centroid(first, close, cutoff=10), {0: (1.5, 2)})
        self.assertEqual(
            frechet_centroid(first, close, cutoff=10, weights=(3, 1)),
            {0: (0.75, 1)},
        )

        far = {0: (15, 0)}
        # The midpoint is inside both caps but still costs more than an endpoint.
        self.assertEqual(frechet_centroid(first, far, cutoff=10), first)
        self.assertEqual(frechet_centroid(far, first, cutoff=10), first)
        self.assertEqual(frechet_centroid(first, far, cutoff=10, weights=(1, 3)), far)

    def test_domain_flip_reweights_common_knots_using_new_union_sizes(self):
        first = {0: (0, 0), 1: (0, 0)}
        second = {0: (2, 0), 2: (2, 0), 3: (2, 0)}
        centroid = frechet_centroid(first, second, cutoff=20, weights=(3, 1))
        self.assertEqual(list(centroid), [0, 1])
        self.assertAlmostEqual(centroid[0][0], 2 / 7)
        self.assertEqual(centroid[1], first[1])

    def test_single_source_copies_samples_and_explicit_empty_is_a_sample(self):
        first = {3: (8, 1), 0: (2, 4)}
        centroid = frechet_centroid(first, cutoff=10)
        self.assertEqual(centroid, first)
        self.assertEqual(list(centroid), [0, 3])
        self.assertIsNot(centroid, first)
        self.assertEqual(frechet_centroid(first, {}, cutoff=10), first)
        self.assertEqual(frechet_centroid({}, {}, cutoff=10), {})

        # An explicit empty sample can win a strict drop when its weight is larger.
        self.assertEqual(
            frechet_centroid({0: (2, 4)}, {}, cutoff=10, weights=(1, 2)),
            {},
        )

    def test_disjoint_samples_do_not_fill_gaps(self):
        first = {0: (2, 4)}
        second = {3: (8, 1)}
        self.assertEqual(frechet_centroid(first, second, cutoff=10), first | second)

    def test_reject_invalid_units_or_search_parameters(self):
        with self.assertRaises(ValueError):
            trajectory_distance({0: (float("inf"), 1)}, {}, cutoff=1)
        with self.assertRaises(ValueError):
            trajectory_distance({0.5: (0, 1)}, {}, cutoff=1)
        with self.assertRaises(ValueError):
            frechet_centroid({}, cutoff=0)
        with self.assertRaises(ValueError):
            frechet_centroid({}, cutoff=1, weights=(1, 0))
        with self.assertRaises(ValueError):
            frechet_centroid({}, cutoff=1, max_sweeps=0)

    def test_fixed_slots_use_per_source_cardinality_weights(self):
        left = ({0: (0, 0)},)
        right = ({0: (6, 0)}, {0: (100, 0)})
        options = dict(cutoff=10, cardinality_penalty=8)
        centers, cost = fit_frechet_slots(left, right[:1], [(0, 0)], **options)
        self.assertEqual(centers, ({0: (3, 0)},))
        self.assertAlmostEqual(cost, 9.0)
        centers, cost = fit_frechet_slots(left, right, [(0, 0)], **options)
        self.assertEqual(centers, ({0: (2, 0)},))
        self.assertAlmostEqual(cost, (4 + (16 + 64) / 2) / 2)
        centers, cost = fit_frechet_slots(left, right, [(0, 0), (None, 1)], **options)
        self.assertEqual(centers, ({0: (3, 0)}, right[1]))
        self.assertAlmostEqual(cost, ((9 + 64) / 2 + 9 / 2) / 2)

    def test_fixed_slots_charge_empty_side_and_validate_assignments(self):
        left = ({0: (0, 0)},)
        options = dict(cutoff=10, cardinality_penalty=8)
        self.assertEqual(fit_frechet_slots((), (), (), **options), ((), 0))
        self.assertEqual(fit_frechet_slots(left, (), (), **options), ((), 32))
        self.assertEqual(fit_frechet_slots(left, (), [(0, None)], **options), (left, 32))
        for slots in ([(None, None)], [(1, 0)], [(0, 0), (0, None)], [(0, None)]):
            with self.subTest(slots=slots), self.assertRaises(ValueError):
                fit_frechet_slots(left, left, slots, **options)

    def test_set_search_retains_far_singletons_at_metric_boundary(self):
        left, right = ({0: (0, 0)},), ({0: (22000, 0)},)
        options = dict(cutoff=4000.0, cardinality_penalty=4000.0 / sqrt(2))
        result = search_frechet_slots(left, right, **options)
        self.assertEqual(result.slots, ((0, None), (None, 0)))
        self.assertEqual(result.centers, left + right)
        self.assertAlmostEqual(result.objective, options["cardinality_penalty"] ** 2 / 2)
        _, empty_cost = fit_frechet_slots(left, right, (), **options)
        _, fused_cost = fit_frechet_slots(left, right, [(0, 0)], **options)
        self.assertAlmostEqual(empty_cost, fused_cost)
        self.assertEqual(search_frechet_slots(left, (), **options).slots, ((0, None),))

    def test_set_search_matches_geometry_and_masks_only_with_joint_support(self):
        options = dict(cutoff=4000.0, cardinality_penalty=4000.0 / sqrt(2))
        left = ({0: (0, 0)}, {0: (22000, 0)})
        right = ({0: (22002, 0)}, {0: (4, 0)})
        result = search_frechet_slots(left, right, **options)
        self.assertEqual(set(result.slots), {(0, 1), (1, 0)})
        self.assertAlmostEqual(result.objective, 2.5)
        self.assertEqual(search_frechet_slots(left, right, **options), result)

        # Three one-sided knots dominate the unmasked fit, but the coeval points agree.
        sparse_left = ({0: (0, 0), 1: (0, 0)},)
        sparse_right = ({1: (2, 0), 2: (2, 0), 3: (2, 0)},)
        masked = search_frechet_slots(sparse_left, sparse_right, **options, unknown_mask=True)
        self.assertEqual(masked.slots, ((0, 0),))
        self.assertAlmostEqual(masked.objective, 1.0)
        self.assertEqual(masked.centers, ({0: (0, 0), 1: (1, 0), 2: (2, 0), 3: (2, 0)},))
        lacking_joint_support = search_frechet_slots(left[:1], ({1: (0, 0)},), **options, unknown_mask=True)
        self.assertEqual(lacking_joint_support.slots, ((0, None), (None, 0)))


class LindenmaierExistenceTests(unittest.TestCase):
    def test_fresh_sources_then_discounted_global_prior(self):
        local = ExistenceMass.from_local(existence_probability=0.75, tracking_probability=0.8,
                                        trust=0.5)
        self.assertAlmostEqual(local.exists, 0.3)
        self.assertAlmostEqual(local.absent, 0.1)
        self.assertAlmostEqual(local.unknown, 0.6)
        first = ExistenceMass(0.6, 0.1, 0.3)
        second = ExistenceMass(0.2, 0.4, 0.4)
        result = update_existence(ExistenceMass(0.4, 0.4, 0.2), (first, second), gamma=0.5)
        # Dempster gives masses proportional to (0.42, 0.20, 0.12). The
        # discounted global masses are (0.2, 0.2, 0.6). Accumulate once.
        self.assertAlmostEqual(result.exists, 23 / 41)
        self.assertAlmostEqual(result.absent, 12 / 41)
        self.assertAlmostEqual(result.unknown, 6 / 41)
        self.assertAlmostEqual(result.probability, 26 / 41)

    def test_silence_only_discounts_existing_evidence(self):
        prior = ExistenceMass(0.75, 0.0, 0.25)
        first = update_existence(prior, (), gamma=0.5)
        split = update_existence(first, (ExistenceMass(),), gamma=0.5)
        unbroken = update_existence(prior, (), gamma=0.25)
        self.assertEqual(split, unbroken)
        self.assertEqual(unbroken.probability, 0.59375)
        self.assertEqual(update_existence(prior, (ExistenceMass(),), gamma=1), prior)

    def test_singular_fusion_requires_explicit_external_resolution(self):
        exists = ExistenceMass(1.0, 0.0, 0.0)
        absent = ExistenceMass(0.0, 1.0, 0.0)
        with self.assertRaisesRegex(ValueError, "total conflict"):
            update_existence(ExistenceMass(), (exists, absent), gamma=1)
        with self.assertRaisesRegex(ValueError, "both masses have zero uncertainty"):
            update_existence(exists, (exists,), gamma=1)
        self.assertEqual(update_existence(exists, (absent,), gamma=0.9), absent)


class LindenmaierArmTests(unittest.TestCase):
    def test_feedback_changes_the_null_decision_only_after_confirmation(self):
        a, b = ("A", "1"), ("B", "2")

        def reading(east, stamp):
            state = DiagonalState((east, 0, 0, 0), (22500, 144, 22500, 144))
            return PrefixObservation(stamp, (east, 0), state)

        pair_at_first = ReplayFrame(0, {a: reading(-700, 0), b: reading(-150, 0)}, ((0, (a, b)),))
        self.assertEqual(len(LindenmaierArm(feedback=True).publish(pair_at_first)), 2)

        final_ids = []
        for feedback in (False, True):
            arm = LindenmaierArm(feedback=feedback)
            for stamp in (0, 1, 2):
                initial, = arm.publish(ReplayFrame(stamp, {a: reading(0, stamp)}, ((stamp, (a,)),)))
            self.assertTrue(arm.existence_by_id[initial.track_id].confirmed)
            final = ReplayFrame(3, {a: reading(-700, 3), b: reading(-150, 3)}, ((3, (a, b)),))
            groups = arm.publish(final)
            expected = [(a, b)] if feedback else [(a,), (b,)]
            self.assertEqual([item.candidate.members for item in groups], expected)
            self.assertEqual(groups[0].track_id, initial.track_id)
            self.assertEqual(arm.diagnostics["scored_pairs"], 1)
            self.assertEqual(arm.diagnostics["scored_pairs_with_informative_prior"], int(feedback))
            final_ids.append(groups[0].track_id)
        self.assertEqual(*final_ids)

    def test_boundary_keeps_singletons_and_never_reuses_a_report_as_evidence(self):
        a, b, c = ("A", "1"), ("B", "2"), ("B", "3")
        arm = LindenmaierArm(feedback=True)
        events = [(0, {a: (0, 0), b: (0, 0), c: (0, 0)}),
                  (10, {a: (0, 0), b: (0, 0), c: (0, 0)}), (90, {a: (0, 0)})]
        frames = iter(replay_frames(events, interval_seconds=20))
        first = arm.publish(next(frames))
        self.assertEqual([item.candidate.members for item in first], [(a,), (b,), (c,)])
        self.assertEqual(arm.diagnostics["positive_pairs_abstained_on_exact_tie"], 2)
        self.assertEqual(arm.diagnostics["existence_report_updates"], 6)
        before = arm.existence_by_id[first[0].track_id].probability
        self.assertEqual(arm.publish(next(frames)), first)
        after = arm.existence_by_id[first[0].track_id].probability
        self.assertAlmostEqual(after, 0.5 + (before - 0.5) * 2 ** (-20 / 60))
        self.assertEqual(arm.diagnostics["existence_report_updates"], 6)
        self.assertEqual([len(arm.publish(frame)) for frame in frames], [3, 0, 1])
        self.assertEqual(arm.diagnostics["existence_report_updates"], 7)
