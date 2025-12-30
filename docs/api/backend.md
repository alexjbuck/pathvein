# Backend Information

Pathvein includes both a high-performance Rust backend and a pure Python fallback.

## get_backend_info

::: pathvein._backend.get_backend_info
    options:
      show_root_heading: true
      show_source: true

Returns information about which backend is currently active.

### Usage

```python
from pathvein import get_backend_info

backend = get_backend_info()
print(f"Active backend: {backend}")
```

### Return Values

- `"rust"` - Rust backend is active (best performance)
- `"python"` - Pure Python fallback is active

## Rust Backend

When available, the Rust backend provides:

- **5-10x faster** directory traversal with `walk_parallel()`
- **3-5x faster** pattern matching with compiled glob patterns
- Parallel processing across CPU cores
- Optimized memory usage with SmallVec

### Functions

The Rust backend exposes these functions (automatically used by pathvein):

#### walk_parallel

```python
from pathvein._backend import walk_parallel

# Parallel directory walking (Rust implementation)
for dirpath, dirnames, filenames in walk_parallel("/path/to/scan"):
    print(f"{dirpath}: {len(filenames)} files")
```

**Parameters:**
- `path: str` - Root directory to walk
- `max_depth: Optional[int]` - Maximum depth (None = unlimited)
- `follow_links: bool` - Whether to follow symbolic links (default: False)

**Returns:**
- `List[Tuple[str, List[str], List[str]]]` - List of (path, dirnames, filenames)

#### PatternMatcher

```python
from pathvein._backend import PatternMatcher

# Compile patterns once for efficient matching
matcher = PatternMatcher(["*.py", "test_*.rs"])

# Check single match
if matcher.matches("test_file.py"):
    print("Matched!")

# Get all matching patterns
patterns = matcher.matching_patterns("test_file.py")
print(f"Matched patterns: {patterns}")

# Check if matches all patterns
if matcher.matches_all("test_file.py.rs"):
    print("Matches all patterns!")
```

**Methods:**
- `__init__(patterns: List[str])` - Create matcher from glob patterns
- `matches(path: str) -> bool` - Check if path matches any pattern
- `matching_patterns(path: str) -> List[str]` - Get all matching patterns
- `matches_all(path: str) -> bool` - Check if path matches all patterns

#### match_pattern

```python
from pathvein._backend import match_pattern

# Single pattern matching (cached)
if match_pattern("file.py", "*.py"):
    print("Matched!")
```

**Parameters:**
- `path: str` - File or directory name to match
- `pattern: str` - Glob pattern

**Returns:**
- `bool` - True if matches, False otherwise

**Note:** Uses LRU cache (maxsize=256) for compiled patterns. For multiple matches, use `PatternMatcher` instead.

## Python Backend

The pure Python backend is used when:

- Rust extension is not available
- Working with cloud storage (S3, GCS, etc.)
- Using path-like objects other than `pathlib.Path`

### Functions

The Python backend provides equivalent functionality:

```python
from pathvein._path_utils import walk

# Python directory walking
for dirpath, dirnames, filenames in walk(Path("/path/to/scan")):
    print(f"{dirpath}: {len(filenames)} files")
```

## Automatic Backend Selection

Pathvein automatically selects the appropriate backend:

```python
from pathlib import Path
from upath import UPath
from pathvein import scan

# Uses Rust backend for local paths
local_matches = scan(Path("/local/data"), [pattern])

# Automatically uses Python backend for S3
s3_matches = scan(UPath("s3://bucket/data"), [pattern])
```

### Detection Logic

```python
from pathlib import Path

# In scan() function
if type(source) is Path:
    # Use Rust backend (fast)
    walk_parallel(str(source))
else:
    # Use Python backend (compatible)
    walk_python(source)
```

## Performance Comparison

| Operation | Python | Rust | Speedup |
|-----------|--------|------|---------|
| Directory Walking | 1x | 5-10x | 5-10x faster |
| Pattern Matching | 1x | 3-5x | 3-5x faster |
| Pattern Compilation | 1x | 10x+ | 10x+ faster |

### Benchmarks

```python
import time
from pathlib import Path
from pathvein import scan, get_backend_info, FileStructurePattern

pattern = FileStructurePattern(files=["*.py"])

print(f"Backend: {get_backend_info()}")

start = time.time()
matches = scan(Path("/large/directory"), [pattern])
elapsed = time.time() - start

print(f"Found {len(matches)} matches in {elapsed:.2f}s")
```

## Building with Rust

To build pathvein with the Rust backend:

### Requirements

- Rust 1.70 or newer
- cargo (comes with Rust)

### Install Rust

```shell
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

### Build from Source

```shell
git clone https://github.com/alexjbuck/pathvein.git
cd pathvein
pip install .
```

Maturin will automatically detect Rust and build the extension.

### Verify Rust Backend

```python
from pathvein import get_backend_info

assert get_backend_info() == "rust", "Rust backend not available"
print("✓ Rust backend is active")
```

## Fallback Behavior

If the Rust backend is unavailable, pathvein falls back gracefully:

```python
# This works regardless of backend
from pathvein import scan

matches = scan(source, [pattern])
# Uses Rust if available, Python otherwise
```

No code changes needed - the API is identical.

## Cloud Storage

For cloud storage, install the S3 extra:

```shell
pip install 'pathvein[s3]'
```

Then use with UPath:

```python
from upath import UPath
from pathvein import scan, FileStructurePattern

pattern = FileStructurePattern(files=["*.parquet"])

# Automatically uses Python backend for S3
matches = scan(
    source=UPath("s3://my-bucket/data/"),
    patterns=[pattern]
)
```

The Python backend works with any fsspec-compatible filesystem:
- S3 (`s3://`)
- Google Cloud Storage (`gs://`)
- Azure Blob Storage (`az://`)
- HTTP/HTTPS
- And more
