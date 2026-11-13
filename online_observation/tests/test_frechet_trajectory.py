from math import sqrt
import unittest

from online_observation.frechet_trajectory import frechet_centroid, trajectory_distance


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
