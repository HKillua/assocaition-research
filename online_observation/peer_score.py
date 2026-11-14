"""Score frozen peer releases against independent MTAD labels and references."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping
from dataclasses import dataclass
from itertools import pairwise
import math

from .continuous_metrics import OPPORTUNITIES, evaluate_publications
from .continuous_tracker import FRESH_S, Plane
from .fusion_probe import _metrics, _reference_tracks, _truth_position
from .peer_prefix import Fragment, Point

DEADLINES = (20, 60, 120)
FIRST_DECISIONS = ("correct", "incorrect", "independent", "unpublished")


@dataclass
class _Birth:
    stamp: float
    opportunity: str
    sparse: bool
    decision: str = "unpublished"
    decision_stamp: float | None = None
    opportunity_at_decision: str | None = None
    confirmed_after: float | None = None


@dataclass(frozen=True, slots=True)
class _FrozenTrack:
    track_id: str
    members: tuple[Fragment, ...]
    observed_at: tuple[float, ...]
    position_m: Point | None


def score_peer_replay(events, publications, labels, *, stop, reference=None, include_birth_details=False):
    """Grade releases at their actual timestamps and on a common integer grid.

    Events are (native time, {fragment: lat/lon}) or (native time, fragments)
    when scoring membership alone. Releases are dictionaries with query_time
    and a list of tracks containing track_id and members. Optional observed_at
    member times must agree with the already arrived reports. Reference scoring
    uses metric position_m in the plane set by the first position batch. Birth
    details contain private fragment keys for same-scene arm comparisons.
    """
    events = tuple(events)
    if not math.isfinite(stop) or any(not math.isfinite(stamp) or stamp > stop for stamp, _ in events):
        raise ValueError("all native report times must lie within the finite common scoring horizon")
    if any(left[0] >= right[0] for left, right in pairwise(events)):
        raise ValueError("native report batches must be strictly ordered")
    if any(key not in labels for _, batch in events for key in batch):
        raise ValueError("unmapped measurement fragment in post-replay labels")

    start = math.floor(events[0][0]) if events else math.floor(stop)
    reference_score = None
    if reference is not None:
        if not events or not isinstance(events[0][1], Mapping) or not events[0][1]:
            raise ValueError("reference scoring requires a nonempty first position batch")
        reference_score = _PositionScore(reference, Plane.from_first_batch(events[0][1].values()), labels)
    frames, births, service = _grade_releases(events, publications, labels, stop, reference is not None)
    integer = evaluate_publications(events, _grid(events, frames, start, stop, reference_score), labels)
    sparse = sum(birth.sparse for birth in births.values())
    native = _birth_summary(births.values(), stop)
    native["by_opportunity_at_birth"] = {
        name: _birth_summary((birth for birth in births.values() if birth.opportunity == name), stop)
        for name in OPPORTUNITIES
    }
    native["sparse_births"] = _birth_summary((birth for birth in births.values() if birth.sparse), stop)
    result = dict(
        integer_grid=integer, native_births=native, false_chains=_false_chains(frames, labels, stop),
        population=dict(births=len(births), sparse_births=sparse,
                        is_sparse_scene=bool(births) and 2 * sparse >= len(births)),
        position=reference_score.result() if reference_score is not None else None,
        service_seconds=service,
    )
    if include_birth_details:
        result["birth_details"] = [
            dict(fragment=list(key), first_decision=birth.decision, birth_time=birth.stamp,
                 first_release_time=birth.decision_stamp, opportunity_at_birth=birth.opportunity,
                 opportunity_at_release=birth.opportunity_at_decision,
                 confirmed_after_seconds=birth.confirmed_after, sparse=birth.sparse)
            for key, birth in sorted(births.items())
        ]
    return result


def _opportunity(latest_by_source, source, stamp):
    other = [report for current, report in latest_by_source.items() if current != source]
    if any(stamp <= report + FRESH_S for report in other):
        return "fresh"
    return "stale" if other else "never_observed"


def _grade_releases(events, publications, labels, stop, keep_positions):
    frames = []
    births, latest = {}, {}
    by_target = defaultdict(dict)
    pending = set()
    event_index = 0
    previous = -math.inf
    service_times, ready_delays, queue_waits = [], [], []
    ready = -math.inf

    def advance(stamp):
        nonlocal event_index
        while event_index < len(events) and events[event_index][0] <= stamp:
            observed, batch = events[event_index]
            born = set(batch) - latest.keys()
            latest.update(dict.fromkeys(batch, observed))
            for key in batch:
                by_target[labels[key]][key[0]] = observed
            for key in born:
                source = key[0]
                peers = sum(other[0] != source and observed <= report + FRESH_S
                            for other, report in latest.items())
                births[key] = _Birth(observed, _opportunity(by_target[labels[key]], source, observed), peers <= 3)
            pending.update(born)
            event_index += 1

    for publication in publications:
        stamp = publication["query_time"]
        if not math.isfinite(stamp) or stamp <= previous:
            raise ValueError("frozen releases must have strictly increasing finite timestamps")
        if stamp > stop:
            break
        previous = stamp
        advance(stamp)
        tracks = _release_tracks(publication["tracks"], latest, stamp, keep_positions)
        frames.append((stamp, tracks))
        decisions = {}
        for track in tracks:
            members = track.members
            decision = "independent"
            if len(members) == 2:
                decision = "correct" if labels[members[0]] == labels[members[1]] else "incorrect"
            for key in members:
                decisions[key] = decision
                if decision == "correct" and births[key].confirmed_after is None:
                    births[key].confirmed_after = stamp - births[key].stamp
        for key in pending:
            birth = births[key]
            if stamp <= latest[key] + FRESH_S:
                birth.decision = decisions.get(key, "unpublished")
                birth.decision_stamp = stamp
                birth.opportunity_at_decision = _opportunity(by_target[labels[key]], key[0], stamp)
        pending.clear()

        service = publication.get("service_seconds")
        if service is not None:
            if not math.isfinite(service) or service < 0:
                raise ValueError("service time must be finite and nonnegative")
            wait = max(0.0, ready - stamp)
            total = wait + service
            ready = stamp + total
            service_times.append(service)
            queue_waits.append(wait)
            ready_delays.append(total)

    advance(stop)
    timing = None
    if service_times and len(service_times) == len(frames):
        timing = dict(service=_distribution(service_times), queue_wait=_distribution(queue_waits),
                      release_to_ready=_distribution(ready_delays))
    return frames, births, timing


def _release_tracks(tracks, latest, stamp, keep_positions):
    validated = []
    seen_ids, seen_members = set(), set()
    for track in tracks:
        track_id = track["track_id"]
        members = tuple(tuple(key) for key in track["members"])
        if not isinstance(track_id, str) or not track_id or track_id in seen_ids:
            raise ValueError("a release requires nonempty unique output IDs")
        if (not 1 <= len(members) <= 2 or any(len(key) != 2 or key not in latest for key in members)
                or len({key[0] for key in members}) != len(members) or seen_members.intersection(members)):
            raise ValueError("a release requires arrived fragment keys, used at most once, one per source")
        observed = tuple(latest[key] for key in members)
        if tuple(track.get("observed_at", observed)) != observed:
            raise ValueError("output report times must agree with the already arrived reports")
        if any(stamp > report + FRESH_S for report in observed):
            raise ValueError("a release includes a stale report")
        seen_ids.add(track_id)
        seen_members.update(members)
        point = track.get("position_m") if keep_positions else None
        validated.append(_FrozenTrack(track_id, members, observed, tuple(point) if point is not None else None))
    return tuple(validated)


def _birth_summary(births, stop):
    births = tuple(births)
    decisions = Counter(dict.fromkeys(FIRST_DECISIONS, 0))
    decisions.update(birth.decision for birth in births)
    delays = [birth.confirmed_after for birth in births if birth.confirmed_after is not None]
    by_wait = {}
    for deadline in DEADLINES:
        correct_by = sum(delay <= deadline for delay in delays)
        censored = sum(stop < birth.stamp + deadline and birth.confirmed_after is None for birth in births)
        by_wait[str(deadline)] = dict(confirmed=correct_by, censored=censored,
                                      unconfirmed=len(births) - correct_by - censored)
    return dict(
        births=len(births), first_decisions=dict(decisions),
        no_release_while_supported=sum(birth.decision_stamp is None for birth in births),
        first_wrong_without_true_peer_at_birth=sum(
            birth.decision == "incorrect" and birth.opportunity == "never_observed" for birth in births),
        first_wrong_without_true_peer_at_release=sum(
            birth.decision == "incorrect" and birth.opportunity_at_decision == "never_observed" for birth in births),
        ever_confirmed=len(delays), unconfirmed_by_end=len(births) - len(delays),
        confirmation_wait_seconds=_distribution(delays), confirmed_within_seconds=by_wait,
    )


def _distribution(values):
    values = sorted(values)
    if not values:
        return dict(n=0, p50=None, p95=None, p99=None, max=None)
    return dict(n=len(values), p50=values[math.ceil(.50 * len(values)) - 1],
                p95=values[math.ceil(.95 * len(values)) - 1],
                p99=values[math.ceil(.99 * len(values)) - 1], max=values[-1])


def _grid(events, frames, start, stop, position_score):
    index, event_index = 0, 0
    tracks = ()
    latest = {}
    for tick in range(start, math.floor(stop) + 1):
        while index < len(frames) and frames[index][0] <= tick:
            tracks = frames[index][1]
            index += 1
        visible = []
        for track in tracks:
            members = tuple(key for key, report in zip(track.members, track.observed_at)
                            if tick <= report + FRESH_S)
            if members:
                # A trimmed estimate can still depend on an expired member.
                point = track.position_m if len(members) == len(track.members) else None
                visible.append(dict(track_id=track.track_id, members=members, position_m=point))
        if position_score is not None:
            while event_index < len(events) and events[event_index][0] <= tick:
                stamp, batch = events[event_index]
                latest.update(dict.fromkeys(batch, stamp))
                event_index += 1
            latest = {key: stamp for key, stamp in latest.items() if tick <= stamp + FRESH_S}
            position_score.add(tick, latest, visible)
        yield dict(query_time=tick, tracks=visible)


def _false_chains(frames, labels, stop):
    active, closed = {}, []
    for index, (stamp, tracks) in enumerate(frames):
        next_time = frames[index + 1][0] if index + 1 < len(frames) else stop
        continued = {}
        for track in tracks:
            members = track.members
            if len(members) != 2 or labels[members[0]] == labels[members[1]]:
                continue
            edge = frozenset(members)
            expiry = min(track.observed_at) + FRESH_S
            if edge in active and active[edge][1] >= stamp:
                began = active.pop(edge)[0]
            else:
                began = stamp
            continued[edge] = began, min(next_time, expiry), expiry < next_time
        for began, ended, expired in active.values():
            closed.append((began, ended, "expiry" if expired else "selection_change"))
        active = continued
    for began, ended, expired in active.values():
        closed.append((began, ended, "expiry" if expired else "right_censored"))
    durations = [ended - began for began, ended, _ in closed]
    long = [ended - began for began, ended, _ in closed if ended > began + FRESH_S]
    return dict(chains=len(closed), pair_seconds=math.fsum(durations), duration_seconds=_distribution(durations),
                over_60_seconds=dict(chains=len(long), pair_seconds=math.fsum(long)),
                ends=dict(Counter(reason for _, _, reason in closed)))


class _PositionScore:
    def __init__(self, reference, plane, labels):
        self.tracks, self.audit = _reference_tracks(reference)
        self.max_gap = reference.max_gap_seconds
        self.plane = plane
        self.labels = labels
        self.support = Counter()
        self.errors = {"all": [], "fused": [], "single_source": []}

    def add(self, stamp, latest, outputs):
        targets = {self.labels[key] for key in latest}
        self.support["report_supported_target_seconds"] += len(targets)
        positions = defaultdict(list)
        for track in outputs:
            identities = {self.labels[key] for key in track["members"]}
            if len(identities) == 1:
                positions[next(iter(identities))].append(track)
        for target in targets:
            truth, unknown = _truth_position(self.tracks.get(target), stamp, self.max_gap)
            if unknown is not None:
                self.support[unknown] += 1
                continue
            self.support["reference_supported_target_seconds"] += 1
            estimates = positions[target]
            if len(estimates) != 1:
                continue
            track = estimates[0]
            width = len(track["members"])
            point = track.get("position_m")
            if point is None:
                continue
            if len(point) != 2 or not all(map(math.isfinite, point)):
                raise ValueError("published metric position must contain two finite coordinates")
            error = math.dist(point, self.plane.project(truth))
            self.errors["all"].append(error)
            self.errors["fused" if width == 2 else "single_source"].append(error)

    def result(self):
        return dict(support=dict(self.support), errors={name: _metrics(errors) for name, errors in self.errors.items()},
                    reference_audit=self.audit)
