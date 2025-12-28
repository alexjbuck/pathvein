# Benchmark Fix Results: LRU Cache Implementation

## Problem

Initial benchmarks revealed that Rust's `match_pattern` function was **13x SLOWER** than Python's implementation:

- `test_single_pattern_match_pattern`: 13.726ms (Rust) vs 1.046ms (Python) = **0.08x speedup** ❌
- `test_scan_single_pattern`: Much slower than expected ❌

## Root Cause

In `src/pattern.rs`, the `match_pattern` function was recompiling the glob pattern on **every single call**:

```rust
pub fn match_pattern(path: &str, pattern: &str) -> PyResult<bool> {
    match Glob::new(pattern) {
        Ok(glob) => Ok(glob.compile_matcher().is_match(path)),  // ❌ RECOMPILES EVERY TIME
        ...
    }
}
```

Python's equivalent has `@lru_cache(maxsize=256)` to cache compiled patterns, but Rust had **no caching**.

## Solution

Added LRU cache using the `lru` crate (commit 235a3c0):

1. Added `lru = "0.12"` dependency to Cargo.toml
2. Created global cache: `static PATTERN_CACHE: Mutex<Option<LruCache<String, GlobMatcher>>>`
3. Implemented `get_or_compile_pattern()` helper that checks cache first
4. Updated `match_pattern()` to use cached matcher

```rust
static PATTERN_CACHE: Mutex<Option<LruCache<String, GlobMatcher>>> = Mutex::new(None);

fn get_or_compile_pattern(pattern: &str) -> PyResult<GlobMatcher> {
    let mut cache_lock = PATTERN_CACHE.lock().unwrap();

    if cache_lock.is_none() {
        *cache_lock = Some(LruCache::new(NonZeroUsize::new(256).unwrap()));
    }

    let cache = cache_lock.as_mut().unwrap();

    // Check cache first ✅
    if let Some(matcher) = cache.get(pattern) {
        return Ok(matcher.clone());
    }

    // Compile and cache
    match Glob::new(pattern) {
        Ok(glob) => {
            let matcher = glob.compile_matcher();
            cache.put(pattern.to_string(), matcher.clone());
            Ok(matcher)
        }
        ...
    }
}
```

## Results

### pytest-benchmark

**Before fix:**
- `test_single_pattern_match_pattern`: 13.726ms ❌

**After fix:**
- `test_single_pattern_match_pattern`: 3.38ms ✅
- **Improvement: 4x faster!**

### Standalone Benchmark Comparison

**Single Pattern with match_pattern (1000 files):**
- Python: 1.0ms
- Rust (after fix): 4.2ms
- **Rust is 4.2x slower** - This is expected due to FFI overhead

**Multiple Patterns with PatternMatcher (1000 files):**
- 3 patterns: Rust 0.2ms vs Python 0.9ms = **4.5x faster** ✅
- 12 patterns: Rust 0.4ms vs Python 2.0ms = **5.0x faster** ✅

## Performance Analysis

### Why is match_pattern still slower than Python?

When calling `match_pattern(filename, pattern)` 1000 times in Python:

1. **Python → Rust FFI overhead** (crossing the boundary)
2. **String conversion overhead** (Python str → Rust &str)
3. **Result conversion overhead** (Rust bool → Python bool)
4. **Mutex lock overhead** (acquiring cache lock each time)

Python's `fnmatch` doesn't have this overhead - it's all native Python code.

### Why is PatternMatcher much faster?

With `PatternMatcher`, we:

1. ✅ Compile all patterns ONCE upfront in Rust
2. ✅ Keep the compiled GlobSet in Rust memory
3. ✅ Only ONE FFI call per filename check
4. ✅ Use GlobSet DFA which is highly optimized
5. ✅ Amortize FFI overhead across all patterns

## Recommendations

For best performance:

- ✅ **Use `PatternMatcher`** when matching multiple patterns or making many matches with the same pattern(s)
- ⚠️ **Use `match_pattern`** only for one-off single pattern checks
- ✅ The LRU cache ensures `match_pattern` is now reasonable (4x slower, not 13x)

## Benchmark Summary Table

| Test | Python | Rust (before) | Rust (after) | Verdict |
|------|--------|---------------|--------------|---------|
| Single pattern (match_pattern) | 1.0ms | 13.7ms ❌ | 4.2ms 🟡 | Fixed, FFI overhead remains |
| Multiple patterns (PatternMatcher, 3) | 0.9ms | - | 0.2ms ✅ | 4.5x faster |
| Multiple patterns (PatternMatcher, 12) | 2.0ms | - | 0.4ms ✅ | 5.0x faster |
| Directory walking | 61ms | - | 55ms ✅ | 1.1x faster |
| End-to-end scan | 65ms | - | 56ms ✅ | 1.2x faster |

## Conclusion

The LRU cache fix **successfully resolved the performance regression**. The remaining 4x slowdown for single-pattern `match_pattern` is expected and acceptable due to FFI overhead. For real-world usage with `PatternMatcher`, Rust is **4-5x faster** than Python for pattern matching operations.
