"""
Run every example, regenerate the images in docs/images/ and rebuild
docs/gallery.md.

Run:  python examples/run_all.py
"""

import runpy
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent


def main() -> int:
    scripts = sorted(p for p in HERE.glob("[0-9][0-9]_*.py"))
    failures = []
    for script in scripts:
        t0 = time.perf_counter()
        try:
            runpy.run_path(str(script), run_name="__main__")
        except Exception as err:  # noqa: BLE001 - report and keep going
            failures.append((script.name, err))
            print(f"FAILED {script.name}: {err!r}")
        else:
            print(f"ok     {script.name} ({time.perf_counter() - t0:.1f}s)")
    if failures:
        print(f"\n{len(failures)} example(s) failed")
        return 1
    runpy.run_path(str(HERE / "make_gallery.py"), run_name="__main__")
    print(f"\nAll {len(scripts)} examples ran; images are in docs/images/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
