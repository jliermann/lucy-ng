"""256-bit fingerprint encoding for subspectrum shifts.

A fingerprint compactly encodes a set of 13C chemical shifts as a 256-bit
(32-byte) bitset.  Each bit represents a 2 ppm wide bin:

    bin N covers [N * bin_ppm, (N+1) * bin_ppm)

With the default ``bin_ppm=2.0`` and 256 bins, the range is 0–511 ppm.
Shifts outside [0, 512) ppm are silently ignored.

The fingerprint is used for fast Boolean-AND pre-screening during SSC lookup
in Phase 51: the query fingerprint is AND-ed against each stored bitset; a
zero result means no overlap, eliminating the candidate without finer matching.
"""

from __future__ import annotations

import numpy as np

BIN_SIZE_PPM = 2.0
FINGERPRINT_BITS = 256
FINGERPRINT_BYTES = 32  # 256 / 8


def shifts_to_fingerprint(
    shifts: list[float], bin_ppm: float = BIN_SIZE_PPM
) -> bytes:
    """Encode 13C shifts as a 256-bit fingerprint (32 bytes).

    Each bit represents a 2 ppm bin.  Bin N covers
    ``[N * bin_ppm, (N+1) * bin_ppm)`` ppm.  With the default ``bin_ppm=2.0``,
    the valid range is 0–511 ppm (256 bins × 2 ppm = 512 ppm range).

    Shifts outside ``[0, 512)`` ppm are silently ignored.  Setting the same
    bit twice (two shifts in the same bin) is idempotent via bitwise OR.

    Args:
        shifts: List of 13C chemical shift values in ppm.
        bin_ppm: Bin width in ppm (default 2.0).

    Returns:
        32-byte fingerprint as a :class:`bytes` object.
    """
    fp = np.zeros(FINGERPRINT_BYTES, dtype=np.uint8)
    for shift in shifts:
        if 0.0 <= shift < FINGERPRINT_BITS * bin_ppm:
            bin_idx = int(shift / bin_ppm)
            fp[bin_idx // 8] |= np.uint8(1 << (bin_idx % 8))
    return fp.tobytes()
