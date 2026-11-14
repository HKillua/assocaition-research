"""Check the common input and current peer baseline kernels."""
import math
from math import sqrt
import unittest

from online_observation.frechet_trajectory import fit_frechet_slots, frechet_centroid, trajectory_distance
from online_observation.lindenmaier_association import (
    DiagonalState, ExistenceMass, SensorModel, fuse_pair, pair_log_likelihood_ratio, update_existence,
)
from online_observation.peer_identity import CandidateGroup, IdentityReader
from online_observation.peer_prefix import LocalPrefix
from online_observation.peer_replay import replay_frames


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
