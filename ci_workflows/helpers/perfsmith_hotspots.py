#!/usr/bin/env python3
"""
PerfSmith helper: scans backend and frontend sources to highlight hotspots.
Outputs a Markdown summary pointing to the largest modules/functions.
"""

from __future__ import annotations

import argparse
import pathlib
from dataclasses import dataclass
from datetime import datetime
from typing import List, Tuple


@dataclass
class FunctionStat:
    file: pathlib.Path
    name: str
    start: int
    end: int

    @property
    def length(self) -> int:
        return self.end - self.start + 1


def iter_python_files(base: pathlib.Path) -> List[pathlib.Path]:
    return [path for path in base.rglob("*.py") if ".venv" not in path.parts and "venv" not in path.parts]


def iter_js_files(base: pathlib.Path) -> List[pathlib.Path]:
    return [
        path for path in base.rglob("*.js")
        if "node_modules" not in path.parts and "build" not in path.parts
    ]


def parse_python_functions(path: pathlib.Path) -> List[FunctionStat]:
    functions: List[FunctionStat] = []
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    current: FunctionStat | None = None

    for idx, line in enumerate(lines, start=1):
        stripped = line.lstrip()
        if stripped.startswith("def "):
            if current:
                current.end = idx - 1
                functions.append(current)
            name = stripped[4:].split("(")[0].strip()
            indent = len(line) - len(stripped)
            current = FunctionStat(path, name or "<anonymous>", idx, len(lines))
            current._indent = indent  # type: ignore[attr-defined]
            continue

        if current and stripped and not stripped.startswith("#"):
            indent = len(line) - len(stripped)
            if indent <= getattr(current, "_indent", 0) and stripped.startswith(("def ", "class ")):
                current.end = idx - 1
                functions.append(current)
                current = None
                if stripped.startswith("def "):
                    name = stripped[4:].split("(")[0].strip()
                    new_func = FunctionStat(path, name or "<anonymous>", idx, len(lines))
                    new_func._indent = indent  # type: ignore[attr-defined]
                    current = new_func

    if current:
        functions.append(current)

    return functions


def js_line_counts(path: pathlib.Path) -> Tuple[pathlib.Path, int]:
    lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
    return (path, len(lines))


def render_markdown(output: pathlib.Path, py_funcs: List[FunctionStat], js_files: List[Tuple[pathlib.Path, int]]) -> None:
    py_hotspots = [f for f in sorted(py_funcs, key=lambda func: func.length, reverse=True) if f.length >= 60][:8]
    js_hotspots = sorted(js_files, key=lambda item: item[1], reverse=True)[:8]

    with output.open("w", encoding="utf-8") as handle:
        handle.write("# PerfSmith Hotspots\n")
        handle.write(f"Generated: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n")

        handle.write("## Python Functions ≥ 60 lines\n")
        if not py_hotspots:
            handle.write("_No functions exceeded 60 lines._\n\n")
        else:
            handle.write("| File | Function | Lines |\n| --- | --- | --- |\n")
            for stat in py_hotspots:
                if stat.length < 60:
                    continue
                rel = stat.file.as_posix()
                handle.write(f"| `{rel}` | `{stat.name}` | {stat.length} |\n")
            handle.write("\n")

        handle.write("## Largest Frontend Modules (by lines)\n")
        if not js_hotspots:
            handle.write("_No JavaScript files found._\n\n")
        else:
            handle.write("| File | Lines |\n| --- | --- |\n")
            for file_path, count in js_hotspots:
                rel = file_path.as_posix()
                handle.write(f"| `{rel}` | {count} |\n")
            handle.write("\n")

        handle.write("## Recommendations\n")
        handle.write("- Break down functions above 60 lines into smaller helpers.\n")
        handle.write("- Consider lazy loading or code splitting for the largest React modules.\n")
        handle.write("- Pair this report with runtime data via `RUN_PERF_BUILD=1 ci_workflows/agent_perfsmith.sh`.\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="PerfSmith hotspot analyzer")
    parser.add_argument("--backend-dir", type=pathlib.Path, required=True)
    parser.add_argument("--frontend-dir", type=pathlib.Path, required=True)
    parser.add_argument("--output", type=pathlib.Path, required=True)
    args = parser.parse_args()

    py_files = iter_python_files(args.backend_dir)
    py_funcs: List[FunctionStat] = []
    for path in py_files:
        py_funcs.extend(parse_python_functions(path))

    js_files = [js_line_counts(path) for path in iter_js_files(args.frontend_dir)]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    render_markdown(args.output, py_funcs, js_files)


if __name__ == "__main__":
    main()
