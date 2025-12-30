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

/// Sequential directory walking - fast for small directories
///
/// Uses a simple sequential walk without parallel overhead. Best for small directories
/// (< 1000 entries) where parallel setup overhead dominates actual work.
///
/// Args:
///     path: Root directory to walk
///     max_depth: Optional maximum depth to traverse (None = unlimited)
///     follow_links: Whether to follow symbolic links (default: false)
///
/// Returns:
///     List of DirEntry objects, each containing (path, dirnames, filenames)
fn walk_sequential_impl(
    path: String,
    max_depth: Option<usize>,
    follow_links: bool,
) -> PyResult<Vec<DirEntry>> {
    use std::collections::HashMap;

    let mut builder = WalkBuilder::new(&path);

    if let Some(depth) = max_depth {
        builder.max_depth(Some(depth));
    }

    builder.follow_links(follow_links);
    builder.hidden(false);
    builder.ignore(false);
    builder.git_ignore(false);
    builder.git_global(false);
    builder.git_exclude(false);

    // Use simple HashMap for sequential walk
    let mut dir_contents: HashMap<PathBuf, DirContents> = HashMap::new();

    // Sequential walk - no parallel overhead
    for dir_entry in builder.build().flatten() {
        let path = dir_entry.path();

        if let (Some(parent), Some(name)) = (path.parent(), path.file_name()) {
            if let Some(file_type) = dir_entry.file_type() {
                let entry = dir_contents
                    .entry(parent.to_path_buf())
                    .or_insert((SmallVec::new(), SmallVec::new()));

                if file_type.is_file() {
                    entry.0.push(name.to_os_string());
                } else if file_type.is_dir() {
                    entry.1.push(name.to_os_string());
                }
            }
        }
    }

    // Convert to DirEntry format
    let results: Vec<DirEntry> = dir_contents
        .into_iter()
        .map(|(path, (files, dirs))| DirEntry {
            path: path.to_string_lossy().into_owned(),
            filenames: files
                .iter()
                .map(|s| s.to_string_lossy().into_owned())
                .collect(),
            dirnames: dirs
                .iter()
                .map(|s| s.to_string_lossy().into_owned())
                .collect(),
        })
        .collect();

    Ok(results)
}

/// Parallel directory walking using ignore crate (same as ripgrep)
///
/// Uses the ignore crate's WalkParallel for efficient parallel directory
/// traversal. This is the same approach used by ripgrep for fast searching.
///
/// For small directories (<1000 expected entries), automatically falls back
/// to sequential walk to avoid parallel overhead.
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
    // Automatically choose sequential vs parallel based on max_depth
    // For very shallow trees (depth 1-2), sequential avoids ~2ms parallel overhead
    // For deeper/unknown depth, use parallel (optimized for large trees)
    //
    // Note: For small flat directories, Python's os.walk may be faster due to FFI overhead.
    // This implementation is optimized for large directory trees with parallelization.
    if matches!(max_depth, Some(1) | Some(2)) {
        return walk_sequential_impl(path, max_depth, follow_links);
    }

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
