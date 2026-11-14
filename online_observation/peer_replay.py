"""Supply the same native or fixed-boundary input to peer association arms."""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
from heapq import heappop, heappush
from itertools import chain
import math
from types import MappingProxyType

from .continuous_tracker import FRESH_S
from .peer_prefix import Fragment, LocalPrefix, Point, PrefixObservation

NativePositions = tuple[float, Mapping[Fragment, Point]]


@dataclass(frozen=True)
class ReplayFrame:
    """An immutable decision input and the report keys delivered since the last frame."""

    stamp: float
    observations: Mapping[Fragment, PrefixObservation]
    arrivals: tuple[tuple[float, tuple[Fragment, ...]], ...]


def replay_frames(
    events: Iterable[NativePositions], *, interval_seconds: float | None = None,
) -> Iterator[ReplayFrame]:
    """Replay strict position batches. Apply exact-time arrivals before publication.

    Native releases follow each report batch and the first instant past each
    still-current freshness deadline. Fixed releases occur at intervals from
    the first report, with one boundary strictly after the final report. Only
    the replay driver uses end of input. An empty input produces no frames.
    """
    if interval_seconds is not None and (
            not math.isfinite(interval_seconds) or interval_seconds <= 0):
        raise ValueError("publication interval must be positive and finite")
    prefix = LocalPrefix()
    events = iter(events)
    first = next(events, None)
    if first is None:
        return
    ordered = chain((first,), events)
    if interval_seconds is None:
        yield from _native_frames(prefix, ordered)
    else:
        yield from _fixed_frames(prefix, ordered, first[0], interval_seconds)


def _frame(prefix, stamp, arrivals=()):
    return ReplayFrame(stamp, MappingProxyType(prefix.snapshot(stamp)), tuple(arrivals))


def _fixed_frames(prefix, events, start, interval):
    index = 1
    boundary = start + interval
    if not math.isfinite(boundary) or boundary <= start:
        raise ValueError("first fixed boundary must be representable after the first report")
    arrivals = []
    for stamp, positions in events:
        if not math.isfinite(stamp):
            raise ValueError("native epochs must be finite")
        while boundary < stamp:
            yield _frame(prefix, boundary, arrivals)
            arrivals = []
            index += 1
            boundary = _next_boundary(start, index, interval, boundary)
        prefix.ingest(stamp, positions)
        arrivals.append((stamp, tuple(positions)))
        if boundary == stamp:
            yield _frame(prefix, boundary, arrivals)
            arrivals = []
            index += 1
            boundary = _next_boundary(start, index, interval, boundary)
    yield _frame(prefix, boundary, arrivals)


def _next_boundary(start, index, interval, previous):
    boundary = start + index * interval
    if not math.isfinite(boundary) or boundary <= previous:
        raise ValueError("fixed boundaries must be finite and strictly increasing")
    return boundary


def _native_frames(prefix, events):
    deadlines = []
    active = {}

    def remove_expiring(stamp):
        removed = False
        while deadlines and deadlines[0][0] == stamp:
            deadline, key = heappop(deadlines)
            if active.get(key) == deadline:
                del active[key]
                removed = True
        return removed

    for stamp, positions in events:
        while deadlines and deadlines[0][0] < stamp:
            deadline = deadlines[0][0]
            if remove_expiring(deadline):
                yield _frame(prefix, deadline)
        prefix.ingest(stamp, positions)
        deadline = math.nextafter(stamp + FRESH_S, math.inf)
        for key in positions:
            active[key] = deadline
            heappush(deadlines, (deadline, key))
        remove_expiring(stamp)
        yield _frame(prefix, stamp, ((stamp, tuple(positions)),))

    while deadlines:
        deadline = deadlines[0][0]
        if remove_expiring(deadline):
            yield _frame(prefix, deadline)
