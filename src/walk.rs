use dashmap::DashMap;
use ignore::WalkBuilder;
use pyo3::prelude::*;
use smallvec::SmallVec;
use std::ffi::OsString;
use std::path::PathBuf;
use std::sync::Arc;

/// Type alias for directory contents: (filenames, dirnames)
/// Uses OsString to avoid UTF-8 conversion overhead during parallel collection
type DirContents = (SmallVec<[OsString; 32]>, SmallVec<[OsString; 8]>);

/// Directory entry returned from walk
#[pyclass]
#[derive(Clone)]
pub struct DirEntry {
    #[pyo3(get)]
    pub path: String,
    #[pyo3(get)]
    pub dirnames: Vec<String>,
    #[pyo3(get)]
    pub filenames: Vec<String>,
}

#[pymethods]
impl DirEntry {
    fn __repr__(&self) -> String {
        format!(
            "DirEntry(path='{}', dirs={}, files={})",
            self.path,
            self.dirnames.len(),
            self.filenames.len()
        )
    }
}

/// Parallel directory walking using ignore crate (same as ripgrep)
///
/// Uses the ignore crate's WalkParallel for efficient parallel directory
/// traversal. This is the same approach used by ripgrep for fast searching.
///
/// Args:
///     path: Root directory to walk
///     max_depth: Optional maximum depth to traverse (None = unlimited)
///     follow_links: Whether to follow symbolic links (default: false)
///
/// Returns:
///     List of DirEntry objects, each containing (path, dirnames, filenames)
#[pyfunction]
#[pyo3(signature = (path, max_depth=None, follow_links=false))]
pub fn walk_parallel(
    path: String,
    max_depth: Option<usize>,
    follow_links: bool,
) -> PyResult<Vec<DirEntry>> {
    // Build parallel walker (same as ripgrep uses)
    let mut builder = WalkBuilder::new(&path);

    if let Some(depth) = max_depth {
        builder.max_depth(Some(depth));
    }

    builder.follow_links(follow_links);
    builder.hidden(false); // Don't skip hidden files
    builder.ignore(false); // Don't use .gitignore
    builder.git_ignore(false); // Don't use .gitignore
    builder.git_global(false); // Don't use global .gitignore
    builder.git_exclude(false); // Don't use .git/info/exclude

    // Collect all entries grouped by directory (using DashMap for lock-free concurrency)
    // Use PathBuf as key to avoid String allocation during walk
    let dir_contents: Arc<DashMap<PathBuf, DirContents>> = Arc::new(DashMap::new());

    // Walk in parallel
    builder.build_parallel().run(|| {
        let dir_contents = Arc::clone(&dir_contents);
        Box::new(move |entry_result| {
            if let Ok(dir_entry) = entry_result {
                let path = dir_entry.path();

                // Get parent directory and filename
                if let (Some(parent), Some(name)) = (path.parent(), path.file_name()) {
                    if let Some(file_type) = dir_entry.file_type() {
                        // DashMap handles locking internally with sharding
                        let mut entry = dir_contents
                            .entry(parent.to_path_buf())
                            .or_insert((SmallVec::new(), SmallVec::new()));

                        // Use OsString - no UTF-8 validation needed during walk
                        if file_type.is_file() {
                            entry.0.push(name.to_os_string());
                        } else if file_type.is_dir() {
                            entry.1.push(name.to_os_string());
                        }
                    }
                }
            }
            ignore::WalkState::Continue
        })
    });

    // Convert to DirEntry format - only convert to UTF-8 String here at the end
    let results: Vec<DirEntry> = dir_contents
        .iter()
        .map(|entry| {
            let (path, (files, dirs)) = entry.pair();
            DirEntry {
                // Convert PathBuf -> String only once per directory
                path: path.to_string_lossy().into_owned(),
                // Convert OsString -> String only once per filename
                filenames: files
                    .iter()
                    .map(|s| s.to_string_lossy().into_owned())
                    .collect(),
                dirnames: dirs
                    .iter()
                    .map(|s| s.to_string_lossy().into_owned())
                    .collect(),
            }
        })
        .collect();

    Ok(results)
}

/// Scan result - a directory that matched a pattern
#[pyclass]
#[derive(Clone, Debug)]
pub struct ScanResult {
    #[pyo3(get)]
    pub path: String,
    #[pyo3(get)]
    pub pattern_index: usize,
}

#[pymethods]
impl ScanResult {
    fn __repr__(&self) -> String {
        format!(
            "ScanResult(path='{}', pattern_index={})",
            self.path, self.pattern_index
        )
    }

    fn __hash__(&self) -> u64 {
        use std::collections::hash_map::DefaultHasher;
        use std::hash::{Hash, Hasher};
        let mut hasher = DefaultHasher::new();
        self.path.hash(&mut hasher);
        self.pattern_index.hash(&mut hasher);
        hasher.finish()
    }

    fn __eq__(&self, other: &Self) -> bool {
        self.path == other.path && self.pattern_index == other.pattern_index
    }
}

/// Scan directory tree for pattern matches - walk AND match entirely in Rust
///
/// This replaces the Python scan() function's walk+match loop with a single
/// Rust call that does everything internally with NO FFI crossings during the
/// scan loop.
///
/// Args:
///     path: Root directory to scan
///     pattern_jsons: List of JSON-serialized FileStructurePattern objects
///     max_depth: Optional maximum depth to traverse
///     follow_links: Whether to follow symbolic links
///
/// Returns:
///     List of ScanResult tuples (path, pattern_index) for directories that matched
#[pyfunction]
#[pyo3(signature = (path, pattern_jsons, max_depth=None, follow_links=false))]
pub fn scan_parallel(
    path: String,
    pattern_jsons: Vec<String>,
    max_depth: Option<usize>,
    follow_links: bool,
) -> PyResult<Vec<ScanResult>> {
    use crate::file_pattern::FileStructurePattern;

    // Deserialize patterns from JSON
    let patterns: Vec<FileStructurePattern> = pattern_jsons
        .iter()
        .map(|json| {
            FileStructurePattern::from_json(json).map_err(|e| {
                PyErr::new::<pyo3::exceptions::PyValueError, _>(format!(
                    "Invalid pattern JSON: {}",
                    e
                ))
            })
        })
        .collect::<PyResult<Vec<_>>>()?;

    // Walk the directory tree
    let entries = walk_parallel(path, max_depth, follow_links)?;

    // Match each directory against patterns - ALL IN RUST
    let mut results = Vec::new();

    for entry in entries {
        let dirpath_name = std::path::Path::new(&entry.path)
            .file_name()
            .and_then(|n| n.to_str())
            .unwrap_or("");

        // Try each pattern
        for (pattern_idx, pattern) in patterns.iter().enumerate() {
            // Match entirely in Rust - no FFI crossing!
            if pattern.matches(dirpath_name, &entry.dirnames, &entry.filenames) {
                results.push(ScanResult {
                    path: entry.path.clone(),
                    pattern_index: pattern_idx,
                });
            }
        }
    }

    Ok(results)
}
