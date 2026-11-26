"""news-image-20261126: emit the 26 November 2026 front page as one image.

The picture itself is baked into this repository as entry.png: a
newspaper front page put together in-session from the day's wire
reporting (Ukraine, Cairo, Jerusalem, Pyongyang, tariffs, plus the
news strip). This program does not draw anything and never touches
the network; it only checks that the bundled picture satisfies the
gate and copies it to the output directory.

Gate, per the bounty: the picture must be a whole PNG or JPEG, no
more than 1 MiB, and no side longer than 1024 px. Anything else is
refused with a plain error instead of a traceback.

To try it outside the grader:
    mkdir -p out && MAKEFUN_OUTPUT_DIR=out python3 main.py
"""

import os
import struct
import sys
from pathlib import Path

MAX_BYTES = 1024 * 1024
MAX_SIDE = 1024

DEST_DIR = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
SOURCE = Path(__file__).resolve().parent / "entry.png"

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
JPEG_START = b"\xff\xd8\xff"


def fail(message):
    raise SystemExit(f"entry image rejected: {message}")


def png_dimensions(blob):
    """(width, height) from a PNG header, or None when it is not a PNG."""
    if blob[:8] != PNG_SIGNATURE:
        return None
    if len(blob) < 24:
        fail("PNG header is truncated")
    width, height = struct.unpack_from(">II", blob, 16)
    return width, height


def jpeg_dimensions(blob):
    """(width, height) from a JPEG's first start-of-frame segment.

    Returns None when the bytes are not a JPEG, or when no frame
    segment turns up before the scan data begins.
    """
    if blob[:3] != JPEG_START:
        return None
    offset = 2
    while offset + 4 <= len(blob) and blob[offset] == 0xFF:
        code = blob[offset + 1]
        if code in (0xC0, 0xC1, 0xC2):
            if offset + 9 > len(blob):
                return None
            height, width = struct.unpack_from(">HH", blob, offset + 5)
            return width, height
        if code == 0xDA:
            return None
        (segment_size,) = struct.unpack_from(">H", blob, offset + 2)
        if segment_size < 2:
            return None
        offset += 2 + segment_size
    return None


def check_gate(blob):
    """Refuse anything the gate would not accept; return its dimensions."""
    if len(blob) > MAX_BYTES:
        fail(f"{len(blob)} bytes, over the 1 MiB limit")
    dimensions = png_dimensions(blob)
    if dimensions is None:
        dimensions = jpeg_dimensions(blob)
    if dimensions is None:
        fail("not a whole PNG or JPEG")
    width, height = dimensions
    if width > MAX_SIDE or height > MAX_SIDE:
        fail(f"{width}x{height}, over the {MAX_SIDE}x{MAX_SIDE} cap")
    return width, height


def main():
    blob = SOURCE.read_bytes()
    width, height = check_gate(blob)
    os.makedirs(DEST_DIR, exist_ok=True)
    target = Path(DEST_DIR) / "entry.png"
    target.write_bytes(blob)
    print(
        f"wrote {target} ({width}x{height}, {len(blob)} bytes)",
        file=sys.stderr,
    )


main()
