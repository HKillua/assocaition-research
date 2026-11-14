"""Grade bounded fixed-cardinality rivals using frozen 20-second snapshots."""

from __future__ import annotations

from collections import Counter, defaultdict
from math import fsum, isfinite

from .frechet_trajectory import _SlotObjective, _validate_slots
from .peer_experiment import CARDINALITY_M, CUTOFF_M

MASKED = "frechet_masked_20s"
CURRENT = "frechet_current_20s"
UNIQUE = "frechet_unique_20s"
ARMS = (MASKED, CURRENT, UNIQUE)


def _snapshot(record):
    keys = tuple(tuple(tuple(key) for key in side) for side in record["keys"])
    tags = tuple(tuple({int(knot): stamp for knot, stamp in track.items()} for track in side)
                 for side in record["tags"])
    fits, slots = {}, {}
    for arm in ARMS:
        left, right = ([{int(knot): tuple(point) for knot, point in track.items()} for track in side]
                       for side in record["trajectories"][arm])
        fit = _SlotObjective(left, right, CUTOFF_M, CARDINALITY_M, unknown_mask=True)
        if fit.sizes != tuple(map(len, keys)):
            raise ValueError("attribution changed the frozen candidate population")
        arm_slots = tuple(tuple(slot) for slot in record["slots"][arm])
        _validate_slots(arm_slots, fit.sizes)
        fits[arm], slots[arm] = fit, arm_slots
    if tuple(map(len, tags)) != tuple(map(len, keys)):
        raise ValueError("report tags do not match the frozen candidates")
    return keys, tags, fits, slots


def _fixed_rival(slots, focal, anchor_side, rival):
    """Replace or swap opposing indices while holding all slot occupancies fixed."""
    side = 1 - anchor_side
    owner = slots.index(focal)
    other = next((i for i, slot in enumerate(slots) if slot[side] == rival), None)
    changed = list(slots)
    replacement = list(focal)
    replacement[side] = rival
    changed[owner] = tuple(replacement)
    step = "one_edge_unassigned"
    if other is not None:
        displaced = list(slots[other])
        displaced[side] = focal[side]
        changed[other] = tuple(displaced)
        step = "one_edge_singleton" if displaced[anchor_side] is None else "two_edge_swap"
    return tuple(replacement), tuple(changed), step


def _local_joint(fit, base, trial, focal, rival):
    if any(None not in (a, b) and not fit.pair_supported(fit.left[a], fit.right[b])
           for a, b in (focal, rival)):
        return None, None
    local = fit.cross_loss(*rival) - fit.cross_loss(*focal)
    changes = [(old, new) for old, new in zip(base, trial) if old != new]
    if any(None not in new and not fit.pair_supported(fit.left[new[0]], fit.right[new[1]])
           for _, new in changes):
        return local, None
    # Eq. 18's cardinality term and unchanged slots cancel exactly at fixed m.
    # Use Eq. 27 with the original population weights to refit both changed slots.
    left_n, right_n = (max(len(base), size) for size in fit.sizes)

    def loss(slot):
        if None in slot:
            return 0.0
        _, left, right = fit.pair_fit(*slot, left_n, right_n)
        return left / left_n + right / right_n

    joint = fit.squared_cutoff / 2 * fsum(loss(new) - loss(old) for old, new in changes)
    return local, joint


def _direction(delta, field):
    if delta is None:
        return "unavailable"
    tolerance = 1e-12 if field == "local" else 1e-6
    if delta < -tolerance:
        return "true_rival"
    return "focal_false" if delta > tolerance else "tie"


def _report_support(tags, fits, pair):
    a, b = pair
    old_common = fits[MASKED].left[a].keys() & fits[MASKED].right[b].keys()
    new_common = fits[UNIQUE].left[a].keys() & fits[UNIQUE].right[b].keys()
    return {
        "masked_common_grids": len(old_common),
        "unique_common_grids": len(new_common),
        "masked_distinct_report_pairs": len({(tags[0][a][k], tags[1][b][k]) for k in old_common}),
    }


def _observed_partner(slots, side, index):
    return next((slot[1 - side] for slot in slots if slot[side] == index), None)


def _true_pairs(slots, keys, labels):
    return sum(labels[keys[0][a]] == labels[keys[1][b]]
               for a, b in slots if a is not None and b is not None)


def _alternatives(keys, labels, side, anchor, competitors):
    peers = keys[1 - side]
    known = competitors.get(anchor)
    if known in peers and labels[known] == labels[anchor]:
        return "state_true_partner", (peers.index(known),)
    return "visible_true_set", tuple(i for i, peer in enumerate(peers) if labels[peer] == labels[anchor])


def _aggregate(rows):
    totals = defaultdict(Counter)
    for row in rows:
        rivals = row["rivals"]
        groups = [("input", row["rival_source"])]
        if not rivals:
            groups.append(("input", "no_visible_true_rival"))
        for arm in ARMS:
            for field in ("local", "joint"):
                statuses = sorted({_direction(rival["delta"][arm][field], field) for rival in rivals})
                if statuses:
                    groups.append((f"{arm}:{field}", "+".join(statuses)))
            groups.append((f"{arm}:raw_assignment", row["raw_assignment"][arm]))
        for arm in (CURRENT, UNIQUE):
            for field in ("local", "joint"):
                if any(_direction(rival["delta"][MASKED][field], field) == "focal_false"
                       and _direction(rival["delta"][arm][field], field) == "true_rival" for rival in rivals):
                    groups.append((f"{arm}:{field}", "strict_reversal_against_masked"))
        for field, status in groups:
            totals[field + ":" + status]["endpoint_intervals"] += 1
            totals[field + ":" + status]["endpoint_seconds"] += row["seconds"]
    return {category: dict(counts) for category, counts in sorted(totals.items())}


def attribute_disputes(disputes, snapshots, labels) -> dict:
    """Audit already labeled original false edges without a new global search.

    The three alternative objectives are evaluated on the same original active
    slots. Costs are rival minus focal, with direct distance in normalized
    squared units and joint deltas in square metres. A strict joint decrease
    identifies a feasible bounded competitor to the original incumbent only.
    Private occurrence rows use roster-local release and arm slot indices.
    Seconds aggregate once per endpoint interval, not once per possible rival.
    """
    rows = []
    previous = None
    applicable = (row for row in disputes if row["focus_direction"] == "mask_to_state")
    for dispute in sorted(applicable, key=lambda row: row["release_index"]):
        index = dispute["release_index"]
        seconds = dispute["end"] - dispute["start"]
        if not isfinite(seconds) or seconds <= 0:
            raise ValueError("an attributed interval must have positive finite duration")
        if index != previous:
            keys, tags, fits, slots = _snapshot(snapshots[index])
            previous = index
        edge = tuple(tuple(key) for key in dispute["focal_edge"])
        if edge[0] not in keys[0]:
            edge = edge[::-1]
        focal = tuple(side.index(key) for side, key in zip(keys, edge))
        if labels[edge[0]] == labels[edge[1]] or focal not in slots[MASKED]:
            raise ValueError("the disputed edge must be false and in the original slots")
        competitors = {}
        for pair in dispute["state_edges"]:
            first, second = map(tuple, pair)
            competitors.update(((first, second), (second, first)))
        baseline_truth = _true_pairs(slots[MASKED], keys, labels)
        for side, anchor in enumerate(edge):
            source, indices = _alternatives(keys, labels, side, anchor, competitors)
            rivals = []
            for rival in indices:
                pair, trial, step = _fixed_rival(slots[MASKED], focal, side, rival)
                delta = {}
                for arm in ARMS:
                    local, joint = _local_joint(fits[arm], slots[MASKED], trial, focal, pair)
                    delta[arm] = {"local": local, "joint": joint}
                rivals.append(dict(rival_index=rival, change=step, delta=delta,
                                   support=_report_support(tags, fits, pair),
                                   changed_pair_truth=_true_pairs(trial, keys, labels) - baseline_truth))
            observed = {arm: _observed_partner(arm_slots, side, focal[side])
                        for arm, arm_slots in slots.items()}
            raw_assignment = {
                arm: "independent" if partner is None else "same_focal_false" if partner == focal[1 - side]
                else "other_true" if labels[keys[1 - side][partner]] == labels[anchor] else "other_false"
                for arm, partner in observed.items()
            }
            rows.append(dict(index=index, seconds=seconds, anchor_side=side, focal=focal,
                             release_onset=dispute["release_onset"],
                             original_slot_count=len(slots[MASKED]), rival_source=source,
                             focal_support=_report_support(tags, fits, focal), rivals=rivals,
                             observed_partner=observed, raw_assignment=raw_assignment))
    return dict(endpoint_intervals=len(rows), endpoint_seconds=fsum(row["seconds"] for row in rows),
                summary=_aggregate(rows), private_occurrences=rows)
