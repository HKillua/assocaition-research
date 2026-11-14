"""Lindenmaier et al. (2025) on causal, two-source MTAD replay frames."""

from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from itertools import groupby, product
import math

from .continuous_tracker import ACCELERATION_SPECTRAL_DENSITY, FRESH_S, MEMORY_S, RADIUS_M, VELOCITY_VARIANCE
from .lindenmaier_association import (
    DiagonalState, ExistenceMass, SensorModel, _difference_variances, _fuse_with_variances,
    _log_likelihood_ratio, _log_prior, _squared_distance, update_existence,
)
from .peer_identity import CandidateGroup, IdentifiedGroup, IdentityReader
from .peer_prefix import Fragment, Point
from .peer_replay import ReplayFrame


# Fixed development proxies rather than estimates of MTAD sensor performance.
_POSITION_RADIUS = RADIUS_M
_VELOCITY_HALF_WIDTH = 3 * math.sqrt(VELOCITY_VARIANCE)
_STATE_VOLUME = (2 * _POSITION_RADIUS)**2 * (2 * _VELOCITY_HALF_WIDTH)**2
_TRACKING_PROBABILITY = 0.9
_LOCAL_EXISTENCE_PROBABILITY = 0.95
_TRUST = 0.9
_CONFIRMATION_PROBABILITY = 0.9
_CORRELATION = 0.4
_DISTANCE_GATE = 25.0
_PRIOR_GATE = _POSITION_RADIUS
_HALF_LIFE = float(FRESH_S)
_BIRTH_RATE = 1.0
_CLUTTER_RATE = 1.0

PROXY_SETTINGS = {
    "position_gate_m": _POSITION_RADIUS,
    "velocity_volume_half_width_mps": _VELOCITY_HALF_WIDTH,
    "state_volume_m2_mps2": _STATE_VOLUME,
    "source_parameters_symmetric": True,
    "birth_rate_per_state_volume": _BIRTH_RATE,
    "clutter_rate_per_state_volume": _CLUTTER_RATE,
    "tracking_probability": _TRACKING_PROBABILITY,
    "local_existence_probability": _LOCAL_EXISTENCE_PROBABILITY,
    "source_trust": _TRUST,
    "internal_confirmation_strictly_above": _CONFIRMATION_PROBABILITY,
    "correlation": _CORRELATION,
    "mahalanobis_squared_gate": _DISTANCE_GATE,
    "prior_l2_gate_m_mps_coordinates": _PRIOR_GATE,
    "discount_half_life_s": _HALF_LIFE,
    "prior_memory_s": MEMORY_S,
}
_SENSOR = SensorModel(_STATE_VOLUME, _TRACKING_PROBABILITY,
                      _BIRTH_RATE / _STATE_VOLUME, _CLUTTER_RATE / _STATE_VOLUME)
_LOCAL_MASS = ExistenceMass.from_local(existence_probability=_LOCAL_EXISTENCE_PROBABILITY,
                                       tracking_probability=_TRACKING_PROBABILITY, trust=_TRUST)
_DIFFUSE_LOG_PRIOR = -math.log(_STATE_VOLUME)


@dataclass(frozen=True)
class TrackExistence:
    probability: float
    confirmed: bool


@dataclass(frozen=True)
class _GlobalTrack:
    state: DiagonalState
    state_time: float
    candidate: CandidateGroup
    mass: ExistenceMass
    mass_time: float
    confirmed: bool


class LindenmaierArm:
    """Compare diffuse and previous-confirmed-track priors on the same graph."""

    def __init__(self, *, feedback: bool) -> None:
        self.feedback = feedback
        self.diagnostics: Counter = Counter()
        self.existence_by_id: dict[str, TrackExistence] = {}
        self._identity = IdentityReader()
        self._global: dict[str, _GlobalTrack] = {}
        self._clock = -math.inf
        self._sources: set[str] = set()

    def publish(self, frame: ReplayFrame) -> tuple[IdentifiedGroup, ...]:
        """Use previous global tracks for association, then absorb current evidence."""
        stamp = frame.stamp
        if not math.isfinite(stamp) or stamp <= self._clock:
            raise ValueError("Lindenmaier frames must be finite and strictly increasing")
        sources = self._sources | {key[0] for key in frame.observations}
        if len(sources) > 2:
            raise ValueError("the MTAD adaptation accepts at most two sources")

        priors = self._previous_priors(stamp)
        states = _group_states(frame, priors, self.diagnostics)
        candidates = [CandidateGroup(members, _position(state), tuple(
            frame.observations[key].observed_at for key in members)) for members, state in states.items()]
        published = self._identity.publish(stamp, candidates)

        # At a fixed boundary, attribute just this interval's reports to the
        # members selected at that boundary and accumulate on the native clock.
        arrivals = defaultdict(list)
        current = frame.observations
        for arrival, keys in frame.arrivals:
            for key in keys:
                if key in current:
                    arrivals[key].append(arrival)
        surviving = self._identity.remembered_ids
        next_global = {track_id: prior for track_id, prior in self._global.items() if track_id in surviving}
        confirmed = {}
        for output in published:
            track_id, candidate = output.track_id, output.candidate
            prior = self._global.get(track_id)
            record, count = _observe(prior, states[candidate.members], candidate, stamp, arrivals)
            next_global[track_id] = record
            confirmed[track_id] = TrackExistence(record.mass.probability, record.confirmed)
            self.diagnostics["existence_report_updates"] += count
            self.diagnostics["published_confirmed_tracks"] += record.confirmed
            self.diagnostics["published_singletons"] += len(candidate.members) == 1
            self.diagnostics["published_pairs"] += len(candidate.members) == 2
        self._global = next_global
        self.existence_by_id = confirmed
        self._clock = stamp
        self._sources = sources
        self.diagnostics["frames"] += 1
        self.diagnostics["no_arrival_frames"] += not frame.arrivals
        return published

    def _previous_priors(self, stamp: float):
        if not self.feedback:
            return {}
        predicted = []
        for track in self._global.values():
            last_report = max(track.candidate.observed_at)
            if track.confirmed and stamp <= last_report + MEMORY_S:
                state = _predict(track.state, stamp - track.state_time)
                predicted.append((_position(state), state))
                self.diagnostics["eligible_confirmed_prior_tracks"] += 1
                self.diagnostics["eligible_dormant_prior_tracks"] += stamp > last_report + FRESH_S
        return _spatial_index(predicted)


def _position(state: DiagonalState) -> Point:
    return state.mean[0], state.mean[2]


def _predict(state: DiagonalState, seconds: float) -> DiagonalState:
    east, ve, north, vn = state.mean
    pe, pve, pn, pvn = state.variances
    q = ACCELERATION_SPECTRAL_DENSITY
    position_noise = q * seconds**3 / 3
    velocity_noise = q * seconds
    # The previous fused meta-state represents diagonal marginals as in Eq. 52.
    return DiagonalState((east + seconds * ve, ve, north + seconds * vn, vn), (
        pe + seconds**2 * pve + position_noise, pve + velocity_noise,
        pn + seconds**2 * pvn + position_noise, pvn + velocity_noise,
    ))


def _observe(prior, state, candidate, stamp, arrivals):
    reports = sorted(at for key in candidate.members for at in set(arrivals.get(key, ())))
    mass = ExistenceMass() if prior is None else prior.mass
    previous = (reports[0] if reports else stamp) if prior is None else prior.mass_time
    confirmed = prior is not None and prior.confirmed
    for at, batch in groupby(reports):
        mass = update_existence(mass, (_LOCAL_MASS for _ in batch), gamma=_discount(at - previous))
        confirmed |= mass.probability > _CONFIRMATION_PROBABILITY
        previous = at
    if previous < stamp:
        mass = update_existence(mass, (), gamma=_discount(stamp - previous))
    # Repeated publication after an unrelated report must not re-anchor the
    # global state or return historical local evidence to the mass update.
    if prior is not None and not reports and prior.candidate.members == candidate.members:
        state, state_time = prior.state, prior.state_time
    else:
        state_time = stamp
    return _GlobalTrack(state, state_time, candidate, mass, stamp, confirmed), len(reports)


def _discount(seconds):
    return 2 ** (-seconds / _HALF_LIFE)


def _spatial_index(positioned):
    index = defaultdict(list)
    for point, value in positioned:
        index[_cell(point)].append(value)
    return index


def _cell(point):
    return tuple(math.floor(value / _POSITION_RADIUS) for value in point)


def _neighbors(index, point):
    x, y = _cell(point)
    for dx, dy in product((-1, 0, 1), repeat=2):
        yield from index.get((x + dx, y + dy), ())


def _prior(state, priors):
    # A prior eligible under Eq. 32 has a position in the surrounding cells.
    if not priors:
        return _DIFFUSE_LOG_PRIOR
    return _log_prior(state, _neighbors(priors, _position(state)), _STATE_VOLUME, _PRIOR_GATE)


def _group_states(frame, priors, tally):
    observations = frame.observations
    by_source = defaultdict(list)
    for key in observations:
        by_source[key[0]].append(key)
    singleton_states = {(key,): reading.state for key, reading in observations.items()}
    if len(by_source) < 2:
        return singleton_states
    left, right = by_source.values()
    right_index = _spatial_index((_position(observations[key].state), key) for key in right)
    local_priors = {}
    positive = []
    tally["cross_source_pairs"] += len(left) * len(right)
    admitted = 0
    for a in left:
        first = observations[a].state
        for b in _neighbors(right_index, _position(first)):
            second = observations[b].state
            if math.dist(_position(first), _position(second)) > _POSITION_RADIUS:
                continue
            admitted += 1
            variances = _difference_variances(first, second, _CORRELATION)
            distance = _squared_distance(first.mean, second.mean, variances)
            if distance >= _DISTANCE_GATE:
                tally["outside_mahalanobis_gate"] += 1
                continue
            tally["scored_pairs"] += 1
            for key, state in ((a, first), (b, second)):
                if key not in local_priors:
                    local_priors[key] = _prior(state, priors)
            # Symmetric source proxies permit ordering the arithmetic by state
            # rather than fragment identifiers before computing the fused mean.
            if (first.mean, first.variances) <= (second.mean, second.variances):
                fused = _fuse_with_variances(first, second, _CORRELATION, variances)
                left_prior, right_prior = local_priors[a], local_priors[b]
            else:
                fused = _fuse_with_variances(second, first, _CORRELATION, variances)
                left_prior, right_prior = local_priors[b], local_priors[a]
            fused_prior = _prior(fused, priors)
            margin = _log_likelihood_ratio(distance, variances, fused_prior, left_prior, right_prior,
                                           _SENSOR, _SENSOR)
            tally["scored_pairs_with_informative_prior"] += max(
                left_prior, right_prior, fused_prior) > _DIFFUSE_LOG_PRIOR
            if margin > 0:
                positive.append((margin, a, b, fused))
            elif margin < 0:
                tally["negative_margin_pairs"] += 1
            else:
                tally["zero_margin_pairs"] += 1
    tally["outside_position_gate"] += len(left) * len(right) - admitted
    tally["positive_margin_pairs"] += len(positive)
    selected = _greedy_pairs(positive, tally)
    for pair, state in selected:
        for member in pair:
            del singleton_states[(member,)]
        singleton_states[pair] = state
    return singleton_states


def _greedy_pairs(positive, tally):
    blocked: set[Fragment] = set()
    for _, batch in groupby(sorted(positive, key=lambda edge: -edge[0]), key=lambda edge: edge[0]):
        eligible = []
        degree = Counter()
        for _, first, second, state in batch:
            if first in blocked or second in blocked:
                tally["positive_pairs_lost_to_competition"] += 1
            else:
                degree.update((first, second))
                eligible.append((first, second, state))
        blocked.update(degree)
        for first, second, state in eligible:
            if degree[first] == 1 and degree[second] == 1:
                yield tuple(sorted((first, second))), state
            else:
                tally["positive_pairs_abstained_on_exact_tie"] += 1
