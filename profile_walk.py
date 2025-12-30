"""Quick profiling script to compare Python vs Rust walk performance"""
import os
import tempfile
import time
from pathlib import Path

# Create test directory
tmpdir = tempfile.mkdtemp()
test_dir = Path(tmpdir) / "test"
test_dir.mkdir()

# Small: 100 files
for i in range(100):
    (test_dir / f"file_{i}.txt").touch()

# Python os.walk
times = []
for _ in range(100):
    start = time.perf_counter()
    result = list(os.walk(test_dir))
    times.append(time.perf_counter() - start)
py_time = min(times) * 1000
print(f"Python os.walk (100 files): {py_time:.3f}ms")

# Rust walk_parallel
import pathvein._pathvein_rs as rs
times = []
for _ in range(100):
    start = time.perf_counter()
    result = rs.walk_parallel(str(test_dir))
    times.append(time.perf_counter() - start)
rust_time = min(times) * 1000
print(f"Rust walk_parallel (100 files): {rust_time:.3f}ms")

print(f"Speedup: {py_time/rust_time:.2f}x")

# Cleanup
import shutil
shutil.rmtree(tmpdir)
