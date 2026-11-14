"""Recover the original report tags behind a frozen Fréchet window."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
import math
from typing import Literal

from .peer_prefix import Fragment
from .peer_replay import ReplayFrame

Edge = tuple[Fragment, Fragment]
ReportTag = tuple[Fragment, float]
LineageCategory = Literal["single_grid", "both_advanced", "one_advanced", "reused"]


@dataclass(frozen=True)
class EdgeLineage:
    """Measure advancement of native report tags at common closed grids."""

    category: LineageCategory
    common_grids: int
    distinct_tag_pairs: int
    older_latest_tags: frozenset[ReportTag]
    side_tag_counts: tuple[int, int]
    report_tags: frozenset[ReportTag]
    common_indices: tuple[int, ...]
    latest_pairs: tuple[tuple[float, float], ...]


def edge_lineage(edge: Edge, grids: Sequence[Mapping[Fragment, float]]) -> EdgeLineage:
    """Classify one current cross-source edge over up to three frozen grids.

    Pass the grid maps from oldest to current, with only the fresh observations
    published on each grid. The caller separately verifies common clocks and
    complete matching observation maps across arms. Both endpoints must be
    eligible on the current grid. History is considered on common grids only.
    A new tag certifies a different report. The corresponding filtered states
    can still share earlier input reports.
    """
    left, right = edge
    if left[0] == right[0]:
        raise ValueError("a lineage edge requires different sources")
    if not 1 <= len(grids) <= 3:
        raise ValueError("provide the current grid and at most two trailing grids")
    if left not in grids[-1] or right not in grids[-1]:
        raise ValueError("both edge endpoints must be eligible on the current grid")

    indices = tuple(index for index, grid in enumerate(grids) if left in grid and right in grid)
    pairs = tuple((grids[index][left], grids[index][right]) for index in indices)
    left_times, right_times = zip(*pairs)
    if (not all(map(math.isfinite, (*left_times, *right_times)))
            or any(t1 > t2 for times in (left_times, right_times) for t1, t2 in zip(times, times[1:]))):
        raise ValueError("latest report times must be finite and nondecreasing")

    side_counts = (len(set(left_times)), len(set(right_times)))
    advanced = sum(count > 1 for count in side_counts)
    category: LineageCategory = "single_grid"
    if len(indices) >= 2:
        category = ("reused", "one_advanced", "both_advanced")[advanced]

    tags = frozenset((endpoint, stamp)
                     for endpoint, times in zip(edge, (left_times, right_times))
                     for stamp in times)
    older_tags = tags - {(left, left_times[-1]), (right, right_times[-1])}
    return EdgeLineage(category, len(indices), len(set(pairs)), older_tags,
                       side_counts, tags, indices, pairs)


def indirect_report_tags(
    edge: Edge, frames: Sequence[ReplayFrame], lineage: EdgeLineage,
) -> frozenset[ReportTag]:
    """Return endpoint arrivals superseded before a closed grid can show them.

    Frames follow the same order and cover the same window used for lineage.
    Look strictly after the first common grid and through the last common grid.
    Check latest tags on all intervening grids, including one-sided grids. An
    indirect tag marks a raw input to the shared prefix, not an extra knot.
    """
    first, last = lineage.common_indices[0], lineage.common_indices[-1]
    if not 1 <= len(frames) <= 3 or last != len(frames) - 1:
        raise ValueError("replay frames must cover the original trailing lineage window")
    for index, stamps in zip(lineage.common_indices, lineage.latest_pairs):
        if any(key not in frames[index].observations or frames[index].observations[key].observed_at != stamp
               for key, stamp in zip(edge, stamps)):
            raise ValueError("replay report tags differ from the frozen window")

    interval = frames[first + 1:last + 1]
    arrivals = {(key, stamp) for frame in interval for stamp, keys in frame.arrivals
                for key in keys if key in edge}
    directly_seen = {(key, frame.observations[key].observed_at) for frame in interval
                     for key in edge if key in frame.observations}
    return frozenset(arrivals - directly_seen)
