"""Measure the effects of changing window history on frozen focal publications."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from itertools import pairwise
import math

from .continuous_tracker import FRESH_S
from .peer_chain_audit import _check_frozen, _live_edges
from .peer_chain_intervals import Chain, FrozenFrame, endpoint_status, false_chains, frame_cuts
from .peer_prefix import Fragment

STATE = "state_20s"
MASK = "frechet_masked_20s"
CURRENT = "frechet_current_20s"
UNIQUE = "frechet_unique_20s"
ARMS = (STATE, MASK, CURRENT, UNIQUE)
TRUE_REPLACEMENT = frozenset(("4827", "4979"))
WRONG_EXTENSION = frozenset(("3062", "4409"))


@dataclass
class _ChainAudit:
    chain: Chain
    source_seconds: Counter = field(default_factory=Counter)
    comparison_endpoint_seconds: dict = field(default_factory=lambda: {CURRENT: Counter(), UNIQUE: Counter()})
    changed_pair_seconds: float = 0.0
    previous_dispute: tuple | None = None

    def summary(self):
        return dict(
            duration_seconds=self.chain.end - self.chain.start, end_reason=self.chain.reason,
            original_relation_pair_seconds=dict(self.source_seconds),
            comparison_endpoint_seconds={arm: dict(counts) for arm, counts in self.comparison_endpoint_seconds.items()},
            focal_pair_seconds=self.changed_pair_seconds,
        )


def audit_focus(
    scene: str, frames_by_arm: Mapping[str, Sequence[FrozenFrame]], labels: Mapping[Fragment, str], stop: float,
) -> dict:
    """Audit focal wrong chains in the same fixed-release population.

    Forward scenes follow state-arm long false chains and count each end where
    the original masked arm replaced its partner with a true one. Reverse
    scenes follow masked-arm long false chains and separate state same-edge
    long/short exposure from intervals where the state chose something else.
    Only ``disputes`` carries member keys and exact times. Its ``entered``
    marks a new region of unchanged original matching for a focal chain.
    """
    if scene not in TRUE_REPLACEMENT | WRONG_EXTENSION:
        raise ValueError("expected a prospectively selected focal scene")
    if set(frames_by_arm) != set(ARMS):
        raise ValueError("expected the four frozen history comparison arms")
    forward = scene in TRUE_REPLACEMENT
    direction = "state_to_mask" if forward else "mask_to_state"
    origin, comparator = (STATE, MASK) if forward else (MASK, STATE)
    reference = frames_by_arm[origin]
    stamps = tuple(frame.stamp for frame in reference)
    reports = tuple(frame.reports for frame in reference)
    for frames in frames_by_arm.values():
        _check_frozen(frames, stamps, reports, stop)
    if any(key not in labels for report in reports for key in report):
        raise ValueError("frozen member has no post-replay label")

    original = [_ChainAudit(chain) for chain in false_chains(reference, labels, stop) if _long(chain)]
    by_edge = defaultdict(list)
    for item in original:
        by_edge[item.chain.edge].append(item)
    comparison_chains = defaultdict(list)
    for chain in false_chains(frames_by_arm[comparator], labels, stop):
        comparison_chains[chain.edge].append(chain)

    disputes = []
    controls = Counter()
    source_endpoints = Counter()
    for index, frame in enumerate(reference):
        end_of_frame = stamps[index + 1] if index + 1 < len(stamps) else stop
        other = frames_by_arm[comparator][index]
        release_edges = {
            arm: {(key, peer) for key, peer in frames_by_arm[arm][index].partners.items() if key < peer}
            for arm in (STATE, MASK)
        }
        for start, end in pairwise(frame_cuts(frame, other, end_of_frame)):
            if end <= start:
                continue
            seconds = end - start
            original_edges = _live_edges(frame, start)
            comparison_edges = _live_edges(other, start)
            controls["unchanged_true_pair_seconds"] += seconds * sum(
                labels[left] == labels[right] for left, right in original_edges & comparison_edges
            )
            for edge in sorted(original_edges & by_edge.keys()):
                item = next((entry for entry in by_edge[edge] if entry.chain.start <= start < entry.chain.end), None)
                if item is None:
                    continue
                statuses = tuple(endpoint_status(other, key, peer, labels, start) for key, peer in (edge, edge[::-1]))
                for outcome in statuses:
                    source_endpoints[outcome] += seconds
                if edge in comparison_edges:
                    still_long = any(_long(chain) and chain.start <= start < chain.end
                                     for chain in comparison_chains[edge])
                    overlap = "same_false_long" if still_long else "same_false_short"
                    item.source_seconds[overlap] += seconds
                    item.previous_dispute = None
                    continue
                item.source_seconds["absent_same_false"] += seconds
                eligible = tuple(endpoint for endpoint, status in zip(edge, statuses) if not forward or status == "other_true")
                if not eligible:
                    item.previous_dispute = None
                    continue

                item.changed_pair_seconds += seconds
                for arm in (CURRENT, UNIQUE):
                    alternate = frames_by_arm[arm][index]
                    for endpoint in eligible:
                        original_peer = edge[1] if endpoint == edge[0] else edge[0]
                        outcome = _outcome(alternate, other, endpoint, original_peer, labels, start)
                        item.comparison_endpoint_seconds[arm][outcome] += seconds

                state_edges, mask_edges = (
                    (original_edges, comparison_edges) if forward else (comparison_edges, original_edges)
                )
                left, right = _changed_matching(edge, state_edges, mask_edges)
                release_left, release_right = _changed_matching(edge, release_edges[STATE], release_edges[MASK])
                signature = (left, right)
                entered = item.previous_dispute != (start, signature)
                item.previous_dispute = (end, signature)
                disputes.append(dict(
                    release_index=index, release_time=frame.stamp, focal_edge=edge, chain_start=item.chain.start,
                    start=start, end=end, entered=entered, release_onset=entered and start == frame.stamp,
                    focus_direction=direction, state_edges=left, mask_edges=right,
                    release_state_edges=release_left, release_mask_edges=release_right,
                    source_statuses=statuses, focal_endpoints=eligible,
                ))

    focal_seconds = math.fsum(item.changed_pair_seconds for item in original)
    long_seconds = math.fsum(item.chain.end - item.chain.start for item in original)
    original_relation = Counter()
    results = {arm: Counter() for arm in (CURRENT, UNIQUE)}
    for item in original:
        _same_seconds(math.fsum(item.source_seconds.values()), item.chain.end - item.chain.start)
        original_relation.update(item.source_seconds)
        for arm, counts in item.comparison_endpoint_seconds.items():
            results[arm].update(counts)
    changed_endpoints = math.fsum(
        (row["end"] - row["start"]) * len(row["focal_endpoints"]) for row in disputes
    )
    _same_seconds(math.fsum(source_endpoints.values()), 2 * long_seconds)
    _same_seconds(math.fsum(row["end"] - row["start"] for row in disputes), focal_seconds)
    for counts in results.values():
        _same_seconds(math.fsum(counts.values()), changed_endpoints)
    return dict(
        focus=direction, chain_count=len(original), long_pair_seconds=long_seconds,
        focal_pair_seconds=focal_seconds, focal_endpoint_seconds=changed_endpoints,
        original_endpoint_seconds=dict(source_endpoints), original_relation_pair_seconds=dict(original_relation),
        comparison_endpoint_seconds={arm: dict(counts) for arm, counts in results.items()},
        chains=[item.summary() for item in original], controls=dict(controls), disputes=disputes,
        changed_releases=len({row["release_index"] for row in disputes}),
        entered_releases=len({row["release_index"] for row in disputes if row["release_onset"]}),
    )


def _long(chain: Chain) -> bool:
    return chain.end > chain.start + FRESH_S


def _outcome(alternate, comparator, endpoint, old_peer, labels, start):
    status = endpoint_status(alternate, endpoint, old_peer, labels, start)
    if status == "other_true":
        peer = comparator.partners.get(endpoint)
        has_same_truth = peer == alternate.partners[endpoint] and endpoint_status(
            comparator, endpoint, old_peer, labels, start
        ) == "other_true"
        return "same_true" if has_same_truth else "different_true"
    return status


def _changed_matching(edge, left, right):
    changed = left ^ right
    adjacency = defaultdict(set)
    for first, second in changed:
        adjacency[first].add(second)
        adjacency[second].add(first)
    nodes = set(edge)
    pending = list(edge)
    while pending:
        peers = adjacency[pending.pop()] - nodes
        nodes.update(peers)
        pending.extend(peers)
    members = {pair for pair in changed if pair[0] in nodes}
    return tuple(sorted(members & left)), tuple(sorted(members & right))


def _same_seconds(first, second):
    if not math.isclose(first, second, rel_tol=0, abs_tol=1e-7):
        raise ValueError(f"focal chain time does not reconcile: {first} vs {second}")
