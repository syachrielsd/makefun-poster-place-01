#!/usr/bin/env python3
"""AURVIK — travel poster for a place that isn't there.

Copy-only entrypoint (Python 3.13, standard library only). The poster
(entry.png, 1024x1024) is composed at build time and committed with the
repo; this program never renders anything in the grader sandbox. It
copies entry.png from its own directory to the output directory and
byte-verifies the copy with SHA-256.
"""

import hashlib
import os
import shutil
import sys

SOURCE_NAME = "entry.png"


def output_dir():
    """MAKEFUN_OUTPUT_DIR first, then /output, then ./out."""
    for candidate in (
        os.environ.get("MAKEFUN_OUTPUT_DIR"),
        "/output",
        os.path.join(os.getcwd(), "out"),
    ):
        if candidate:
            return candidate
    return os.path.join(os.getcwd(), "out")


def sha256_of(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def jpeg_dimensions(path):
    """Read width/height from a JPEG's SOF marker (stdlib only).

    Returns (width, height), or None if the file is not a JPEG.
    """
    with open(path, "rb") as handle:
        data = handle.read(2)
        if data != b"\xff\xd8":
            return None
        while True:
            marker = handle.read(2)
            if len(marker) < 2 or marker[0] != 0xFF:
                return None
            code = marker[1]
            if code in (0xD8, 0xD9) or 0xD0 <= code <= 0xD7:
                continue
            length_bytes = handle.read(2)
            if len(length_bytes) < 2:
                return None
            length = int.from_bytes(length_bytes, "big")
            if 0xC0 <= code <= 0xCF and code not in (0xC4, 0xC8, 0xCC):
                frame = handle.read(5)
                if len(frame) < 5:
                    return None
                height = int.from_bytes(frame[1:3], "big")
                width = int.from_bytes(frame[3:5], "big")
                return (width, height)
            handle.seek(length - 2, 1)


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    source = os.path.join(here, SOURCE_NAME)
    if not os.path.isfile(source):
        print(f"error: {SOURCE_NAME} not found next to main.py", file=sys.stderr)
        return 1

    # Self-check the gate before copying: a whole JPEG, 1024x1024,
    # at most 1,048,576 bytes.
    dims = jpeg_dimensions(source)
    if dims is None:
        print("error: entry.png is not a JPEG", file=sys.stderr)
        return 1
    if dims != (1024, 1024):
        print(f"error: entry.png is {dims[0]}x{dims[1]}, expected 1024x1024",
              file=sys.stderr)
        return 1
    if os.path.getsize(source) > 1048576:
        print("error: entry.png exceeds 1,048,576 bytes", file=sys.stderr)
        return 1

    dest_dir = output_dir()
    os.makedirs(dest_dir, exist_ok=True)
    dest = os.path.join(dest_dir, SOURCE_NAME)

    shutil.copyfile(source, dest)

    source_hash = sha256_of(source)
    dest_hash = sha256_of(dest)
    if source_hash != dest_hash:
        print("error: byte verification failed", file=sys.stderr)
        return 1

    size = os.path.getsize(dest)
    print(f"wrote {dest} ({size} bytes, sha256={dest_hash})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
