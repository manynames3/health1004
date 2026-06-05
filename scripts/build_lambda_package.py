#!/usr/bin/env python3
import argparse
import os
import shutil
import subprocess
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the Health1004 FastAPI Lambda zip package.")
    parser.add_argument("--out", default="outputs/health1004-api-lambda.zip")
    parser.add_argument("--workdir", default="outputs/lambda-package")
    parser.add_argument("--python-version", default="3.12")
    parser.add_argument("--platform", default="manylinux2014_x86_64")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    package_dir = ROOT / args.workdir
    output_path = ROOT / args.out
    requirements = ROOT / "backend" / "requirements-lambda.txt"

    if package_dir.exists():
        shutil.rmtree(package_dir)
    package_dir.mkdir(parents=True)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    subprocess.run(
        [
            sys.executable,
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--upgrade",
            "--target",
            str(package_dir),
            "--platform",
            args.platform,
            "--implementation",
            "cp",
            "--python-version",
            args.python_version,
            "--only-binary=:all:",
            "-r",
            str(requirements),
        ],
        check=True,
    )

    shutil.copytree(ROOT / "backend" / "app", package_dir / "app", ignore=shutil.ignore_patterns("__pycache__"))
    shutil.copytree(ROOT / "data", package_dir / "data", ignore=shutil.ignore_patterns("__pycache__"))
    remove_unwanted_files(package_dir)

    if output_path.exists():
        output_path.unlink()
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for path in sorted(package_dir.rglob("*")):
            if path.is_file():
                archive.write(path, path.relative_to(package_dir).as_posix())

    size_mb = output_path.stat().st_size / (1024 * 1024)
    print(f"Wrote {output_path} ({size_mb:.1f} MB)")
    return 0


def remove_unwanted_files(package_dir: Path) -> None:
    for path in package_dir.rglob("__pycache__"):
        shutil.rmtree(path, ignore_errors=True)
    for path in package_dir.rglob("*.pyc"):
        path.unlink(missing_ok=True)
    for path in package_dir.rglob("*.pyo"):
        path.unlink(missing_ok=True)
    for path in package_dir.rglob("tests"):
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
    for path in package_dir.rglob("*.dist-info/RECORD"):
        path.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
