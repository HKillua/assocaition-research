"""One strict position prefix for peer baseline comparison on MTAD."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
import math

from .continuous_tracker import ACCELERATION_SPECTRAL_DENSITY, FRESH_S, MEMORY_S, LocalTrack, Plane
from .lindenmaier_association import DiagonalState

Fragment = tuple[str, str]
Point = tuple[float, float]


@dataclass(frozen=True)
class PrefixObservation:
    """Latest report time and raw metric position, with state at the snapshot time."""

    observed_at: float
    raw_location: Point
    state: DiagonalState


class LocalPrefix:
    """Receive one atomic position batch at each native epoch, then expose its prefix."""

    def __init__(self) -> None:
        self.plane: Plane | None = None
        self._clock = -math.inf
        self._locals: dict[Fragment, LocalTrack] = {}

    def ingest(self, stamp: float, positions: Mapping[Fragment, Point]) -> None:
        """Receive (latitude, longitude) reports from ``positions.event_batches``."""
        if not math.isfinite(stamp) or stamp <= self._clock:
            raise ValueError("native epochs must be strictly after earlier reports and snapshots")
        if not positions:
            raise ValueError("native epochs must contain at least one position")
        plane = self.plane or Plane.from_first_batch(positions.values())
        updated = {}
        for key, coordinates in positions.items():
            observation = plane.project(coordinates)
            prior = self._locals.get(key)
            if prior is None or stamp > prior.stamp + MEMORY_S:
                updated[key] = LocalTrack(stamp, observation, observation)
            else:
                updated[key] = prior.updated(stamp, observation)
        self._locals.update(updated)
        self.plane = plane
        self._advance(stamp)

    def snapshot(self, stamp: float) -> dict[Fragment, PrefixObservation]:
        """Return fresh observations at a nondecreasing release or window-closure time.

        An epoch with the same timestamp must already be ingested. Repeating a
        snapshot time yields equivalent results without updating local filters.
        """
        if not math.isfinite(stamp) or stamp < self._clock:
            raise ValueError("snapshot time must be finite and cannot go backwards")
        self._advance(stamp)
        return {
            key: PrefixObservation(track.stamp, track.observation, _predict(track, stamp))
            for key, track in self._locals.items()
            if stamp <= track.stamp + FRESH_S
        }

    def _advance(self, stamp: float) -> None:
        expired = [key for key, track in self._locals.items() if stamp > track.stamp + MEMORY_S]
        for key in expired:
            del self._locals[key]
        self._clock = stamp


def _predict(track: LocalTrack, stamp: float) -> DiagonalState:
    dt = stamp - track.stamp
    east, north = track.location
    ve, vn = track.velocity
    q = ACCELERATION_SPECTRAL_DENSITY
    pp = track.pp + 2 * dt * track.pv + dt**2 * track.vv + q * dt**3 / 3
    vv = track.vv + q * dt
    return DiagonalState((east + dt * ve, ve, north + dt * vn, vn), (pp, vv, pp, vv))
