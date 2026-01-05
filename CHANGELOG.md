# pathvein

## 0.10.0

### Minor Changes

- [#67](https://github.com/alexjbuck/pathvein/pull/67) [`0decdea`](https://github.com/alexjbuck/pathvein/commit/0decdea8589fe1a8918391b7f9b352e356ca812c) Thanks [@alexjbuck](https://github.com/alexjbuck)! - Major performance improvements and quality enhancements

  **Performance Improvements:**

  - Replace `path.iterdir()` with `os.scandir()` for 2-3x faster directory listing
  - Add pre-compiled pattern matching with LRU cache (10-20% faster)
  - Expose threaded copy operations via `use_threading` parameter
  - Bound LRU cache to prevent memory leaks (maxsize=10000)
  - Add optional Rust backend with maturin for 5-10x performance boost

  **Rust Backend:**

  - Parallel directory walking using walkdir + rayon
  - Compiled glob matching using globset (3-5x faster)
  - Automatic fallback to pure Python when Rust not available
  - Cross-platform support with graceful degradation

  **Bug Fixes:**

  - Fix missing API exports (`shuffle_to`, `shuffle_with`)
  - Add comprehensive JSON error handling with clear messages
  - Fix logging bugs (typo and missing parameters)
  - Fix CLI import error without `[cli]` extra
  - Make log file path configurable and cross-platform

  **API Improvements:**

  - Properly separate library and CLI with `[cli]` extra
  - Add `get_backend_info()` to check active backend
  - Document `assess()` function with examples
  - Add type hints (chunk_size parameter)
  - Improve docstrings with comprehensive examples

  **Testing:**

  - Add comprehensive CLI test suite (23 tests)
  - Tests for scan and shuffle commands
  - Tests for error handling and edge cases

  **Documentation:**

  - Document Rust backend with build instructions
  - Add pattern assessment examples
  - Improve README with installation options
  - Add IMPROVEMENTS.md tracking future enhancements

- [#68](https://github.com/alexjbuck/pathvein/pull/68) [`419cd40`](https://github.com/alexjbuck/pathvein/commit/419cd40a8a57beb3f913fffba1b976f4c5d69407) Thanks [@alexjbuck](https://github.com/alexjbuck)! - Integrate Rust backend into core library for real-world performance gains

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
  - **Cloud storage support preserved** - detects path type and uses appropriate walker:
    - Local `Path` objects → Rust `walk_parallel()` for performance
    - Cloud/UPath objects (S3, Azure, GCS) → Python `walk()` for compatibility
  - Internal pattern matching migrated to `_backend.match_pattern()` and `PatternMatcher`

  **Developer Experience:**

  - Comprehensive benchmark suite with Python/Rust comparison
  - Updated benchmarks to reflect actual library usage patterns
  - Benchmark workflow now updates existing PR comments instead of spamming new ones

### Patch Changes

- [#69](https://github.com/alexjbuck/pathvein/pull/69) [`ec36ceb`](https://github.com/alexjbuck/pathvein/commit/ec36ceb98ae2fbc3bf25768ea28b2ed9c5db7544) Thanks [@alexjbuck](https://github.com/alexjbuck)! - Add comprehensive documentation site with MkDocs

  - Set up MkDocs with Material theme for modern documentation
  - Add mkdocstrings for automatic API documentation from docstrings
  - Configure mike for versioned documentation (supports main/nightly + release versions)
  - Create comprehensive user guides for patterns, scanning, and shuffling
  - Add full API reference with auto-generated docs from Python and Rust docstrings
  - Integrate documentation deployment into changesets release workflow
  - Deploy latest docs on push to main, versioned docs on release

- [#71](https://github.com/alexjbuck/pathvein/pull/71) [`9449317`](https://github.com/alexjbuck/pathvein/commit/944931734714e01de38c76938df7129672efbca7) Thanks [@alexjbuck](https://github.com/alexjbuck)! - Fix test failure: filter out special directory names from test strategies

  - Update valid_name_strategy to exclude '.' and '..' as complete filenames
  - Prevents Hypothesis from generating invalid filesystem references in tests
  - Resolves IsADirectoryError when tests attempted to create files with these reserved names

- [#48](https://github.com/alexjbuck/pathvein/pull/48) [`c0a779c`](https://github.com/alexjbuck/pathvein/commit/c0a779caf42a3422306aaf28773858df3acd63b4) Thanks [@alexjbuck](https://github.com/alexjbuck)! - Add Cursor rules for project documentation and code style

  - Add project overview rule with repository structure and workflow
  - Add Python code style guide with modern Python practices
  - Add framework for learning from errors and building new rules

- [#48](https://github.com/alexjbuck/pathvein/pull/48) [`c0a779c`](https://github.com/alexjbuck/pathvein/commit/c0a779caf42a3422306aaf28773858df3acd63b4) Thanks [@alexjbuck](https://github.com/alexjbuck)! - Add Cursor rule for proper changeset creation

  - Add detailed guidelines for creating changesets
  - Include examples for both monorepo and monolithic scenarios
  - Document best practices and file naming conventions

- [#74](https://github.com/alexjbuck/pathvein/pull/74) [`b8477c9`](https://github.com/alexjbuck/pathvein/commit/b8477c909196bbe71f8de37c0aae2dffffcc4378) Thanks [@alexjbuck](https://github.com/alexjbuck)! - Show help by default when running `pathvein` without arguments

  - Add `no_args_is_help=True` to Typer CLI
  - Migrate dev dependencies from deprecated `tool.uv.dev-dependencies` to `dependency-groups.dev`

- [#48](https://github.com/alexjbuck/pathvein/pull/48) [`c0a779c`](https://github.com/alexjbuck/pathvein/commit/c0a779caf42a3422306aaf28773858df3acd63b4) Thanks [@alexjbuck](https://github.com/alexjbuck)! - Move package to src/ directory structure
  - Relocate pathvein package to src/pathvein/
  - Update package configuration files
  - Add bench package initialization

## 0.9.0

### Minor Changes

- [#43](https://github.com/alexjbuck/pathvein/pull/43) [`fbabb50`](https://github.com/alexjbuck/pathvein/commit/fbabb501f48f258512c0084b013e1c0944893f20) Thanks [@alexjbuck](https://github.com/alexjbuck)! - Add a method to find the possible mission root directories of a pattern-file set

- [#43](https://github.com/alexjbuck/pathvein/pull/43) [`fbabb50`](https://github.com/alexjbuck/pathvein/commit/fbabb501f48f258512c0084b013e1c0944893f20) Thanks [@alexjbuck](https://github.com/alexjbuck)! - Added threaded copy operations to concurrently process files

### Patch Changes

- [#34](https://github.com/alexjbuck/pathvein/pull/34) [`e466a9d`](https://github.com/alexjbuck/pathvein/commit/e466a9d3ce3aa88dab2974abe06b35bdd5ee53bc) Thanks [@alexjbuck](https://github.com/alexjbuck)! - Changed private path utils to public

## 0.8.0

### Minor Changes

- [#31](https://github.com/alexjbuck/pathvein/pull/31) [`68fc485`](https://github.com/alexjbuck/pathvein/commit/68fc485cd4643694a33f5b1ab6a4b966a842d9c6) Thanks [@alexjbuck](https://github.com/alexjbuck)! - Added cacheing to the path walk functionality.

  Specifically cached the results of `_iterdir` which powers the core of the path `walk` function.

## 0.7.1

### Patch Changes

- [#24](https://github.com/alexjbuck/pathvein/pull/24) [`b08dadb`](https://github.com/alexjbuck/pathvein/commit/b08dadb1df7c050edea9d0846a7991928f0531bc) Thanks [@alexjbuck](https://github.com/alexjbuck)! - Added support for static type checking with `py.typed`

## 0.7.0

### Minor Changes

- [#21](https://github.com/alexjbuck/pathvein/pull/21) [`d605cdd`](https://github.com/alexjbuck/pathvein/commit/d605cddd09ba2eaf3e749c643e94d7c4ad3ebeee) Thanks [@alexjbuck](https://github.com/alexjbuck)! - Implemented and tested s3 path support

## 0.6.2

### Patch Changes

- [#15](https://github.com/alexjbuck/pathvein/pull/15) [`bd3f34a`](https://github.com/alexjbuck/pathvein/commit/bd3f34a6ea8038171b84c00f03b2af02e3b391eb) Thanks [@alexjbuck](https://github.com/alexjbuck)! - Fix CI to remove use of make

## 0.6.1

### Patch Changes

- 6901fdf: (ci) Fix configuration for creating GitHub releases from changesets
- b4674f8: (docs) Update README to reflect breaking changes to the API
- b4674f8: Bump cross-spawn version to 7.0.6 to resolve security audit

  Security audit recommends >=6.0.6 and flags <6.0.6

## 0.6.0

### Minor Changes

- c6e5589: BREAKING CHANGE: Change the library scan and shuffle API.

  The library scan and shuffle functions have been made orthogonal and to accept in-memory objects
  instead of taking file paths.

  Added `shuffle_to` and `shuffle_with` to allow shuffling to a fixed destination or shuffling to
  a destination defined by some function for each match result from `scan`.

- c6e5589: Add initial prop-testing suite. Coverage improving

### Patch Changes

- c6e5589: Fix bug preventing pattern matching to occur during scan
- c6e5589: Remove shutil copy and pathlib.Path.walk or os.walk

## 0.5.6

### Patch Changes

- 76fb3ba: Update README

## 0.5.5

### Patch Changes

- 7d7878a: Resize logo in readme

## 0.5.4

### Patch Changes

- 4f1ff47: Fix type annotation error in typer cli arguments
- 4f1ff47: Fix logging
- 9853a72: Update ci and add yarn ecosystem to use changesets
- 4f1ff47: Update README

## 0.5.2

### Patch Changes

- 9853a72: Update ci and add yarn ecosystem to use changesets

### Fix

- **uv**: Fix lockfile

## 0.5.1 (2024-11-19)

### Fix

- **ci**: Change runs-on setting for build and check workflow

## 0.5.0 (2024-11-19)

### Feat

- **library**: Restructure pathvein library and extract cli into separate optional module

### Fix

- **uv**: Update lockfile

## 0.4.0 (2024-11-16)

### Feat

- **ci**: Add CI pipeline to create GitLab releases on new tags

### Fix

- **uv**: Add updated uv.lock file

## 0.3.0 (2024-11-16)

### BREAKING CHANGE

- Entry point is now called `org`, which is also `organizer.cli`

### Feat

- **project**: Refactor into package and update pyproject to support building wheel and sdist

## 0.2.0 (2024-11-15)

### Feat

- **project**: Add commitizen as a dev dependency
