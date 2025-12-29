---
"pathvein": minor
---

Integrate Rust backend into core library for real-world performance gains

**Breaking Behavior Changes:**
- Library now uses Rust-backed `walk_parallel()` for directory traversal when available
- Pattern matching uses Rust `PatternMatcher` and `match_pattern()` for 4-7x speedup
- All scan and copy operations now leverage Rust optimizations automatically

**Performance Improvements:**
- Directory walking: 1.1-1.6x faster with parallel Rust implementation
- Pattern matching with PatternMatcher: 4-7x faster for multiple patterns
- Pattern matching (single): Fixed 13x regression with LRU cache, now 4x slower than Python due to FFI (use PatternMatcher instead)
- End-to-end scans: 1.5-2x faster overall
- File copy operations: Now use optimized pattern matching

**Bug Fixes:**
- Fixed scan_single_pattern benchmark to use PatternMatcher (21% improvement)
- Added LRU cache to Rust match_pattern to fix 13x performance regression

**API Compatibility:**
- Automatic fallback to pure Python when Rust backend unavailable
- No breaking API changes - all public interfaces remain the same
- Internal implementation migrated from `_path_utils.walk()` to `_backend.walk_parallel()`
- Internal implementation migrated from `_path_utils.pattern_match()` to `_backend.match_pattern()`

**Developer Experience:**
- Comprehensive benchmark suite with Python/Rust comparison
- Updated benchmarks to reflect actual library usage patterns
- Benchmark workflow now updates existing PR comments instead of spamming new ones
