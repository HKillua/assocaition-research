"""Diagonal-state association and two-track fusion from Lindenmaier et al. (2025).

The caller supplies states at a shared decision time, previous confirmed
global states predicted to that time, and declared sensor model parameters.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import chain
import math


@dataclass(frozen=True)
class DiagonalState:
    """Position and velocity in (east, east velocity, north, north velocity)."""

    mean: tuple[float, float, float, float]
    variances: tuple[float, float, float, float]

    def __post_init__(self):
        if (len(self.mean) != 4 or len(self.variances) != 4
                or not all(math.isfinite(value) for value in self.mean)
                or not all(math.isfinite(value) and value > 0 for value in self.variances)):
            raise ValueError("a diagonal state needs four finite means and positive finite variances")


@dataclass(frozen=True)
class SensorModel:
    """Constant source parameters in the units of the four-dimensional state."""

    state_volume: float
    tracking_probability: float
    birth_density: float
    clutter_density: float

    def __post_init__(self):
        if not math.isfinite(self.state_volume) or self.state_volume <= 0:
            raise ValueError("state volume must be positive and finite")
        if not math.isfinite(self.tracking_probability) or not 0 <= self.tracking_probability <= 1:
            raise ValueError("tracking probability must be in [0, 1]")
        densities = (self.birth_density, self.clutter_density)
        if not all(math.isfinite(value) and value >= 0 for value in densities):
            raise ValueError("birth and clutter densities must be finite and nonnegative")


def _difference_variances(left, right, correlation):
    if not math.isfinite(correlation) or not -1 < correlation < 1:
        raise ValueError("correlation must be strictly between -1 and 1")
    deviations = tuple(zip(map(math.sqrt, left.variances), map(math.sqrt, right.variances)))
    return tuple((a - b) ** 2 + 2 * (1 - correlation) * a * b for a, b in deviations)


def fuse_pair(left: DiagonalState, right: DiagonalState, *, correlation: float) -> DiagonalState:
    """Apply equations (45–47) with the diagonal correlation model of equation (7)."""
    difference_variances = _difference_variances(left, right, correlation)
    mean, variances = [], []
    for a, b, pa, pb, difference_variance in zip(
            left.mean, right.mean, left.variances, right.variances, difference_variances):
        std_a, std_b = math.sqrt(pa), math.sqrt(pb)
        cross_covariance = correlation * std_a * std_b
        gain = (pa - cross_covariance) / difference_variance
        mean.append(a + gain * (b - a))
        variances.append((pa / difference_variance) * pb * (1 - correlation**2))
    return DiagonalState(tuple(mean), tuple(variances))


def _log_gaussian(squared_distance, variances):
    return -0.5 * (squared_distance + len(variances) * math.log(math.tau)
                   + math.fsum(map(math.log, variances)))


def _squared_distance(left, right, variances):
    return math.fsum(((b - a) / math.sqrt(variance)) ** 2
                     for a, b, variance in zip(left, right, variances))


def _log_sum_exp(log_values):
    values = tuple(log_values)
    peak = max(values, default=-math.inf)
    if peak == -math.inf:
        return peak
    return peak + math.log(math.fsum(math.exp(value - peak) for value in values))


def _log_prior(state, confirmed_states, volume, prior_gate):
    def nearby_gaussians():
        for previous in confirmed_states:
            if math.dist(state.mean, previous.mean) < prior_gate:
                variances = tuple(a + b for a, b in zip(state.variances, previous.variances))
                yield _log_gaussian(_squared_distance(state.mean, previous.mean, variances), variances)

    return _log_sum_exp(chain((-math.log(volume),), nearby_gaussians()))


def _log_density(density):
    return math.log(density) if density > 0 else -math.inf


def _log_unassignment(sensor, local_prior, fused_prior):
    log_inverse_volume = -math.log(sensor.state_volume)
    return _log_sum_exp((
        _log_density(sensor.birth_density) + log_inverse_volume - local_prior,
        local_prior + log_inverse_volume - _log_sum_exp((local_prior, fused_prior)),
        _log_density(sensor.clutter_density),
    ))


def pair_log_likelihood_ratio(
    left: DiagonalState,
    right: DiagonalState,
    left_sensor: SensorModel,
    right_sensor: SensorModel,
    *,
    state_volume: float,
    correlation: float,
    prior_gate: float,
    distance_gate: float,
    confirmed_states: tuple[DiagonalState, ...] = (),
) -> float:
    """Compute equations (29–37) for one cross-source edge at the decision time.

    An empty confirmed set applies the diffuse prior to the matching and
    unassignment terms. A positive return value favors a match. Zero means
    equality or the paper's distance-gate approximation to an unscored edge.
    """
    if not all(math.isfinite(value) and value > 0 for value in (state_volume, prior_gate, distance_gate)):
        raise ValueError("state volume and both gates must be positive and finite")
    difference_variances = _difference_variances(left, right, correlation)
    distance = _squared_distance(left.mean, right.mean, difference_variances)
    if distance >= distance_gate:
        return 0.0

    fused = fuse_pair(left, right, correlation=correlation)
    fused_prior = _log_prior(fused, confirmed_states, state_volume, prior_gate)
    left_prior = _log_prior(left, confirmed_states, left_sensor.state_volume, prior_gate)
    right_prior = _log_prior(right, confirmed_states, right_sensor.state_volume, prior_gate)
    match = math.fsum((
        _log_gaussian(distance, difference_variances), fused_prior,
        _log_density(left_sensor.tracking_probability), _log_density(right_sensor.tracking_probability),
    ))
    return match - _log_unassignment(left_sensor, left_prior, fused_prior) - _log_unassignment(
        right_sensor, right_prior, fused_prior)
