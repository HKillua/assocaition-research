import math
import unittest

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


if __name__ == "__main__":
    unittest.main()
