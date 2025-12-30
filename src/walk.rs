use ignore::WalkBuilder;
use pyo3::prelude::*;
use smallvec::SmallVec;
use std::collections::HashMap;
use std::sync::{Arc, Mutex};

/// Type alias for directory contents: (filenames, dirnames)
type DirContents = (SmallVec<[String; 32]>, SmallVec<[String; 8]>);

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

    // Collect all entries grouped by directory
    let dir_contents: Arc<Mutex<HashMap<String, DirContents>>> =
        Arc::new(Mutex::new(HashMap::new()));

    // Walk in parallel
    builder.build_parallel().run(|| {
        let dir_contents = Arc::clone(&dir_contents);
        Box::new(move |entry_result| {
            if let Ok(dir_entry) = entry_result {
                let path = dir_entry.path();

                // Get parent directory
                if let Some(parent) = path.parent() {
                    let parent_str = parent.to_string_lossy().to_string();
                    let name = path
                        .file_name()
                        .and_then(|n| n.to_str())
                        .map(|s| s.to_string());

                    if let Some(name) = name {
                        if let Some(file_type) = dir_entry.file_type() {
                            let mut contents = dir_contents.lock().unwrap();
                            let entry = contents
                                .entry(parent_str)
                                .or_insert((SmallVec::new(), SmallVec::new()));

                            if file_type.is_file() {
                                entry.0.push(name);
                            } else if file_type.is_dir() {
                                entry.1.push(name);
                            }
                        }
                    }
                }
            }
            ignore::WalkState::Continue
        })
    });

    // Convert to DirEntry format
    let contents = dir_contents.lock().unwrap();
    let results: Vec<DirEntry> = contents
        .iter()
        .map(|(path, (files, dirs))| DirEntry {
            path: path.clone(),
            filenames: files.to_vec(),
            dirnames: dirs.to_vec(),
        })
        .collect();

    Ok(results)
}
