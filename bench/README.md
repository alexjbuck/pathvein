# Pathvein Performance Benchmarks

This directory contains benchmarks for comparing the Python-only and Rust-backed implementations of pathvein.

## Overview

Pathvein has two backends:
- **Rust backend**: Uses PyO3 bindings for high-performance directory walking and pattern matching (5-10x faster)
- **Python backend**: Pure Python fallback using `os.walk()` and `fnmatch`

The backend is automatically selected at import time. The Rust backend is used if the `_pathvein_rs` extension module is available.

## Quick Start

### Run benchmark with your current installation:

```bash
cd bench
python benchmark_backends.py
```

This will:
- Detect which backend is currently active
- Run comprehensive benchmarks
- Save results to `benchmark_results_rust.json` or `benchmark_results_python.json`

## Comparing Rust vs Python Backends

To properly compare the two backends, you need to run the benchmark twice: once with each backend.

### Method 1: Using Virtual Environments (Recommended)

#### Step 1: Benchmark with Rust backend

```bash
# From the repository root
python -m venv venv_rust
source venv_rust/bin/activate  # On Windows: venv_rust\Scripts\activate

# Install normally (includes Rust backend if Rust is available)
pip install -e .

# Run benchmark
cd bench
python benchmark_backends.py -o rust_results.json
deactivate
```

#### Step 2: Benchmark with Python-only backend

```bash
# Create a new venv for Python-only testing
python -m venv venv_python
source venv_python/bin/activate  # On Windows: venv_python\Scripts\activate

# Build and install from sdist (pure Python)
# This works because maturin will skip Rust compilation if cargo/rustc is not found
pip install build
cd ..  # Return to repo root

# Build source distribution
python -m build --sdist

# Install from the sdist in an environment without Rust
# If Rust is not available, maturin will build a Python-only version
pip install dist/pathvein-*.tar.gz --force-reinstall --no-cache-dir

# Verify Python backend is active
python -c "from pathvein._backend import get_backend_info; print(get_backend_info())"
# Should show: {'backend': 'python', 'has_rust': False, 'rust_version': None}

# Run benchmark
cd bench
python benchmark_backends.py -o python_results.json
deactivate
```

#### Step 3: Compare results

```bash
# From any environment with the script
python benchmark_backends.py --compare python_results.json rust_results.json
```

### Method 2: Using Conditional Import

Alternatively, you can temporarily disable the Rust backend by modifying `src/pathvein/_backend.py`:

```python
# Change this line:
HAS_RUST_BACKEND = _try_import_rust()

# To this:
HAS_RUST_BACKEND = False  # Force Python backend
```

Then reinstall and run benchmarks.

## Building Pure Python Version

### Understanding the Build Process

Pathvein uses [Maturin](https://github.com/PyO3/maturin) as its build backend. Maturin has special behavior when Rust is not available:

1. **Normal build** (`pip install .` or `pip install -e .`): Compiles Rust extensions if cargo/rustc is found
2. **sdist build** (`python -m build --sdist`): Creates a source distribution
3. **Installing from sdist without Rust**: Maturin detects missing Rust toolchain and creates a Python-only wheel

### To force a Python-only build:

```bash
# Option 1: Install in environment without Rust toolchain
# Unset Rust environment (temporary for this shell)
unset CARGO
unset RUSTC

pip install --no-binary pathvein pathvein

# Option 2: Build sdist and install it
python -m build --sdist
pip install dist/pathvein-*.tar.gz --force-reinstall
```

### Verifying the Backend

Always verify which backend is active:

```bash
python -c "from pathvein._backend import get_backend_info; import json; print(json.dumps(get_backend_info(), indent=2))"
```

Expected output with Rust:
```json
{
  "backend": "rust",
  "has_rust": true,
  "rust_version": "0.1.0"
}
```

Expected output without Rust:
```json
{
  "backend": "python",
  "has_rust": false,
  "rust_version": null
}
```

## Benchmark Operations

The benchmark suite tests the following operations:

### 1. Directory Walking
- Small tree (2 levels, ~100 files)
- Medium tree (3 levels, ~1000 files)
- Large tree (4 levels, ~10000 files)

Tests the `walk()` function which uses:
- **Rust**: `walkdir` + `rayon` for parallel traversal
- **Python**: `os.walk()` with sequential traversal

### 2. Pattern Matching
- Single simple pattern (`*.py`)
- Single complex pattern (`test_*.{py,rs,md}`)
- Multiple patterns (3 patterns)
- Many patterns (12 patterns)
- Repeated matching (cache effectiveness)

Tests pattern matching which uses:
- **Rust**: `globset` with pre-compiled DFA matchers
- **Python**: `fnmatch` with LRU cache

### 3. End-to-End Scanning
- Small/medium/large trees with various patterns
- Complex glob patterns
- Pattern exclusions

Tests the high-level `scan()` API which combines walking + matching.

### 4. Real Repository
- Scans the actual pathvein repository
- Real-world file structure and patterns
- Practical performance measurement

## Benchmark Options

```bash
# Basic run (auto-detects backend)
python benchmark_backends.py

# Save to specific file
python benchmark_backends.py -o my_results.json

# Skip real repository benchmark (faster, uses only synthetic data)
python benchmark_backends.py --skip-real

# Compare two result files
python benchmark_backends.py --compare rust_results.json python_results.json

# Show help
python benchmark_backends.py --help
```

## Expected Performance Differences

Based on the codebase documentation:

| Operation | Expected Speedup (Rust vs Python) |
|-----------|----------------------------------|
| Directory Walking | 5-10x faster |
| Pattern Matching | 3-5x faster |
| End-to-End Scan | 4-8x faster (combined effect) |

Actual results will vary based on:
- Directory structure (depth vs breadth)
- Number and complexity of patterns
- File system characteristics
- Cache effects (Python's LRU cache vs Rust's compiled patterns)

## Troubleshooting

### "Cannot find Rust backend but Python backend also failing"

The Python fallback should always work. If both backends fail:
1. Check that pathvein is properly installed: `pip list | grep pathvein`
2. Try reinstalling: `pip install --force-reinstall pathvein`

### "Getting Rust backend when I want Python-only"

The Rust backend is preferred if available. To force Python:
1. Create a fresh venv without Rust toolchain
2. Or temporarily rename `_pathvein_rs.so` in your site-packages
3. Or modify `_backend.py` to force `HAS_RUST_BACKEND = False`

### "sdist build is still compiling Rust"

This means Rust toolchain is available. To build Python-only:
1. Use a system/container without Rust installed
2. Or temporarily rename `~/.cargo` to hide the Rust toolchain
3. Or set environment variable: `export CARGO_BUILD_TARGET=""`

### "Benchmark results are inconsistent"

Performance benchmarks can vary due to:
- File system caching
- System load
- Python's JIT warmup
- Run the benchmark multiple times and average results
- Close other applications during benchmarking

## Integration with CI/CD

To track performance regressions:

```bash
# In CI, run both benchmarks and compare
python benchmark_backends.py -o ci_results.json

# Compare against baseline
python benchmark_backends.py --compare baseline_results.json ci_results.json

# Fail if performance regresses by >10%
python check_regression.py baseline_results.json ci_results.json --threshold 0.1
```

## Contributing

When adding new features or optimizations:

1. Run benchmarks before changes (baseline)
2. Make your changes
3. Run benchmarks after changes
4. Compare results to verify improvement
5. Include benchmark results in PR description

## Additional Resources

- [Maturin Documentation](https://www.maturin.rs/)
- [PyO3 Documentation](https://pyo3.rs/)
- [Python Performance Tips](https://wiki.python.org/moin/PythonSpeed/PerformanceTips)
