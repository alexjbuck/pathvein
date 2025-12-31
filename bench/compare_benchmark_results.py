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


def categorize_benchmark(name: str) -> tuple[str, Optional[str]]:
    """
    Categorize benchmark by type and approach.

    Returns: (category, approach)
    - category: "api" or "micro"
    - approach: "pure_python", "hybrid", "pure_rust", or None (for non-comparison benchmarks)
    """
    # Main 3-way comparison benchmarks (CLEARLY NAMED)
    if "test_api_scan_1_pure_python" in name:
        return ("api", "pure_python")
    elif "test_api_scan_2_hybrid" in name:
        return ("api", "hybrid")
    elif "test_api_scan_3_pure_rust" in name:
        return ("api", "pure_rust")
    # Other API benchmarks (not part of main comparison)
    elif "test_api" in name:
        return ("api", None)
    # Micro benchmarks
    elif "test_micro" in name:
        return ("micro", None)
    else:
        return ("other", None)


def generate_markdown_comparison(data: Dict) -> str:
    """Generate markdown comparison showing Pure Python vs Hybrid vs Pure Rust."""
    benchmarks = {b["name"]: b for b in extract_benchmarks(data)}

    # Find the three main scan benchmarks
    pure_python = None
    hybrid = None
    pure_rust = None

    for name, bench in benchmarks.items():
        cat, approach = categorize_benchmark(name)
        if approach == "pure_python":
            pure_python = bench
        elif approach == "hybrid":
            hybrid = bench
        elif approach == "pure_rust":
            pure_rust = bench

    lines = [
        "# 🚀 Pathvein Performance: Pure Python vs Hybrid vs Pure Rust",
        "",
        "## Main Scan Comparison (3 Approaches)",
        "",
        "This compares **3 different scan implementations** to answer: **Is Rust worth it?**",
        "",
        "1. **Approach #1 - Pure Python**: `os.walk()` + Python `fnmatch` (baseline, no Rust)",
        "2. **Approach #2 - Hybrid**: Python `os.walk()` + Rust matchers (fast matching only)",
        "3. **Approach #3 - Pure Rust**: Everything in Rust, precompiled patterns (optimal)",
        "",
    ]

    if not all([pure_python, hybrid, pure_rust]):
        lines.append("⚠️ **Warning**: Not all three scan benchmarks found in results.")
        lines.append("")
        lines.append(f"- Pure Python: {'✓' if pure_python else '✗'}")
        lines.append(f"- Hybrid: {'✓' if hybrid else '✗'}")
        lines.append(f"- Pure Rust: {'✓' if pure_rust else '✗'}")
        return "\n".join(lines)

    # Main comparison table
    lines.extend(
        [
            "| Approach | Time (ms) | Speedup vs #1 | Speedup vs #2 | Status |",
            "|----------|-----------|---------------|---------------|--------|",
        ]
    )

    pp_ms = pure_python["mean"] * 1000
    hybrid_ms = hybrid["mean"] * 1000
    rust_ms = pure_rust["mean"] * 1000

    # Row 1: Pure Python
    lines.append(f"| #1 Pure Python | {pp_ms:.3f} | 1.00x (baseline) | — | 📊 |")

    # Row 2: Hybrid
    hybrid_speedup_vs_python = pure_python["mean"] / hybrid["mean"]
    if hybrid_speedup_vs_python >= 1.2:
        hybrid_emoji = "⚡"
    elif hybrid_speedup_vs_python >= 0.8:
        hybrid_emoji = "➖"
    else:
        hybrid_emoji = "🐌"

    lines.append(
        f"| #2 Hybrid | {hybrid_ms:.3f} | {hybrid_speedup_vs_python:.2f}x | 1.00x | {hybrid_emoji} |"
    )

    # Row 3: Pure Rust
    rust_speedup_vs_python = pure_python["mean"] / pure_rust["mean"]
    rust_speedup_vs_hybrid = hybrid["mean"] / pure_rust["mean"]

    if rust_speedup_vs_python >= 2.0:
        rust_emoji = "🚀"
    elif rust_speedup_vs_python >= 1.2:
        rust_emoji = "⚡"
    elif rust_speedup_vs_python >= 0.8:
        rust_emoji = "➖"
    else:
        rust_emoji = "🐌"

    lines.append(
        f"| #3 Pure Rust | {rust_ms:.3f} | {rust_speedup_vs_python:.2f}x | "
        f"{rust_speedup_vs_hybrid:.2f}x | {rust_emoji} |"
    )

    lines.extend(
        [
            "",
            "### Key Insights",
            "",
            f"- **Hybrid vs Pure Python**: {hybrid_speedup_vs_python:.2f}x speedup "
            f"({abs(hybrid_speedup_vs_python - 1.0) * 100:.1f}% {'faster' if hybrid_speedup_vs_python > 1 else 'slower'})",
            f"- **Pure Rust vs Pure Python**: {rust_speedup_vs_python:.2f}x speedup "
            f"({abs(rust_speedup_vs_python - 1.0) * 100:.1f}% {'faster' if rust_speedup_vs_python > 1 else 'slower'})",
            f"- **Pure Rust vs Hybrid**: {rust_speedup_vs_hybrid:.2f}x speedup "
            f"({abs(rust_speedup_vs_hybrid - 1.0) * 100:.1f}% {'faster' if rust_speedup_vs_hybrid > 1 else 'slower'})",
            "",
        ]
    )

    # Verdict
    if rust_speedup_vs_python >= 2.0:
        verdict = "🎉 **Rust is definitely worth it!** Pure Rust implementation is ≥2x faster."
    elif rust_speedup_vs_python >= 1.5:
        verdict = "✅ **Rust is worth it.** Pure Rust provides significant speedup."
    elif rust_speedup_vs_python >= 1.2:
        verdict = "👍 **Rust provides moderate improvement.** Worth keeping if FFI complexity is manageable."
    elif rust_speedup_vs_python >= 0.8:
        verdict = "⚠️ **Rust provides minimal benefit.** Consider if added complexity is worth it."
    else:
        verdict = "❌ **Rust is slower!** Something is wrong with the implementation."

    lines.extend(
        [
            "### Verdict",
            "",
            verdict,
            "",
        ]
    )

    # Other benchmarks
    lines.extend(
        [
            "## Other Benchmarks",
            "",
            "| Benchmark | Time (ms) | Type |",
            "|-----------|-----------|------|",
        ]
    )

    for name in sorted(benchmarks.keys()):
        cat, approach = categorize_benchmark(name)
        # Skip the three main comparison benchmarks we already showed
        if approach in ["pure_python", "hybrid", "pure_rust"]:
            continue

        bench = benchmarks[name]
        display_name = name.replace("test_", "").replace("_", " ").title()
        time_ms = bench["mean"] * 1000
        bench_type = "🔬 Micro" if cat == "micro" else "📦 API"

        lines.append(f"| {display_name} | {time_ms:.3f} | {bench_type} |")

    lines.extend(
        [
            "",
            "### Legend",
            "",
            "- 🚀 Significant speedup (≥2.0x)",
            "- ⚡ Moderate speedup (≥1.2x)",
            "- ➖ Comparable performance (0.8-1.2x)",
            "- 🐌 Slower (unusual, may indicate issue)",
            "- 📊 Baseline (Pure Python)",
            "- 🔬 Micro benchmark (internal implementation)",
            "- 📦 API benchmark (user-facing function)",
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

    # Find the three main scan benchmarks
    pure_python = None
    hybrid = None
    pure_rust = None

    for name, bench in benchmarks.items():
        cat, approach = categorize_benchmark(name)
        if approach == "pure_python":
            pure_python = bench
        elif approach == "hybrid":
            hybrid = bench
        elif approach == "pure_rust":
            pure_rust = bench

    lines = [
        "=" * 80,
        "PERFORMANCE COMPARISON: Pure Python vs Hybrid vs Pure Rust",
        "=" * 80,
        "",
    ]

    if not all([pure_python, hybrid, pure_rust]):
        lines.append("Warning: Not all three scan benchmarks found")
        return "\n".join(lines)

    pp_ms = pure_python["mean"] * 1000
    hybrid_ms = hybrid["mean"] * 1000
    rust_ms = pure_rust["mean"] * 1000

    hybrid_speedup = pure_python["mean"] / hybrid["mean"]
    rust_speedup_vs_python = pure_python["mean"] / pure_rust["mean"]
    rust_speedup_vs_hybrid = hybrid["mean"] / pure_rust["mean"]

    lines.extend(
        [
            "Scan Performance:",
            f"  Pure Python:  {pp_ms:.3f}ms (baseline)",
            f"  Hybrid:       {hybrid_ms:.3f}ms ({hybrid_speedup:.2f}x vs Python)",
            f"  Pure Rust:    {rust_ms:.3f}ms ({rust_speedup_vs_python:.2f}x vs Python, "
            f"{rust_speedup_vs_hybrid:.2f}x vs Hybrid)",
            "",
        ]
    )

    if rust_speedup_vs_python >= 2.0:
        lines.append("Verdict: Pure Rust is definitely worth it! (≥2x speedup)")
    elif rust_speedup_vs_python >= 1.5:
        lines.append("Verdict: Pure Rust provides significant speedup")
    elif rust_speedup_vs_python >= 1.2:
        lines.append("Verdict: Pure Rust provides moderate improvement")
    else:
        lines.append("Verdict: Pure Rust provides minimal or no benefit")

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
