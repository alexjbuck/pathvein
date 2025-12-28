# Pathvein Improvements & Fixes

This document tracks remaining improvements and fixes for the pathvein project.

## Critical Issues

### 1. CLI Import Error Without [cli] Extra
**Status**: 🔴 Critical
**Issue**: The `pathvein` script entry point is always installed, but typer is only in `[cli]` extra. Installing without `[cli]` causes ImportError.

**Fix Options**:
- **Option A**: Make CLI script conditional (check if typer available, show error if not)
- **Option B**: Move typer back to core dependencies (loses library/CLI separation)
- **Option C**: Remove script entry point, require `python -m pathvein.cli` for CLI

**Recommended**: Option A with graceful error message

**Implementation**:
```python
# In cli.py, add at module level:
try:
    import typer
    HAS_TYPER = True
except ImportError:
    HAS_TYPER = False

def main():
    if not HAS_TYPER:
        print("Error: CLI requires typer. Install with: pip install 'pathvein[cli]'")
        sys.exit(1)
    # ... rest of main
```

---

## High Priority

### 2. Missing CLI Tests
**Status**: 🟡 High
**File**: `tests/test_cli.py` (0 lines)

**What's Missing**:
- No tests for `cli_scan` command
- No tests for `cli_shuffle` command
- No tests for error handling
- No tests for verbosity flags
- No tests for pattern file loading

**Recommendation**: Add comprehensive CLI tests using typer's testing utilities

---

### 3. Undocumented `assess()` Function
**Status**: 🟡 High
**File**: `src/pathvein/__init__.py`

**Issue**: `assess()` is exported in `__all__` but not documented in README

**Options**:
- Document it in README with usage examples
- Mark as internal/private by removing from `__all__`

---

### 4. Hardcoded Log File Path
**Status**: 🟡 High
**File**: `src/pathvein/cli.py:89`

```python
handlers=[logging.FileHandler("/tmp/organizer.log"), logging.StreamHandler()]
```

**Issues**:
- `/tmp/` doesn't exist on Windows
- No user control over log location
- Could fill up /tmp

**Fix**: Make configurable via environment variable or CLI flag:
```python
log_path = os.getenv("PATHVEIN_LOG_FILE", "/tmp/pathvein.log")
# Or add CLI option: --log-file
```

---

## Medium Priority

### 5. Pattern Validation
**Status**: 🟠 Medium

**Issue**: No validation that patterns are sensible before use

**Examples of Invalid Patterns**:
- Empty directory_name
- Conflicting required/optional files
- Self-referential directories

**Recommendation**: Add `.validate()` method to FileStructurePattern:
```python
def validate(self) -> List[str]:
    """Return list of validation warnings/errors"""
    issues = []
    if not self.directory_name:
        issues.append("directory_name is empty")

    # Check for duplicates between required and optional
    duplicate_files = set(self.files) & set(self.optional_files)
    if duplicate_files:
        issues.append(f"Files in both required and optional: {duplicate_files}")

    # Recursively validate subdirectories
    for subdir in self.all_directories:
        issues.extend(subdir.validate())

    return issues
```

---

### 6. Better Error Reporting for Failed Copies
**Status**: 🟠 Medium
**File**: `src/pathvein/lib.py:142-147`

**Current Behavior**: FileExistsError is logged and swallowed, returns empty result

**Issue**: User doesn't know which specific files failed

**Fix**: Return partial results with error information:
```python
@dataclass
class ShuffleResult:
    source: Path
    destination: Path
    pattern: FileStructurePattern
    success: bool = True
    error: Optional[str] = None
```

---

### 7. Progress Callbacks for Large Operations
**Status**: 🟠 Medium

**Use Case**: Scanning/copying large directory trees with no feedback

**Recommendation**: Add optional progress callback:
```python
def scan(
    source: Path,
    patterns: Iterable[FileStructurePattern],
    on_progress: Optional[Callable[[int, int, Path], None]] = None
) -> Set[ScanResult]:
    """
    on_progress called as: on_progress(current, total, current_path)
    """
```

---

### 8. Type Hint for chunk_size
**Status**: 🟢 Low
**File**: `src/pathvein/_path_utils.py:20`

**Issue**: Missing type hint on chunk_size parameter

**Fix**:
```python
def stream_copy(source: Path, destination: Path, chunk_size: int = 256 * 1024) -> None:
```

---

## Documentation Improvements

### 9. Add `assess()` Documentation
**Status**: 🟡 High

Add to README:
```markdown
### Advanced: Pattern Assessment

The `assess()` function can determine which pattern a file belongs to:

\`\`\`python
from pathvein import assess, FileStructurePattern

# Given a file, find which patterns it could match
patterns = [pattern1, pattern2, pattern3]
matches = assess(Path("data/experiment_1/results.csv"), patterns)

for match in matches:
    print(f"File matches pattern: {match.pattern}")
    print(f"Root directory: {match.source}")
\`\`\`
```

---

### 10. Add Performance Benchmarks Section
**Status**: 🟢 Low

Document actual performance comparisons:
- Python vs Rust backend benchmarks
- os.scandir vs path.iterdir speedup
- Pattern caching improvements
- Threading speedup with different worker counts

---

### 11. Add Examples Directory
**Status**: 🟢 Low

Create `examples/` with:
- `basic_scan.py` - Simple pattern matching
- `advanced_shuffle.py` - Using shuffle_with with custom logic
- `s3_example.py` - Working with S3 paths
- Common pattern files (`.json`) for typical use cases

---

## Future Enhancements

### 12. Dry-run Reporting Structure
**Status**: 🔵 Future

**Current**: Dry-run just skips operations
**Better**: Return structured data about what would be done

```python
@dataclass
class DryRunReport:
    would_copy: List[Tuple[Path, Path]]
    total_files: int
    total_bytes: int
    estimated_time: float
```

---

### 13. Plugin System for Destination Strategies
**Status**: 🔵 Future

Instead of just functions, allow registering destination strategies:
```python
from pathvein.strategies import AlphabeticBins, DateBased

shuffle(matches, strategy=AlphabeticBins(bins=["a-m", "n-z"]))
shuffle(matches, strategy=DateBased(format="%Y-%m-%d"))
```

---

### 14. Pattern Builder DSL
**Status**: 🔵 Future

More ergonomic pattern creation:
```python
pattern = (
    Pattern()
    .name("experiment_*")
    .require("data.csv", "config.yaml")
    .optional("notes.txt")
    .subdir(
        Pattern()
        .name("results")
        .require("*.png")
    )
)
```

---

## Testing Gaps

### 15. Add Integration Tests
- End-to-end scan + shuffle workflows
- S3 integration tests (currently only basic S3 path tests)
- Error recovery tests (permission errors, disk full, etc.)

### 16. Add Performance Tests
- Benchmark suite comparing backends
- Regression tests for performance
- Memory usage tests (cache bounds)

### 17. Add Property-Based Tests
- Already using Hypothesis for pattern generation
- Add more property tests for scan/shuffle operations
- Fuzzing for JSON pattern parsing

---

## Code Quality

### 18. Add Docstrings to CLI Functions
**Files**: `src/pathvein/cli.py:46-56, 60-81`

Both `cli_scan` and `cli_shuffle` lack docstrings.

---

### 19. Type Stub File Generation
Generate `.pyi` stub files for better IDE support, especially for Rust extension fallback logic.

---

## Summary

**Critical (Fix Now)**:
- #1: CLI import error without [cli] extra

**High Priority (Next Release)**:
- #2: Add CLI tests
- #3: Document or privatize assess()
- #4: Configurable log file path

**Medium Priority (Nice to Have)**:
- #5-7: Pattern validation, better error reporting, progress callbacks

**Future Enhancements**:
- #12-14: Structured dry-run, plugins, builder DSL
