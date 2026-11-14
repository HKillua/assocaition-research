"""Check the two current peer baseline kernels."""
import math
from math import sqrt
import unittest

from online_observation.frechet_trajectory import frechet_centroid, trajectory_distance
from online_observation.lindenmaier_association import (
    DiagonalState, SensorModel, fuse_pair, pair_log_likelihood_ratio,
)


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
