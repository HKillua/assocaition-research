"""Order-two Euclidean trajectory consensus from Nguyen et al., arXiv:2504.20391v3."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from math import dist, fsum, isfinite, sqrt
from numbers import Integral

Point = tuple[float, float]
Trajectory = Mapping[int, Point]


def _samples(trajectory: Trajectory) -> dict[int, Point]:
    samples = {}
    for knot, point in trajectory.items():
        if isinstance(knot, bool) or not isinstance(knot, Integral):
            raise ValueError("trajectory knot must be an integer grid index")
        x, y = point
        if not (isfinite(x) and isfinite(y)):
            raise ValueError("trajectory coordinates must be finite")
        samples[int(knot)] = (float(x), float(y))
    return samples


def _validate_cutoff(cutoff: float) -> None:
    if not isfinite(cutoff) or cutoff <= 0:
        raise ValueError("cutoff must be finite and positive")


def _normalized_point_loss(first: Point, second: Point, cutoff: float) -> float:
    return (min(dist(first, second), cutoff) / cutoff) ** 2


def _normalized_trajectory_loss(left: Trajectory, right: Trajectory, cutoff: float) -> float:
    left_knots = left.keys()
    right_knots = right.keys()
    union_size = len(left_knots | right_knots)
    if not union_size:
        return 0.0
    overlap_loss = fsum(
        _normalized_point_loss(left[knot], right[knot], cutoff)
        for knot in left_knots & right_knots
    )
    return (len(left_knots ^ right_knots) + overlap_loss) / union_size


def trajectory_distance(left: Trajectory, right: Trajectory, *, cutoff: float) -> float:
    """Return the order-two OSPA trajectory distance in position units (Eq. 2).

    Both trajectories use the caller's already sampled integer time grid. Missing
    on one side costs ``cutoff`` and missing on both sides does not contribute.
    Two empty trajectories have distance zero. Samples are never interpolated.
    """
    _validate_cutoff(cutoff)
    return cutoff * sqrt(_normalized_trajectory_loss(_samples(left), _samples(right), cutoff))


def _common_position(
    left: Point, right: Point, left_weight: float, right_weight: float, cutoff: float
) -> Point:
    # Canonical endpoint order also fixes ties when both endpoints minimize the loss.
    if right < left:
        left, right = right, left
        left_weight, right_weight = right_weight, left_weight

    fraction = right_weight / (left_weight + right_weight)
    mean = (
        (1 - fraction) * left[0] + fraction * right[0],
        (1 - fraction) * left[1] + fraction * right[1],
    )

    # The capped sum is the minimum of four uncapped objectives. Their minimizers
    # are the weighted mean, either endpoint, and any point for the all-capped case.
    def loss(point: Point) -> float:
        return (
            left_weight * _normalized_point_loss(point, left, cutoff)
            + right_weight * _normalized_point_loss(point, right, cutoff)
        )

    return min((left, mean, right), key=loss)


def frechet_centroid(
    left: Trajectory,
    right: Trajectory | None = None,
    *,
    cutoff: float,
    weights: tuple[float, float] = (1.0, 1.0),
    max_sweeps: int = 5,
    tolerance: float = 0.0,
) -> dict[int, Point]:
    """Compute a two-sample Fréchet trajectory by greedy domain search (Alg. 1).

    A missing argument (``right=None``) uses the sole trajectory directly. An
    explicit empty trajectory is a sample with the one-sided penalties of Eq. 2.
    An equal-weight empty sample retains the nonempty sample on a tie. Sample
    weights are positive and relative. Each included knot is solved exactly for
    its proposed domain using sample weight divided by its union size (Prop. 1).

    The search starts at the union, tries knot flips in chronological order, and
    accepts strict improvements. It stops after ``max_sweeps`` (the paper's five
    for trajectory consensus by default) or a sweep improving the normalized
    squared objective by at most ``tolerance``. The threshold uses the complete
    sweep's reduction. The domain search can stop at a local minimum. The caller
    decides which sampled prefix is available and no other knots are produced.
    """
    _validate_cutoff(cutoff)
    if isinstance(max_sweeps, bool) or not isinstance(max_sweeps, Integral) or max_sweeps < 1:
        raise ValueError("max_sweeps must be a positive integer")
    if not isfinite(tolerance) or tolerance < 0:
        raise ValueError("tolerance must be finite and nonnegative")
    left_weight, right_weight = weights
    if any(not isfinite(weight) or weight <= 0 for weight in weights):
        raise ValueError("sample weights must be finite and positive")
    scale = max(weights)
    left_weight /= scale
    right_weight /= scale

    first = _samples(left)
    if right is None:
        return dict(sorted(first.items()))
    second = _samples(right)
    knots = sorted(first.keys() | second.keys())

    def fit(domain: set[int]) -> tuple[dict[int, Point], float]:
        first_union_size = len(first.keys() | domain)
        second_union_size = len(second.keys() | domain)
        fitted = {}
        for knot in sorted(domain):
            if knot not in first:
                fitted[knot] = second[knot]
            elif knot not in second:
                fitted[knot] = first[knot]
            else:
                fitted[knot] = _common_position(
                    first[knot], second[knot],
                    left_weight / first_union_size, right_weight / second_union_size,
                    cutoff,
                )
        objective = (
            left_weight * _normalized_trajectory_loss(fitted, first, cutoff)
            + right_weight * _normalized_trajectory_loss(fitted, second, cutoff)
        ) / (left_weight + right_weight)
        return fitted, objective

    # Outside the union, adding a knot incurs the maximum loss for every sample
    # and cannot improve its average. Those knots are irrelevant to a strict search.
    domain = set(knots)
    fitted, objective = fit(domain)
    for _ in range(max_sweeps):
        previous = objective
        for knot in knots:
            trial_domain = domain ^ {knot}
            trial_fit, trial_objective = fit(trial_domain)
            if trial_objective < objective:
                domain, fitted, objective = trial_domain, trial_fit, trial_objective
        if previous - objective <= tolerance:
            break
    return fitted


def fit_frechet_slots(
    left: Sequence[Trajectory],
    right: Sequence[Trajectory],
    slots: Sequence[tuple[int | None, int | None]],
    *,
    cutoff: float,
    cardinality_penalty: float,
) -> tuple[tuple[dict[int, Point], ...], float]:
    """Fit ordered active trajectories and return their mean squared OSPA cost.

    Each slot contains the indices of its assigned left and right trajectories.
    ``None`` denotes a virtual assignment. The supplied assignment saturates the
    smaller cardinality on each side, as in Nguyen et al. Definition 5. Slots
    require at least one real assignment. This fits the centers using Eq. 27 and
    scores the supplied assignment using Eq. 18, without searching assignments.
    The cost is an equal-source average in squared position units.
    """
    _validate_cutoff(cutoff)
    if (not isfinite(cardinality_penalty) or cardinality_penalty <= 0
            or not cardinality_penalty <= cutoff <= sqrt(2) * cardinality_penalty):
        raise ValueError("require 0 < cardinality_penalty <= cutoff <= sqrt(2) * cardinality_penalty")
    squared_cutoff = cutoff * cutoff
    if not isfinite(squared_cutoff) or squared_cutoff == 0:
        raise ValueError("squared cutoff must be finite and positive")

    count = len(slots)
    assigned = (set(), set())
    sizes = (len(left), len(right))
    for left_index, right_index in slots:
        if left_index is None and right_index is None:
            raise ValueError("an active slot needs a real assignment")
        for index, size, used in zip((left_index, right_index), sizes, assigned):
            if index is None:
                continue
            if isinstance(index, bool) or not isinstance(index, Integral) or not 0 <= index < size:
                raise ValueError("assignment index outside its source")
            if index in used:
                raise ValueError("a source trajectory cannot be assigned twice")
            used.add(index)
    if any(len(used) != min(count, size) for size, used in zip(sizes, assigned)):
        raise ValueError("assignment must saturate the smaller cardinality for each source")

    left_samples = tuple(_samples(trajectory) for trajectory in left)
    right_samples = tuple(_samples(trajectory) for trajectory in right)
    left_size, right_size = sizes
    left_denominator, right_denominator = max(count, left_size), max(count, right_size)
    centers = []
    left_losses = []
    right_losses = []
    for left_index, right_index in slots:
        if left_index is None:
            center = frechet_centroid(right_samples[right_index], cutoff=cutoff)
        elif right_index is None:
            center = frechet_centroid(left_samples[left_index], cutoff=cutoff)
        else:
            first, second = left_samples[left_index], right_samples[right_index]
            center = frechet_centroid(first, second, cutoff=cutoff,
                                      weights=(1 / left_denominator, 1 / right_denominator))
            left_losses.append(_normalized_trajectory_loss(center, first, cutoff))
            right_losses.append(_normalized_trajectory_loss(center, second, cutoff))
        centers.append(center)

    squared_penalty = cardinality_penalty * cardinality_penalty
    cost = fsum(
        (squared_cutoff * (fsum(losses) / denominator)
         + squared_penalty * (abs(count - size) / denominator)) / 2
        for size, denominator, losses in (
            (left_size, left_denominator, left_losses), (right_size, right_denominator, right_losses),
        )
        if denominator
    )
    return tuple(centers), cost
