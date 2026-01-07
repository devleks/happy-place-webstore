#!/usr/bin/env python3
"""
PerfSmith Hotspot Analyzer - Optimized Edition
Scans backend (Python) and frontend (JS/TS/JSX/TSX) sources to identify performance hotspots.
Outputs detailed Markdown and optional JSON summary.

Features:
- Multi-language support (Python, JavaScript, TypeScript, React)
- Function complexity analysis
- Import dependency tracking
- Cyclomatic complexity estimation
- JSON output for CI/CD integration
- Enhanced error handling
"""

from __future__ import annotations

import argparse
import ast
import json
import pathlib
import re
import sys
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import List, Tuple, Dict, Optional


@dataclass
class FunctionStat:
    """Statistics for a single function/method"""
    file: str  # Convert Path to str for JSON serialization
    name: str
    start: int
    end: int
    complexity: int = 0
    num_params: int = 0
    
    @property
    def length(self) -> int:
        return self.end - self.start + 1
    
    def to_dict(self) -> dict:
        return {
            "file": self.file,
            "name": self.name,
            "start_line": self.start,
            "end_line": self.end,
            "length": self.length,
            "complexity": self.complexity,
            "num_params": self.num_params
        }


@dataclass
class FileStat:
    """Statistics for a source file"""
    file: str
    lines: int
    functions: int = 0
    imports: int = 0
    complexity: int = 0
    
    def to_dict(self) -> dict:
        return asdict(self)


def safe_read_file(path: pathlib.Path, encoding: str = "utf-8") -> Optional[str]:
    """Safely read file with fallback encodings"""
    encodings = [encoding, "utf-8", "latin-1", "cp1252"]
    
    for enc in encodings:
        try:
            return path.read_text(encoding=enc)
        except (UnicodeDecodeError, LookupError):
            continue
        except Exception as e:
            print(f"Warning: Could not read {path}: {e}", file=sys.stderr)
            return None
    
    return None


def iter_python_files(base: pathlib.Path) -> List[pathlib.Path]:
    """Find all Python files, excluding virtual environments"""
    exclude_patterns = {".venv", "venv", "__pycache__", ".pytest_cache", ".tox", "env"}
    
    python_files = []
    for path in base.rglob("*.py"):
        # Skip if any excluded pattern in path
        if any(pattern in path.parts for pattern in exclude_patterns):
            continue
        python_files.append(path)
    
    return python_files


def iter_frontend_files(base: pathlib.Path) -> List[pathlib.Path]:
    """Find all frontend files (JS, JSX, TS, TSX)"""
    exclude_patterns = {"node_modules", "build", "dist", ".next", "coverage", ".cache"}
    extensions = {".js", ".jsx", ".ts", ".tsx"}
    
    frontend_files = []
    for ext in extensions:
        for path in base.rglob(f"*{ext}"):
            # Skip if any excluded pattern in path
            if any(pattern in path.parts for pattern in exclude_patterns):
                continue
            # Skip minified files
            if ".min." in path.name:
                continue
            frontend_files.append(path)
    
    return frontend_files


def calculate_cyclomatic_complexity(code: str) -> int:
    """Estimate cyclomatic complexity (simplified)"""
    # Count decision points: if, elif, for, while, except, and, or
    complexity = 1  # Base complexity
    
    keywords = [
        r'\bif\b', r'\belif\b', r'\bfor\b', r'\bwhile\b',
        r'\bexcept\b', r'\band\b', r'\bor\b', r'\bcase\b'
    ]
    
    for keyword in keywords:
        complexity += len(re.findall(keyword, code))
    
    return complexity


def parse_python_functions_ast(path: pathlib.Path) -> Tuple[List[FunctionStat], int]:
    """Parse Python file using AST for accurate analysis"""
    text = safe_read_file(path)
    if not text:
        return [], 0
    
    functions = []
    total_complexity = 0
    
    try:
        tree = ast.parse(text)
        
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Calculate function complexity
                func_code = ast.get_source_segment(text, node)
                complexity = calculate_cyclomatic_complexity(func_code or "")
                
                stat = FunctionStat(
                    file=str(path),
                    name=node.name,
                    start=node.lineno,
                    end=node.end_lineno or node.lineno,
                    complexity=complexity,
                    num_params=len(node.args.args)
                )
                functions.append(stat)
                total_complexity += complexity
    
    except SyntaxError as e:
        print(f"Warning: Syntax error in {path}: {e}", file=sys.stderr)
        # Fallback to regex-based parsing
        return parse_python_functions_regex(path)
    except Exception as e:
        print(f"Warning: Could not parse {path}: {e}", file=sys.stderr)
        return [], 0
    
    return functions, total_complexity


def parse_python_functions_regex(path: pathlib.Path) -> Tuple[List[FunctionStat], int]:
    """Fallback regex-based Python function parsing"""
    text = safe_read_file(path)
    if not text:
        return [], 0
    
    functions: List[FunctionStat] = []
    lines = text.splitlines()
    current: Optional[FunctionStat] = None
    
    for idx, line in enumerate(lines, start=1):
        stripped = line.lstrip()
        if stripped.startswith("def ") or stripped.startswith("async def "):
            if current:
                current.end = idx - 1
                functions.append(current)
            
            # Extract function name
            match = re.match(r'(?:async\s+)?def\s+(\w+)\s*\(', stripped)
            name = match.group(1) if match else "<anonymous>"
            
            indent = len(line) - len(stripped)
            current = FunctionStat(
                file=str(path),
                name=name,
                start=idx,
                end=len(lines)
            )
            current._indent = indent  # type: ignore
            continue
        
        if current and stripped and not stripped.startswith("#"):
            indent = len(line) - len(stripped)
            if indent <= getattr(current, "_indent", 0) and stripped.startswith(("def ", "class ", "async ")):
                current.end = idx - 1
                functions.append(current)
                current = None
    
    if current:
        functions.append(current)
    
    return functions, 0


def analyze_python_file(path: pathlib.Path) -> FileStat:
    """Comprehensive Python file analysis"""
    text = safe_read_file(path)
    if not text:
        return FileStat(file=str(path), lines=0)
    
    lines = text.splitlines()
    
    # Count imports
    import_count = sum(1 for line in lines if re.match(r'^\s*(?:import|from)\s+', line))
    
    # Parse functions
    functions, complexity = parse_python_functions_ast(path)
    
    return FileStat(
        file=str(path),
        lines=len(lines),
        functions=len(functions),
        imports=import_count,
        complexity=complexity
    )


def analyze_frontend_file(path: pathlib.Path) -> FileStat:
    """Analyze JavaScript/TypeScript file"""
    text = safe_read_file(path)
    if not text:
        return FileStat(file=str(path), lines=0)
    
    lines = text.splitlines()
    
    # Count imports (import statements)
    import_count = sum(1 for line in lines if re.match(r'^\s*import\s+', line))
    
    # Count functions (function, arrow functions, methods)
    function_patterns = [
        r'function\s+\w+\s*\(',
        r'const\s+\w+\s*=\s*\(',
        r'=>',
        r'^\s*\w+\s*\([^)]*\)\s*{',  # methods
    ]
    function_count = 0
    for pattern in function_patterns:
        function_count += len(re.findall(pattern, text))
    
    # Estimate complexity
    complexity = calculate_cyclomatic_complexity(text)
    
    return FileStat(
        file=str(path),
        lines=len(lines),
        functions=function_count,
        imports=import_count,
        complexity=complexity
    )


def render_markdown(
    output: pathlib.Path,
    py_files: List[FileStat],
    py_funcs: List[FunctionStat],
    fe_files: List[FileStat]
) -> None:
    """Generate comprehensive Markdown report"""
    
    # Top hotspots
    py_func_hotspots = sorted(py_funcs, key=lambda f: f.length, reverse=True)[:10]
    py_complex_funcs = sorted(py_funcs, key=lambda f: f.complexity, reverse=True)[:10]
    py_large_files = sorted(py_files, key=lambda f: f.lines, reverse=True)[:10]
    fe_large_files = sorted(fe_files, key=lambda f: f.lines, reverse=True)[:10]
    fe_complex_files = sorted(fe_files, key=lambda f: f.complexity, reverse=True)[:10]
    
    with output.open("w", encoding="utf-8") as f:
        f.write("# PerfSmith Hotspot Analysis\n")
        f.write(f"**Generated:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}\n\n")
        
        # Summary statistics
        f.write("## 📊 Summary Statistics\n\n")
        f.write(f"- **Python Files:** {len(py_files)}\n")
        f.write(f"- **Python Functions:** {len(py_funcs)}\n")
        f.write(f"- **Frontend Files:** {len(fe_files)}\n")
        f.write(f"- **Total Lines (Python):** {sum(pf.lines for pf in py_files):,}\n")
        f.write(f"- **Total Lines (Frontend):** {sum(ff.lines for ff in fe_files):,}\n\n")
        
        # Python function hotspots
        f.write("## 🔥 Python Function Hotspots (by length)\n\n")
        if not py_func_hotspots:
            f.write("_No Python functions found._\n\n")
        else:
            f.write("| File | Function | Lines | Complexity | Params |\n")
            f.write("|------|----------|-------|------------|--------|\n")
            for stat in py_func_hotspots:
                if stat.length < 30:  # Only show functions >= 30 lines
                    continue
                f.write(f"| `{stat.file}` | `{stat.name}` | {stat.length} | {stat.complexity} | {stat.num_params} |\n")
            f.write("\n")
        
        # Complex Python functions
        f.write("## 🧩 Most Complex Python Functions\n\n")
        if not py_complex_funcs:
            f.write("_No complex functions found._\n\n")
        else:
            f.write("| File | Function | Complexity | Lines |\n")
            f.write("|------|----------|------------|-------|\n")
            for stat in py_complex_funcs[:8]:
                if stat.complexity < 10:  # Only show high complexity
                    continue
                f.write(f"| `{stat.file}` | `{stat.name}` | {stat.complexity} | {stat.length} |\n")
            f.write("\n")
        
        # Large Python files
        f.write("## 📄 Largest Python Files\n\n")
        if not py_large_files:
            f.write("_No Python files found._\n\n")
        else:
            f.write("| File | Lines | Functions | Imports | Avg Complexity |\n")
            f.write("|------|-------|-----------|---------|----------------|\n")
            for stat in py_large_files:
                avg_complexity = stat.complexity // max(stat.functions, 1)
                f.write(f"| `{stat.file}` | {stat.lines} | {stat.functions} | {stat.imports} | {avg_complexity} |\n")
            f.write("\n")
        
        # Large frontend files
        f.write("## 📱 Largest Frontend Files\n\n")
        if not fe_large_files:
            f.write("_No frontend files found._\n\n")
        else:
            f.write("| File | Lines | Functions | Imports | Complexity |\n")
            f.write("|------|-------|-----------|---------|------------|\n")
            for stat in fe_large_files:
                f.write(f"| `{stat.file}` | {stat.lines} | {stat.functions} | {stat.imports} | {stat.complexity} |\n")
            f.write("\n")
        
        # Complex frontend files
        f.write("## 🎯 Most Complex Frontend Files\n\n")
        if not fe_complex_files:
            f.write("_No complex frontend files found._\n\n")
        else:
            f.write("| File | Complexity | Lines | Functions |\n")
            f.write("|------|------------|-------|----------|\n")
            for stat in fe_complex_files[:8]:
                if stat.complexity < 50:  # Only show high complexity
                    continue
                f.write(f"| `{stat.file}` | {stat.complexity} | {stat.lines} | {stat.functions} |\n")
            f.write("\n")
        
        # Recommendations
        f.write("## 💡 Recommendations\n\n")
        f.write("### Code Quality\n")
        f.write("- **Break down functions >60 lines** into smaller, focused helpers\n")
        f.write("- **Reduce complexity >15** by extracting conditional logic\n")
        f.write("- **Limit parameters to 5-7** for better maintainability\n\n")
        
        f.write("### Performance\n")
        f.write("- **Code-split large React components** (>300 lines)\n")
        f.write("- **Use React.lazy()** for conditional/route-based components\n")
        f.write("- **Consider memoization** for complex computations\n\n")
        
        f.write("### Maintainability\n")
        f.write("- **Files >500 lines** should be split into multiple modules\n")
        f.write("- **High import counts** (>20) suggest tight coupling\n")
        f.write("- **Review complex files** for potential refactoring opportunities\n\n")
        
        f.write("### Next Steps\n")
        f.write("1. Profile runtime performance with browser DevTools\n")
        f.write("2. Run `RUN_PERF_BUILD=1 ci_workflows/agent_perfsmith.sh` for bundle analysis\n")
        f.write("3. Use `pytest --cov` to identify untested complex code\n")
        f.write("4. Consider adding complexity gates to your CI/CD pipeline\n")


def render_json(
    output: pathlib.Path,
    py_files: List[FileStat],
    py_funcs: List[FunctionStat],
    fe_files: List[FileStat]
) -> None:
    """Generate JSON output for CI/CD integration"""
    
    data = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "summary": {
            "python_files": len(py_files),
            "python_functions": len(py_funcs),
            "python_total_lines": sum(pf.lines for pf in py_files),
            "frontend_files": len(fe_files),
            "frontend_total_lines": sum(ff.lines for ff in fe_files),
        },
        "python": {
            "files": [f.to_dict() for f in sorted(py_files, key=lambda x: x.lines, reverse=True)[:20]],
            "functions": [f.to_dict() for f in sorted(py_funcs, key=lambda x: x.length, reverse=True)[:20]],
        },
        "frontend": {
            "files": [f.to_dict() for f in sorted(fe_files, key=lambda x: x.lines, reverse=True)[:20]],
        },
        "recommendations": []
    }
    
    # Add automated recommendations
    large_funcs = [f for f in py_funcs if f.length > 60]
    if large_funcs:
        data["recommendations"].append(f"Refactor {len(large_funcs)} Python functions >60 lines")
    
    complex_funcs = [f for f in py_funcs if f.complexity > 15]
    if complex_funcs:
        data["recommendations"].append(f"Simplify {len(complex_funcs)} Python functions with complexity >15")
    
    large_fe_files = [f for f in fe_files if f.lines > 300]
    if large_fe_files:
        data["recommendations"].append(f"Split {len(large_fe_files)} frontend files >300 lines")
    
    with output.open("w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def main() -> int:
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="PerfSmith Hotspot Analyzer - Optimized Edition",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--backend-dir", type=pathlib.Path, required=True,
                       help="Path to backend Python source directory")
    parser.add_argument("--frontend-dir", type=pathlib.Path, required=True,
                       help="Path to frontend source directory")
    parser.add_argument("--output", type=pathlib.Path, required=True,
                       help="Output Markdown file path")
    parser.add_argument("--json", type=pathlib.Path,
                       help="Optional JSON output file for CI/CD")
    parser.add_argument("--min-function-length", type=int, default=30,
                       help="Minimum function length to report (default: 30)")
    parser.add_argument("--min-complexity", type=int, default=10,
                       help="Minimum complexity to report (default: 10)")
    
    args = parser.parse_args()
    
    # Validate inputs
    if not args.backend_dir.exists():
        print(f"Error: Backend directory not found: {args.backend_dir}", file=sys.stderr)
        return 1
    
    if not args.frontend_dir.exists():
        print(f"Error: Frontend directory not found: {args.frontend_dir}", file=sys.stderr)
        return 1
    
    print(f"Analyzing Python files in {args.backend_dir}...")
    py_paths = iter_python_files(args.backend_dir)
    py_files = [analyze_python_file(p) for p in py_paths]
    
    py_funcs: List[FunctionStat] = []
    for path in py_paths:
        funcs, _ = parse_python_functions_ast(path)
        py_funcs.extend(funcs)
    
    print(f"Found {len(py_files)} Python files, {len(py_funcs)} functions")
    
    print(f"Analyzing frontend files in {args.frontend_dir}...")
    fe_paths = iter_frontend_files(args.frontend_dir)
    fe_files = [analyze_frontend_file(p) for p in fe_paths]
    
    print(f"Found {len(fe_files)} frontend files")
    
    # Create output directory
    args.output.parent.mkdir(parents=True, exist_ok=True)
    
    # Generate outputs
    print(f"Generating Markdown report: {args.output}")
    render_markdown(args.output, py_files, py_funcs, fe_files)
    
    if args.json:
        print(f"Generating JSON report: {args.json}")
        render_json(args.json, py_files, py_funcs, fe_files)
    
    print("✓ Analysis complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
