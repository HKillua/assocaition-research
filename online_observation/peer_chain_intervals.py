"""Reconstruct false-edge intervals from immutable peer publications."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
import math

from .continuous_tracker import FRESH_S
from .peer_prefix import Fragment

Edge = tuple[Fragment, Fragment]


@dataclass(frozen=True)
class FrozenFrame:
    stamp: float
    reports: dict[Fragment, float]
    partners: dict[Fragment, Fragment]


@dataclass(frozen=True)
class Chain:
    edge: Edge
    start: float
    end: float
    reason: str


def frozen_frames(publications: Iterable[dict]) -> list[FrozenFrame]:
    """Validate a strictly ordered stream of already published frames."""
    frames = []
    last_seen = {}
    previous = -math.inf
    for publication in publications:
        stamp = publication["query_time"]
        if not math.isfinite(stamp) or stamp <= previous:
            raise ValueError("frozen publication times must be finite and strictly increasing")
        reports, partners, ids = {}, {}, set()
        for track in publication["tracks"]:
            identifier = track["track_id"]
            if not isinstance(identifier, str) or not identifier or identifier in ids:
                raise ValueError("a frozen frame requires unique nonempty track IDs")
            ids.add(identifier)
            members = tuple(tuple(key) for key in track["members"])
            observed_at = track["observed_at"]
            if (not 1 <= len(members) <= 2 or len(observed_at) != len(members)
                    or any(len(key) != 2 or not all(isinstance(part, str) and part for part in key) for key in members)
                    or len({key[0] for key in members}) != len(members)
                    or any(key in reports for key in members)):
                raise ValueError("a frozen fragment must appear once, with one report time, in a group of distinct sources")
            for key, observed in zip(members, observed_at):
                if (not math.isfinite(observed) or observed > stamp or observed + FRESH_S < stamp
                        or observed < last_seen.get(key, -math.inf)):
                    raise ValueError("observed times must be fresh, arrived and nondecreasing per fragment")
                reports[key] = last_seen[key] = observed
            if len(members) == 2:
                left, right = members
                partners[left], partners[right] = right, left
        frames.append(FrozenFrame(stamp, reports, partners))
        previous = stamp
    return frames


def false_chains(frames: Sequence[FrozenFrame], labels: Mapping[Fragment, str], stop: float) -> list[Chain]:
    """Use the original score's interval, expiry, and end-censoring semantics."""
    if not math.isfinite(stop) or (frames and frames[-1].stamp > stop):
        raise ValueError("the finite common horizon must cover the final frame")
    active, closed = {}, []
    for index, frame in enumerate(frames):
        next_stamp = frames[index + 1].stamp if index + 1 < len(frames) else stop
        continuing = {}
        for left, right in frame.partners.items():
            if left >= right or labels[left] == labels[right]:
                continue
            edge = left, right
            expiry = min(frame.reports[left], frame.reports[right]) + FRESH_S
            if edge in active and active[edge].end >= frame.stamp:
                start = active.pop(edge).start
            else:
                start = frame.stamp
            reason = "expiry" if expiry < next_stamp else "selection_change"
            continuing[edge] = Chain(edge, start, min(next_stamp, expiry), reason)
        closed.extend(active.values())
        active = continuing
    for chain in active.values():
        reason = "expiry" if chain.reason == "expiry" else "right_censored"
        closed.append(Chain(chain.edge, chain.start, chain.end, reason))
    return closed


def endpoint_status(
    frame: FrozenFrame, key: Fragment, old_peer: Fragment, labels: Mapping[Fragment, str], stamp: float,
) -> str:
    """Classify the positive-duration interval starting at ``stamp``.

    The instant at the expiry boundary itself has no duration. A report with
    exactly that boundary is thus expired for this interval, even if it was
    still fresh at the exact release instant.
    """
    if key not in frame.reports or stamp >= frame.reports[key] + FRESH_S:
        return "expired"
    peer = frame.partners.get(key)
    if peer is None:
        return "singleton"
    if stamp >= frame.reports[peer] + FRESH_S:
        return "partner_expired"
    if peer == old_peer:
        return "same_false"
    return "other_true" if labels[key] == labels[peer] else "other_false"


def frame_cuts(first: FrozenFrame, second: FrozenFrame, end: float) -> list[float]:
    """Include the common frame start, intermediate expiries, and interval end."""
    start = first.stamp
    if second.stamp != start or end < start or not math.isfinite(end):
        raise ValueError("frame cuts require matched clocks and a finite interval end")
    return sorted({start, end} | {
        timestamp + FRESH_S for frame in (first, second) for timestamp in frame.reports.values()
        if start < timestamp + FRESH_S < end
    })
