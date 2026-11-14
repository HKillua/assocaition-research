"""Order-two Euclidean trajectory consensus from Nguyen et al., arXiv:2504.20391v3."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from math import dist, fsum, gcd, isfinite, sqrt
from numbers import Integral
from random import Random

from .continuous_assignment import solve_global

Point = tuple[float, float]
Trajectory = Mapping[int, Point]
Slot = tuple[int | None, int | None]


@dataclass(frozen=True)
class FrechetSetFit:
    slots: tuple[Slot, ...]
    centers: tuple[dict[int, Point], ...]
    objective: float


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


def _validate_set_cost(cutoff: float, cardinality_penalty: float) -> None:
    _validate_cutoff(cutoff)
    if (not isfinite(cardinality_penalty) or cardinality_penalty <= 0
            or not cardinality_penalty <= cutoff <= sqrt(2) * cardinality_penalty):
        raise ValueError("require 0 < cardinality_penalty <= cutoff <= sqrt(2) * cardinality_penalty")
    squared_cutoff = cutoff * cutoff
    if not isfinite(squared_cutoff) or squared_cutoff == 0:
        raise ValueError("squared cutoff must be finite and positive")


def _validate_slots(slots: Sequence[Slot], sizes: tuple[int, int]) -> None:
    assigned = (set(), set())
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
    if any(len(used) != min(len(slots), size) for size, used in zip(sizes, assigned)):
        raise ValueError("assignment must saturate the smaller cardinality for each source")


def fit_frechet_slots(
    left: Sequence[Trajectory],
    right: Sequence[Trajectory],
    slots: Sequence[Slot],
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
    fit = _SlotObjective(left, right, cutoff, cardinality_penalty, False)
    _validate_slots(slots, fit.sizes)
    result = fit.evaluate(tuple(slots))
    return result.centers, result.objective


class _SlotObjective:
    def __init__(self, left, right, cutoff, cardinality_penalty, unknown_mask):
        _validate_set_cost(cutoff, cardinality_penalty)
        self.left = tuple(dict(sorted(_samples(sample).items())) for sample in left)
        self.right = tuple(dict(sorted(_samples(sample).items())) for sample in right)
        self.sizes = (len(self.left), len(self.right))
        self.cutoff = cutoff
        self.squared_cutoff = cutoff * cutoff
        self.squared_penalty = cardinality_penalty * cardinality_penalty
        self.unknown_mask = unknown_mask
        self._pair_fits = {}
        self._cross_losses = {}

    def loss(self, first: Trajectory, second: Trajectory) -> float:
        if not self.unknown_mask:
            return _normalized_trajectory_loss(first, second, self.cutoff)
        shared = first.keys() & second.keys()
        if not shared:
            return 1.0
        return fsum(_normalized_point_loss(first[knot], second[knot], self.cutoff)
                    for knot in shared) / len(shared)

    def pair_supported(self, first: Trajectory, second: Trajectory) -> bool:
        return not self.unknown_mask or not first.keys().isdisjoint(second.keys())

    def cross_loss(self, left: int, right: int) -> float:
        key = (left, right)
        if key not in self._cross_losses:
            self._cross_losses[key] = self.loss(self.left[left], self.right[right])
        return self._cross_losses[key]

    def center_loss(self, slot: Slot, center: Trajectory, side: int, index: int) -> float:
        left, right = slot
        if slot[side] == index and None in slot:
            return 0.0
        if right is None:
            if side == 1:
                return self.cross_loss(left, index)
        elif left is None and side == 0:
            return self.cross_loss(index, right)
        source = self.left if side == 0 else self.right
        return self.loss(center, source[index])

    def pair_fit(self, left_index, right_index, left_denominator, right_denominator):
        divisor = gcd(left_denominator, right_denominator)
        key = (left_index, right_index, left_denominator // divisor, right_denominator // divisor)
        if key not in self._pair_fits:
            first, second = self.left[left_index], self.right[right_index]
            weights = (1 / key[2], 1 / key[3])
            if self.unknown_mask:
                center = first | second
                shared = first.keys() & second.keys()
                for knot in shared:
                    center[knot] = _common_position(first[knot], second[knot], *weights, self.cutoff)
                common_center = {knot: center[knot] for knot in shared}
                left_loss, right_loss = self.loss(common_center, first), self.loss(common_center, second)
                center = dict(sorted(center.items()))
            else:
                center = frechet_centroid(first, second, cutoff=self.cutoff, weights=weights)
                left_loss, right_loss = self.loss(center, first), self.loss(center, second)
            self._pair_fits[key] = (center, left_loss, right_loss)
        return self._pair_fits[key]

    def evaluate(self, slots: tuple[Slot, ...]) -> FrechetSetFit:
        count = len(slots)
        left_size, right_size = self.sizes
        left_denominator, right_denominator = max(count, left_size), max(count, right_size)
        centers = []
        left_losses, right_losses = [], []
        for left_index, right_index in slots:
            if left_index is None:
                center = self.right[right_index]
            elif right_index is None:
                center = self.left[left_index]
            else:
                center, left_loss, right_loss = self.pair_fit(
                    left_index, right_index, left_denominator, right_denominator,
                )
                left_losses.append(left_loss)
                right_losses.append(right_loss)
            centers.append(center)
        cost = fsum(
            (self.squared_cutoff * (fsum(losses) / denominator)
             + self.squared_penalty * (abs(count - size) / denominator)) / 2
            for size, denominator, losses in (
                (left_size, left_denominator, left_losses), (right_size, right_denominator, right_losses),
            )
            if denominator
        )
        return FrechetSetFit(slots, tuple(centers), cost)


def _unassigned(slots: Sequence[Slot], sizes: tuple[int, int]) -> tuple[list[int], list[int]]:
    left_used = {left for left, _ in slots}
    right_used = {right for _, right in slots}
    return ([index for index in range(sizes[0]) if index not in left_used],
            [index for index in range(sizes[1]) if index not in right_used])


def _complete_slots(
    fit: _SlotObjective, slots: Sequence[Slot], unused: tuple[list[int], list[int]],
) -> tuple[Slot, ...] | None:
    """Repair a deletion that leaves fewer than min(m, n) real assignments."""
    left_unused, right_unused = unused
    left_required = min(len(slots), fit.sizes[0]) - (fit.sizes[0] - len(left_unused))
    right_required = min(len(slots), fit.sizes[1]) - (fit.sizes[1] - len(right_unused))
    if not left_required and not right_required:
        return tuple(slots)

    completed = list(slots)
    for side, required, unused in ((0, left_required, left_unused), (1, right_required, right_unused)):
        for _ in range(required):
            if side == 0:
                candidates = ((fit.cross_loss(index, right), slot, index)
                              for slot, (left, right) in enumerate(completed) if left is None
                              for index in unused if fit.pair_supported(fit.left[index], fit.right[right]))
            else:
                candidates = ((fit.cross_loss(left, index), slot, index)
                              for slot, (left, right) in enumerate(completed) if right is None
                              for index in unused if fit.pair_supported(fit.left[left], fit.right[index]))
            best = min(candidates, default=None)
            if best is None:
                return None
            _, slot, index = best
            left, right = completed[slot]
            completed[slot] = (index, right) if side == 0 else (left, index)
            unused.remove(index)
    return tuple(completed)


def _add_slots(fit: _SlotObjective, current: FrechetSetFit, random: Random) -> FrechetSetFit:
    """Probe unassigned and capped inputs as in Algorithm 4."""
    left_unused, right_unused = _unassigned(current.slots, fit.sizes)
    left_donors = left_unused + [left for (left, _), center in zip(current.slots, current.centers)
                                 if left is not None and fit.loss(center, fit.left[left]) == 1.0]
    right_donors = right_unused + [right for (_, right), center in zip(current.slots, current.centers)
                                   if right is not None and fit.loss(center, fit.right[right]) == 1.0]
    donors = [(0, index) for index in left_donors] + [(1, index) for index in right_donors]
    random.shuffle(donors)

    for side, index in donors:
        left_unused, right_unused = _unassigned(current.slots, fit.sizes)
        own_unused, other_unused = (left_unused, right_unused) if side == 0 else (right_unused, left_unused)
        if index not in own_unused:
            continue
        costs = [(fit.cross_loss(index, candidate) if side == 0 else fit.cross_loss(candidate, index), candidate)
                 for candidate in other_unused]
        distance, partner = min(costs, default=(1.0, None))
        if distance == 1.0 or sum(cost == distance for cost, _ in costs) != 1:
            partner = None
        if other_unused and partner is None:
            continue
        slot = (index, partner) if side == 0 else (partner, index)
        trial = fit.evaluate((*current.slots, slot))
        if trial.objective < current.objective:
            current = trial

    # A capped seed can be detached as a singleton once its source is over
    # represented in the slot count. Restrict to supported residual slots.
    for side, index in donors:
        if len(current.slots) < fit.sizes[side]:
            continue
        donor = next((position for position, slot in enumerate(current.slots)
                      if slot[side] == index and None not in slot), None)
        if donor is None:
            continue
        source = fit.left if side == 0 else fit.right
        if fit.loss(current.centers[donor], source[index]) != 1.0:
            continue
        slots = list(current.slots)
        left, right = slots[donor]
        slots[donor] = (None, right) if side == 0 else (left, None)
        slots.append((left, None) if side == 0 else (None, right))
        completed = _complete_slots(fit, slots, _unassigned(slots, fit.sizes))
        if completed is not None:
            trial = fit.evaluate(completed)
            if trial.objective < current.objective:
                current = trial
    return current


def _delete_slots(fit: _SlotObjective, current: FrechetSetFit) -> FrechetSetFit:
    """Probe inactivation in slot order, accepting strict decreases (Alg. 5)."""
    unused = _unassigned(current.slots, fit.sizes)
    index = 0
    while index < len(current.slots):
        slot = current.slots[index]
        retained = current.slots[:index] + current.slots[index + 1:]
        freed = tuple(pool + ([track] if track is not None else []) for pool, track in zip(unused, slot))
        completed = _complete_slots(fit, retained, freed)
        if completed is not None:
            trial = fit.evaluate(completed)
            if trial.objective < current.objective:
                current = trial
                unused = _unassigned(current.slots, fit.sizes)
                continue
        index += 1
    return current


def _reassign_slots(fit: _SlotObjective, current: FrechetSetFit) -> FrechetSetFit:
    """Run Eq. 18's squared-distance assignments with fixed centers (Alg. 3)."""
    if not current.slots:
        return current
    selected = []
    for side, source in enumerate((fit.left, fit.right)):
        if not source:
            selected.append({})
            continue
        costs = [[fit.center_loss(slot, center, side, index) for index in range(len(source))]
                 for slot, center in zip(current.slots, current.centers)]
        # Positive savings match exactly the edges that improve on the cutoff.
        # Exclude equal-to-cutoff edges before constructing dense components.
        costs = [[cost if cost < 1.0 else None for cost in row] for row in costs]
        solved = solve_global(costs, [0.5] * len(current.slots), [0.5] * len(source))
        assigned = dict(solved.pairs)
        used = set(assigned.values())
        for slot, original in enumerate(current.slots):
            index = original[side]
            if slot not in assigned and index is not None and index not in used:
                assigned[slot] = index
                used.add(index)
        if len(assigned) < min(len(current.slots), len(source)):
            return current
        selected.append(assigned)
    slots = tuple((selected[0].get(slot), selected[1].get(slot)) for slot in range(len(current.slots)))
    for left, right in slots:
        if left is None and right is None:
            return current
        if left is not None and right is not None and not fit.pair_supported(fit.left[left], fit.right[right]):
            return current
    trial = fit.evaluate(slots)
    return trial if trial.objective < current.objective else current


def _merge_singletons(fit: _SlotObjective, current: FrechetSetFit) -> FrechetSetFit:
    """Propose source-preserving merges from singleton tracks with unique partners."""
    left_only = [left for left, right in current.slots if right is None]
    right_only = [right for left, right in current.slots if left is None]
    if not left_only or not right_only:
        return current
    costs = [[fit.cross_loss(left, right) for right in right_only] for left in left_only]
    costs = [[cost if cost < 1.0 else None for cost in row] for row in costs]
    assignment = solve_global(costs, [0.5] * len(left_only), [0.5] * len(right_only))
    for left_row, right_column in assignment.pairs:
        left, right = left_only[left_row], right_only[right_column]
        retained = tuple(slot for slot in current.slots if slot not in {(left, None), (None, right)})
        trial = fit.evaluate((*retained, (left, right)))
        if trial.objective < current.objective:
            current = trial
    return current


def search_frechet_slots(
    left: Sequence[Trajectory],
    right: Sequence[Trajectory],
    *,
    cutoff: float,
    cardinality_penalty: float,
    seed: int = 20,
    max_sweeps: int = 2,
    unknown_mask: bool = False,
) -> FrechetSetFit:
    """Bounded two-source greedy search over feasible active slots (Alg. 2–5).

    Start from empty and all-singleton sets. The latter is a publication
    adaptation that can escape a strict empty-start tie at the metric boundary.
    Each sweep tries additions, feasible deletions and fixed-center reassignment.
    The singleton start also proposes merges with unique geometric support.
    Strict objective comparisons retain the incumbent on ties, and tied or
    capped reassignments fall back to incumbent slots. This approximates the
    paper's random inactive-slot permutation and can stop at a local optimum.

    In the explicit unknown-mask ablation, one-sided knots remain available in
    centers and only shared knots contribute position costs. A pair with no
    shared knots is forbidden. These scores change Eq. 2's metric.
    """
    if isinstance(max_sweeps, bool) or not isinstance(max_sweeps, Integral) or max_sweeps < 1:
        raise ValueError("max_sweeps must be a positive integer")
    fit = _SlotObjective(left, right, cutoff, cardinality_penalty, unknown_mask)
    singletons = fit.evaluate(tuple((index, None) for index in range(len(left)))
                              + tuple((None, index) for index in range(len(right))))
    if not left or not right:
        return singletons

    best = singletons
    random = Random(seed)
    for initial in (singletons, fit.evaluate(())):
        current = initial
        for _ in range(max_sweeps):
            previous = current.objective
            current = _merge_singletons(fit, current)
            current = _add_slots(fit, current, random)
            current = _delete_slots(fit, current)
            current = _reassign_slots(fit, current)
            if current.objective >= previous:
                break
        if current.objective < best.objective:
            best = current
    return best
