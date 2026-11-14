"""Read persistent publication IDs from completed peer association groups."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from dataclasses import dataclass
import math

from .continuous_assignment import solve_global
from .continuous_tracker import FRESH_S, MEMORY_S, RADIUS_M
from .peer_prefix import Fragment, Point


@dataclass(frozen=True)
class CandidateGroup:
    """One current estimate, with each member's latest report time in the same order."""

    members: tuple[Fragment, ...]
    position: Point
    observed_at: tuple[float, ...]

    def __post_init__(self) -> None:
        members = tuple(tuple(member) for member in self.members)
        if (not 1 <= len(members) <= 2 or len(self.observed_at) != len(members)
                or any(len(member) != 2 or not all(isinstance(part, str) and part for part in member)
                       for member in members)
                or len({member[0] for member in members}) != len(members)):
            raise ValueError("groups need one or two distinct sources and a report time per member")
        position = tuple(self.position)
        if len(position) != 2 or not all(map(math.isfinite, (*position, *self.observed_at))):
            raise ValueError("positions and report times must be finite")
        canonical = sorted(zip(members, self.observed_at))
        object.__setattr__(self, "members", tuple(member for member, _ in canonical))
        object.__setattr__(self, "observed_at", tuple(stamp for _, stamp in canonical))
        object.__setattr__(self, "position", position)


@dataclass(frozen=True)
class IdentifiedGroup:
    track_id: str
    candidate: CandidateGroup


class IdentityReader:
    """Assign one persistent ID per group without changing the current membership."""

    def __init__(self, *, radius_m: float = RADIUS_M) -> None:
        if not math.isfinite(radius_m * radius_m) or radius_m <= 0:
            raise ValueError("identity radius must be positive and finite")
        self._radius_m = radius_m
        self._clock = -math.inf
        self._last_id = 0
        self._memory: dict[str, CandidateGroup] = {}

    @property
    def remembered_ids(self) -> frozenset[str]:
        """IDs retained by the last publication, including dormant tracks."""
        return frozenset(self._memory)

    def publish(self, stamp: float, groups: Iterable[CandidateGroup]) -> tuple[IdentifiedGroup, ...]:
        """Publish one new frame in time order, including empty frames after expiry."""
        if not math.isfinite(stamp) or stamp <= self._clock:
            raise ValueError("publish times must be finite and strictly increasing")
        groups = tuple(sorted(groups, key=lambda group: group.members))
        seen = set()
        for group in groups:
            if seen.intersection(group.members):
                raise ValueError("a fragment may be published in only one group per frame")
            if any(report > stamp or stamp > report + FRESH_S for report in group.observed_at):
                raise ValueError("published members must have fresh, already arrived reports")
            seen.update(group.members)

        memory = {track_id: group for track_id, group in self._memory.items()
                  if stamp <= max(group.observed_at) + MEMORY_S}
        links, claims = _member_continuity(groups, memory)
        pending = [index for index in range(len(groups)) if index not in links]
        reserved = set(links.values())
        available = [track_id for track_id in memory if track_id not in reserved]
        if pending and available:
            costs = [
                [_geometry_cost(groups[index], memory[track_id], stamp, self._radius_m)
                 if track_id not in claims or index in claims[track_id] else None
                 for track_id in available]
                for index in pending
            ]
            null = self._radius_m**2 / 2
            assigned = solve_global(costs, [null] * len(pending), [null] * len(available))
            links.update((pending[row], available[column]) for row, column in assigned.pairs)

        # Consumed members cannot leave an independent dormant ID behind.
        next_memory = {track_id: group for track_id, group in memory.items() if track_id not in claims}
        output = []
        for index, group in enumerate(groups):
            track_id = links.get(index)
            if track_id is None:
                self._last_id += 1
                track_id = str(self._last_id)
            next_memory[track_id] = group
            output.append(IdentifiedGroup(track_id, group))
        self._memory = next_memory
        self._clock = stamp
        return tuple(output)


def _member_continuity(groups, memory):
    owners = {member: track_id for track_id, group in memory.items() for member in group.members}
    previous_by_group = [{owners[member] for member in group.members if member in owners} for group in groups]
    claimed_by = defaultdict(set)
    for index, track_ids in enumerate(previous_by_group):
        for track_id in track_ids:
            claimed_by[track_id].add(index)

    links = {}
    for index, track_ids in enumerate(previous_by_group):
        if len(track_ids) == 1:
            track_id, = track_ids
            if len(claimed_by[track_id]) == 1:
                links[index] = track_id
    return links, claimed_by


def _geometry_cost(group, previous, stamp, radius_m):
    if not any(member in previous.members for member in group.members):
        fresh_sources = {member[0] for member, report in zip(previous.members, previous.observed_at)
                         if stamp <= report + FRESH_S}
        if any(member[0] in fresh_sources for member in group.members):
            return None
    distance = math.dist(group.position, previous.position)
    return None if distance > radius_m else distance**2
