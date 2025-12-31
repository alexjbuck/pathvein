use serde::{Deserialize, Serialize};

use crate::pattern::PatternMatcher;

/// Rust representation of FileStructurePattern
///
/// This mirrors the Python FileStructurePattern class but can be
/// serialized/deserialized for efficient FFI transfer.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct FileStructurePattern {
    pub directory_name: String,
    pub files: Vec<String>,
    pub directories: Vec<FileStructurePattern>,
    pub optional_files: Vec<String>,
    pub optional_directories: Vec<FileStructurePattern>,
}

/// Precompiled version of FileStructurePattern with cached matchers
pub struct CompiledPattern {
    pub directory_name_matcher: Option<PatternMatcher>,
    pub file_matchers: Vec<PatternMatcher>,
    pub subdir_matchers: Vec<PatternMatcher>,
}

impl FileStructurePattern {
    /// Compile all glob patterns into matchers ONCE
    ///
    /// This prevents recompiling patterns on every match check.
    /// Should be called once before starting the directory walk.
    pub fn compile(&self) -> Result<CompiledPattern, String> {
        // Compile directory name matcher if needed
        let directory_name_matcher =
            if !self.directory_name.is_empty() && self.directory_name != "*" {
                Some(
                    PatternMatcher::new(vec![self.directory_name.clone()])
                        .map_err(|e| format!("Invalid directory pattern: {}", e))?,
                )
            } else {
                None
            };

        // Compile all file pattern matchers
        let mut file_matchers = Vec::new();
        for file_pattern in &self.files {
            let matcher = PatternMatcher::new(vec![file_pattern.clone()])
                .map_err(|e| format!("Invalid file pattern '{}': {}", file_pattern, e))?;
            file_matchers.push(matcher);
        }

        // Compile all subdirectory pattern matchers
        let mut subdir_matchers = Vec::new();
        for subdir_pattern in &self.directories {
            if !subdir_pattern.directory_name.is_empty() && subdir_pattern.directory_name != "*" {
                let matcher = PatternMatcher::new(vec![subdir_pattern.directory_name.clone()])
                    .map_err(|e| format!("Invalid subdirectory pattern: {}", e))?;
                subdir_matchers.push(matcher);
            }
        }

        Ok(CompiledPattern {
            directory_name_matcher,
            file_matchers,
            subdir_matchers,
        })
    }

    /// Serialize to JSON string for FFI transfer
    #[allow(dead_code)]
    pub fn to_json(&self) -> Result<String, serde_json::Error> {
        serde_json::to_string(self)
    }

    /// Deserialize from JSON string
    pub fn from_json(json_str: &str) -> Result<Self, serde_json::Error> {
        serde_json::from_str(json_str)
    }
}

impl CompiledPattern {
    /// Check if a directory matches this pattern using precompiled matchers
    ///
    /// This is MUCH faster than recompiling patterns on every check.
    /// No pattern compilation happens here - just matching against precompiled DFAs.
    pub fn matches(&self, dirpath_name: &str, dirnames: &[String], filenames: &[String]) -> bool {
        // Check directory name with precompiled matcher
        if let Some(ref matcher) = self.directory_name_matcher {
            if !matcher.matches(dirpath_name) {
                return false;
            }
        }

        // Check required file patterns - each must match at least one file
        for matcher in &self.file_matchers {
            let has_match = filenames.iter().any(|filename| matcher.matches(filename));
            if !has_match {
                return false;
            }
        }

        // Check required subdirectory patterns - each must match at least one subdirectory
        for matcher in &self.subdir_matchers {
            let has_match = dirnames.iter().any(|dirname| matcher.matches(dirname));
            if !has_match {
                return false;
            }
        }

        true
    }
}
