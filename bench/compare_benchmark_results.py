#!/usr/bin/env python3
"""
Compare pytest-benchmark JSON results and generate markdown report.

This script generates a 3-way comparison showing:
- Pure Python: No Rust (baseline)
- Hybrid: Rust walk + Python matching (FFI overhead)
- Pure Rust: Everything in Rust (should be fastest)

Usage:
    python compare_benchmark_results.py benchmarks.json --output-markdown=comparison.md
"""

import argparse
import json
import sys
from typing import Dict, List, Any, Optional


def load_benchmark_json(filepath: str) -> Dict[str, Any]:
    """Load a pytest-benchmark JSON file."""
    with open(filepath) as f:
        return json.load(f)


def extract_benchmarks(data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract benchmark results from pytest-benchmark JSON."""
    benchmarks = []
    for bench in data.get("benchmarks", []):
        benchmarks.append(
            {
                "name": bench["name"],
                "fullname": bench["fullname"],
                "mean": bench["stats"]["mean"],
                "stddev": bench["stats"]["stddev"],
                "median": bench["stats"]["median"],
                "min": bench["stats"]["min"],
                "max": bench["stats"]["max"],
                "rounds": bench["stats"]["rounds"],
            }
        )
    return benchmarks


def categorize_benchmark(name: str) -> tuple[str, Optional[str], Optional[int]]:
    """
    Categorize benchmark by type, approach, and scenario.

    Returns: (category, approach, scenario)
    - category: "api" or "micro"
    - approach: "pure_python", "hybrid", "pure_rust", or None
    - scenario: 1, 2, 3, 4, or None
    """
    # Scenario benchmarks (4 scenarios × 3 approaches)
    if "scenario1" in name:
        if "1_pure_python" in name:
            return ("scenario", "pure_python", 1)
        elif "2_hybrid" in name:
            return ("scenario", "hybrid", 1)
        elif "3_pure_rust" in name:
            return ("scenario", "pure_rust", 1)
    elif "scenario2" in name:
        if "1_pure_python" in name:
            return ("scenario", "pure_python", 2)
        elif "2_hybrid" in name:
            return ("scenario", "hybrid", 2)
        elif "3_pure_rust" in name:
            return ("scenario", "pure_rust", 2)
    elif "scenario3" in name:
        if "1_pure_python" in name:
            return ("scenario", "pure_python", 3)
        elif "2_hybrid" in name:
            return ("scenario", "hybrid", 3)
        elif "3_pure_rust" in name:
            return ("scenario", "pure_rust", 3)
    elif "scenario4" in name:
        if "1_pure_python" in name:
            return ("scenario", "pure_python", 4)
        elif "2_hybrid" in name:
            return ("scenario", "hybrid", 4)
        elif "3_pure_rust" in name:
            return ("scenario", "pure_rust", 4)
    # Other API benchmarks (not part of scenario comparison)
    elif "test_api" in name:
        return ("api", None, None)
    # Micro benchmarks
    elif "test_micro" in name:
        return ("micro", None, None)
    else:
        return ("other", None, None)


def generate_markdown_comparison(data: Dict) -> str:
    """Generate markdown comparison showing 3 methods across 4 scenarios."""
    benchmarks = {b["name"]: b for b in extract_benchmarks(data)}

    # Organize scenario benchmarks by scenario and approach
    scenarios = {
        1: {},  # Small dir + 1 simple pattern
        2: {},  # Small dir + 8 patterns
        3: {},  # Large dir + 1 simple pattern
        4: {},  # Large dir + 5 complex patterns
    }

    # Categorize all benchmarks
    micro_benchmarks = []
    api_benchmarks = []

    for name, bench in benchmarks.items():
        cat, approach, scenario = categorize_benchmark(name)
        if cat == "scenario" and scenario is not None:
            scenarios[scenario][approach] = bench
        elif cat == "micro":
            micro_benchmarks.append((name, bench))
        elif cat == "api":
            api_benchmarks.append((name, bench))

    lines = [
        "# 🚀 Pathvein Performance Benchmarks",
        "",
        "## Scan API: 3 Methods Across 4 Scenarios",
        "",
        "Comparing **3 different scan implementations**:",
        "",
        "1. **Pure Python**: `os.walk()` + Python `fnmatch` (baseline, no Rust)",
        "2. **Hybrid**: Python `os.walk()` + Rust pattern matching",
        "3. **Pure Rust**: Everything in Rust, precompiled patterns (optimal)",
        "",
    ]

    # Check if we have all scenario data
    missing_scenarios = []
    for scenario_num in [1, 2, 3, 4]:
        if len(scenarios[scenario_num]) != 3:
            missing_scenarios.append(scenario_num)

    if missing_scenarios:
        lines.append(f"⚠️ **Warning**: Missing data for scenarios: {missing_scenarios}")
        lines.append("")

    # Scenario descriptions
    scenario_descriptions = {
        1: "Small dir (~140 files) + 1 simple pattern",
        2: "Small dir (~140 files) + 8 patterns",
        3: "Large dir (~31,250 files) + 1 simple pattern",
        4: "Large dir (~31,250 files) + 5 complex patterns",
    }

    # Generate table for each scenario
    lines.extend(
        [
            "| Scenario | Pure Python (ms) | Hybrid (ms) | Pure Rust (ms) | Rust vs Python | Status |",
            "|----------|------------------|-------------|----------------|----------------|--------|",
        ]
    )

    for scenario_num in [1, 2, 3, 4]:
        scenario_data = scenarios[scenario_num]
        if len(scenario_data) != 3:
            continue  # Skip incomplete scenarios

        pp = scenario_data.get("pure_python")
        hybrid = scenario_data.get("hybrid")
        rust = scenario_data.get("pure_rust")

        if not all([pp, hybrid, rust]):
            continue

        pp_ms = pp["mean"] * 1000
        hybrid_ms = hybrid["mean"] * 1000
        rust_ms = rust["mean"] * 1000

        # Calculate speedup
        speedup = pp["mean"] / rust["mean"]

        # Status emoji
        if speedup >= 2.0:
            status = "🚀"
        elif speedup >= 1.5:
            status = "⚡"
        elif speedup >= 1.2:
            status = "👍"
        elif speedup >= 0.8:
            status = "➖"
        else:
            status = "🐌"

        desc = scenario_descriptions[scenario_num]
        lines.append(
            f"| **{scenario_num}**: {desc} | {pp_ms:.1f} | {hybrid_ms:.1f} | {rust_ms:.1f} | {speedup:.2f}x | {status} |"
        )

    lines.extend(
        [
            "",
            "### Summary",
            "",
        ]
    )

    # Calculate average speedup across all scenarios
    total_speedup = 0
    count = 0
    for scenario_num in [1, 2, 3, 4]:
        scenario_data = scenarios[scenario_num]
        if len(scenario_data) == 3:
            pp = scenario_data["pure_python"]
            rust = scenario_data["pure_rust"]
            total_speedup += pp["mean"] / rust["mean"]
            count += 1

    if count > 0:
        avg_speedup = total_speedup / count
        lines.append(
            f"- **Average Rust speedup**: {avg_speedup:.2f}x across {count} scenarios"
        )

        if avg_speedup >= 2.0:
            verdict = "🎉 **Pure Rust is definitely worth it!** Consistent ≥2x speedup."
        elif avg_speedup >= 1.5:
            verdict = (
                "✅ **Pure Rust provides significant speedup** across all scenarios."
            )
        elif avg_speedup >= 1.2:
            verdict = (
                "👍 **Pure Rust provides moderate improvement** across all scenarios."
            )
        else:
            verdict = "⚠️ **Pure Rust provides minimal benefit** - consider complexity trade-offs."

        lines.append(f"- {verdict}")

    lines.append("")

    # Micro benchmarks section
    if micro_benchmarks:
        lines.extend(
            [
                "## Micro Benchmarks",
                "",
                "Low-level component benchmarks:",
                "",
                "| Benchmark | Time (ms) | Description |",
                "|-----------|-----------|-------------|",
            ]
        )

        for name, bench in sorted(micro_benchmarks, key=lambda x: x[1]["mean"]):
            time_ms = bench["mean"] * 1000

            # Generate description
            if "walk_parallel" in name:
                desc = "Parallel directory walking"
            elif "pattern_matching_multiple" in name:
                desc = "Multiple pattern matching"
            elif "pattern_matching_single" in name:
                desc = "Single pattern matching"
            else:
                desc = name.replace("test_micro_", "").replace("_", " ").title()

            lines.append(f"| {desc} | {time_ms:.3f} | Rust implementation |")

        lines.append("")

    # Other API benchmarks section
    if api_benchmarks:
        lines.extend(
            [
                "## Other API Benchmarks",
                "",
                "| Benchmark | Time (ms) |",
                "|-----------|-----------|",
            ]
        )

        for name, bench in sorted(api_benchmarks, key=lambda x: x[1]["mean"]):
            time_ms = bench["mean"] * 1000
            display_name = name.replace("test_api_", "").replace("_", " ").title()
            lines.append(f"| {display_name} | {time_ms:.3f} |")

        lines.append("")

    lines.extend(
        [
            "### Legend",
            "",
            "- 🚀 Excellent speedup (≥2.0x)",
            "- ⚡ Good speedup (≥1.5x)",
            "- 👍 Moderate speedup (≥1.2x)",
            "- ➖ Comparable (0.8-1.2x)",
            "- 🐌 Slower (investigation needed)",
            "",
            "---",
            "",
            "*Benchmarks run with pytest-benchmark. Lower time is better.*",
        ]
    )

    return "\n".join(lines)


def generate_text_comparison(data: Dict) -> str:
    """Generate plain text comparison (for terminal output)."""
    benchmarks = {b["name"]: b for b in extract_benchmarks(data)}

    # Organize scenario benchmarks
    scenarios = {1: {}, 2: {}, 3: {}, 4: {}}

    for name, bench in benchmarks.items():
        cat, approach, scenario = categorize_benchmark(name)
        if cat == "scenario" and scenario is not None:
            scenarios[scenario][approach] = bench

    lines = [
        "=" * 80,
        "PATHVEIN PERFORMANCE BENCHMARKS",
        "=" * 80,
        "",
        "Scan API: 3 Methods Across 4 Scenarios",
        "",
    ]

    scenario_descriptions = {
        1: "Small dir (~140 files) + 1 simple pattern",
        2: "Small dir (~140 files) + 8 patterns",
        3: "Large dir (~31,250 files) + 1 simple pattern",
        4: "Large dir (~31,250 files) + 5 complex patterns",
    }

    total_speedup = 0
    count = 0

    for scenario_num in [1, 2, 3, 4]:
        scenario_data = scenarios[scenario_num]
        if len(scenario_data) != 3:
            continue

        pp = scenario_data.get("pure_python")
        hybrid = scenario_data.get("hybrid")
        rust = scenario_data.get("pure_rust")

        if not all([pp, hybrid, rust]):
            continue

        pp_ms = pp["mean"] * 1000
        hybrid_ms = hybrid["mean"] * 1000
        rust_ms = rust["mean"] * 1000
        speedup = pp["mean"] / rust["mean"]

        total_speedup += speedup
        count += 1

        lines.extend(
            [
                f"Scenario {scenario_num}: {scenario_descriptions[scenario_num]}",
                f"  Pure Python: {pp_ms:.1f}ms",
                f"  Hybrid:      {hybrid_ms:.1f}ms",
                f"  Pure Rust:   {rust_ms:.1f}ms ({speedup:.2f}x speedup)",
                "",
            ]
        )

    if count > 0:
        avg_speedup = total_speedup / count
        lines.extend(
            [
                f"Average Rust speedup: {avg_speedup:.2f}x across {count} scenarios",
                "",
            ]
        )

        if avg_speedup >= 2.0:
            lines.append("Verdict: Pure Rust is definitely worth it! (≥2x speedup)")
        elif avg_speedup >= 1.5:
            lines.append("Verdict: Pure Rust provides significant speedup")
        elif avg_speedup >= 1.2:
            lines.append("Verdict: Pure Rust provides moderate improvement")
        else:
            lines.append("Verdict: Pure Rust provides minimal benefit")

    lines.append("")
    lines.append("=" * 80)
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Compare pytest-benchmark results showing Pure Python vs Hybrid vs Pure Rust"
    )
    parser.add_argument(
        "benchmark_json", help="Benchmark JSON file with all three approaches"
    )
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
        data = load_benchmark_json(args.benchmark_json)
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}", file=sys.stderr)
        sys.exit(1)

    # Generate markdown output
    if args.output_markdown:
        markdown = generate_markdown_comparison(data)
        with open(args.output_markdown, "w") as f:
            f.write(markdown)
        print(f"Markdown comparison saved to: {args.output_markdown}")

    # Generate text output
    if args.output_text:
        text = generate_text_comparison(data)
        with open(args.output_text, "w") as f:
            f.write(text)
        print(f"Text comparison saved to: {args.output_text}")

    # If no output specified, print to stdout
    if not args.output_markdown and not args.output_text:
        print(generate_text_comparison(data))


if __name__ == "__main__":
    main()
