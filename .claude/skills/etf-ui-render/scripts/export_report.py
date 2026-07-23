#!/usr/bin/env python3
"""Export a rendered report HTML to PDF, summary PNG, or editable DOCX.

PDF and PNG require a Chromium-family browser. DOCX uses pandoc, or macOS
textutil as a fallback. No dependency is installed automatically.
"""

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys


CHROME_NAMES = ("chromium", "chromium-browser", "google-chrome", "chrome")
CHROME_PATHS = (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
)


def find_chrome():
    configured = os.environ.get("CHROME_BIN")
    if configured and Path(configured).is_file():
        return configured
    for name in CHROME_NAMES:
        if path := shutil.which(name):
            return path
    return next((path for path in CHROME_PATHS if Path(path).is_file()), None)


def capabilities():
    return {
        "pdf": bool(find_chrome()),
        "png": bool(find_chrome()),
        "docx": bool(shutil.which("pandoc") or shutil.which("textutil")),
        "chrome": find_chrome(),
        "pandoc": shutil.which("pandoc"),
        "textutil": shutil.which("textutil"),
    }


def run(command):
    subprocess.run(command, check=True)


def export(source, output, format_name, image_height):
    source = Path(source).resolve()
    output = Path(output).resolve()
    if not source.is_file() or source.suffix.lower() not in {".html", ".htm"}:
        raise ValueError("source must be an existing HTML file")
    if output.suffix.lower() != f".{format_name}":
        raise ValueError(f"output must end with .{format_name}")
    output.parent.mkdir(parents=True, exist_ok=True)

    if format_name in {"pdf", "png"}:
        chrome = find_chrome()
        if not chrome:
            raise RuntimeError("Chrome/Chromium not found; set CHROME_BIN")
        command = [chrome, "--headless", "--disable-gpu", "--hide-scrollbars"]
        if format_name == "pdf":
            command += ["--no-pdf-header-footer", f"--print-to-pdf={output}"]
        else:
            command += [
                "--force-device-scale-factor=2",
                f"--window-size=430,{image_height}",
                f"--screenshot={output}",
            ]
        run(command + [source.as_uri()])
    elif pandoc := shutil.which("pandoc"):
        run([pandoc, str(source), "--from=html", "--output", str(output)])
    elif textutil := shutil.which("textutil"):
        run([textutil, "-convert", "docx", "-output", str(output), str(source)])
    else:
        raise RuntimeError("DOCX export requires pandoc or macOS textutil")

    if not output.is_file() or output.stat().st_size == 0:
        raise RuntimeError(f"export did not create {output}")
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", nargs="?", help="rendered HTML file")
    parser.add_argument("--format", choices=("pdf", "png", "docx"))
    parser.add_argument("--output")
    parser.add_argument(
        "--image-height",
        type=int,
        default=6000,
        help="PNG viewport height; use PNG for the summary page only",
    )
    parser.add_argument("--check", action="store_true", help="show available exporters")
    args = parser.parse_args()

    if args.check:
        print(json.dumps(capabilities(), ensure_ascii=False, indent=2))
        return
    if not args.source or not args.format or not args.output:
        parser.error("source, --format, and --output are required unless --check is used")
    if not 1000 <= args.image_height <= 12000:
        parser.error("--image-height must be between 1000 and 12000")

    try:
        output = export(args.source, args.output, args.format, args.image_height)
    except (ValueError, RuntimeError, subprocess.CalledProcessError) as error:
        parser.exit(1, f"export failed: {error}\n")
    print(output)


if __name__ == "__main__":
    main()
