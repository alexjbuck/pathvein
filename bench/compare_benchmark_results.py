#!/usr/bin/env python3
"""
Compare pytest-benchmark JSON results and generate markdown report.

This script is used by CI to compare Rust vs Python benchmark results
and generate markdown output for PR comments.

Usage:
    python compare_benchmark_results.py rust.json python.json --output-markdown=comparison.md
"""

import argparse
import json
import sys
from typing import Dict, List, Any


def load_benchmark_json(filepath: str) -> Dict[str, Any]:
    """Load a pytest-benchmark JSON file."""
    with open(filepath) as f:
        return json.load(f)


def extract_benchmarks(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract benchmark results from pytest-benchmark JSON."""
    benchmarks = []
    for bench in data.get("benchmarks", []):
        benchmarks.append({
            "name": bench["name"],
            "fullname": bench["fullname"],
            "mean": bench["stats"]["mean"],
            "stddev": bench["stats"]["stddev"],
            "median": bench["stats"]["median"],
            "min": bench["stats"]["min"],
            "max": bench["stats"]["max"],
            "rounds": bench["stats"]["rounds"],
        })
    return benchmarks


def generate_markdown_comparison(rust_data: Dict, python_data: Dict) -> str:
    """Generate markdown comparison of Rust vs Python benchmarks."""
    rust_benchmarks = {b["name"]: b for b in extract_benchmarks(rust_data)}
    python_benchmarks = {b["name"]: b for b in extract_benchmarks(python_data)}

    # Get common benchmark names
    common_names = set(rust_benchmarks.keys()) & set(python_benchmarks.keys())

    if not common_names:
        return "⚠️ No common benchmarks found between Rust and Python results."

    lines = [
        "# 🚀 Pathvein Performance Comparison: Rust vs Python",
        "",
        f"Compared {len(common_names)} benchmarks between Rust and Python backends.",
        "",
        "## Summary",
        "",
        "| Benchmark | Python (ms) | Rust (ms) | Speedup | Δ |",
        "|-----------|-------------|-----------|---------|---|",
    ]

    speedups = []
    for name in sorted(common_names):
        rust = rust_benchmarks[name]
        python = python_benchmarks[name]

        python_ms = python["mean"] * 1000
        rust_ms = rust["mean"] * 1000
        speedup = python["mean"] / rust["mean"]
        speedups.append(speedup)

        # Determine emoji based on speedup
        if speedup >= 2.0:
            emoji = "🚀"  # Significant speedup
        elif speedup >= 1.2:
            emoji = "⚡"  # Moderate speedup
        elif speedup >= 0.8:
            emoji = "➖"  # Comparable
        else:
            emoji = "🐌"  # Python faster (unusual)

        # Format benchmark name
        display_name = name.replace("test_", "").replace("_", " ").title()

        lines.append(
            f"| {display_name} | {python_ms:.3f} | {rust_ms:.3f} | "
            f"{speedup:.2f}x | {emoji} |"
        )

    # Calculate overall statistics
    avg_speedup = sum(speedups) / len(speedups)
    max_speedup = max(speedups)
    min_speedup = min(speedups)

    lines.extend([
        "",
        "## Statistics",
        "",
        f"- **Average Speedup**: {avg_speedup:.2f}x",
        f"- **Maximum Speedup**: {max_speedup:.2f}x",
        f"- **Minimum Speedup**: {min_speedup:.2f}x",
        "",
        "### Legend",
        "",
        "- 🚀 Significant speedup (≥2.0x)",
        "- ⚡ Moderate speedup (≥1.2x)",
        "- ➖ Comparable performance (0.8-1.2x)",
        "- 🐌 Python faster (unusual, may indicate caching)",
        "",
        "## Details by Category",
        "",
    ])

    # Group by category
    categories = {
        "Directory Walking": [],
        "Pattern Matching": [],
        "End-to-End": [],
        "Comparison": [],
    }

    for name in sorted(common_names):
        rust = rust_benchmarks[name]
        python = python_benchmarks[name]

        if "walk" in name:
            category = "Directory Walking"
        elif "pattern" in name:
            category = "Pattern Matching"
        elif "scan" in name:
            category = "End-to-End"
        else:
            category = "Comparison"

        speedup = python["mean"] / rust["mean"]
        categories[category].append((name, rust, python, speedup))

    for category, items in categories.items():
        if not items:
            continue

        lines.extend([
            f"### {category}",
            "",
        ])

        for name, rust, python, speedup in items:
            display_name = name.replace("test_", "").replace("_", " ")
            lines.extend([
                f"**{display_name}**",
                f"- Python: {python['mean']*1000:.3f}ms ± {python['stddev']*1000:.3f}ms",
                f"- Rust: {rust['mean']*1000:.3f}ms ± {rust['stddev']*1000:.3f}ms",
                f"- Speedup: **{speedup:.2f}x**",
                "",
            ])

    lines.extend([
        "---",
        "",
        "*Benchmarks run with pytest-benchmark. Lower is better.*",
    ])

    return "\n".join(lines)


def generate_text_comparison(rust_data: Dict, python_data: Dict) -> str:
    """Generate plain text comparison (for terminal output)."""
    rust_benchmarks = {b["name"]: b for b in extract_benchmarks(rust_data)}
    python_benchmarks = {b["name"]: b for b in extract_benchmarks(python_data)}

    common_names = set(rust_benchmarks.keys()) & set(python_benchmarks.keys())

    if not common_names:
        return "No common benchmarks found."

    lines = [
        "=" * 80,
        "PERFORMANCE COMPARISON: Rust vs Python",
        "=" * 80,
        "",
    ]

    for name in sorted(common_names):
        rust = rust_benchmarks[name]
        python = python_benchmarks[name]

        speedup = python["mean"] / rust["mean"]

        display_name = name.replace("test_", "").replace("_", " ")

        lines.extend([
            f"{display_name}:",
            f"  Python: {python['mean']*1000:.3f}ms ± {python['stddev']*1000:.3f}ms",
            f"  Rust:   {rust['mean']*1000:.3f}ms ± {rust['stddev']*1000:.3f}ms",
            f"  Speedup: {speedup:.2f}x",
            "",
        ])

    lines.append("=" * 80)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Compare pytest-benchmark results and generate reports"
    )
    parser.add_argument("rust_json", help="Rust backend benchmark JSON file")
    parser.add_argument("python_json", help="Python backend benchmark JSON file")
    parser.add_argument(
        "--output-markdown",
        help="Output markdown file (for GitHub PR comments)",
    )
    parser.add_argument(
        "--output-text",
        help="Output text file (for terminal display)",
    )

    args = parser.parse_args()

    # Load data
    try:
        rust_data = load_benchmark_json(args.rust_json)
        python_data = load_benchmark_json(args.python_json)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}", file=sys.stderr)
        sys.exit(1)

    # Generate markdown output
    if args.output_markdown:
        markdown = generate_markdown_comparison(rust_data, python_data)
        with open(args.output_markdown, "w") as f:
            f.write(markdown)
        print(f"Markdown comparison saved to: {args.output_markdown}")

    # Generate text output
    if args.output_text:
        text = generate_text_comparison(rust_data, python_data)
        with open(args.output_text, "w") as f:
            f.write(text)
        print(f"Text comparison saved to: {args.output_text}")

    # If no output specified, print to stdout
    if not args.output_markdown and not args.output_text:
        print(generate_text_comparison(rust_data, python_data))


if __name__ == "__main__":
    main()
