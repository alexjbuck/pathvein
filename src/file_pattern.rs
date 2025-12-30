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

impl FileStructurePattern {
    /// Check if a directory matches this pattern
    ///
    /// This implements the same logic as Python's FileStructurePattern.matches():
    /// 1. Check directory name matches the pattern
    /// 2. All required files have at least one match in filenames
    /// 3. All required subdirectories have at least one match in dirnames (recursively)
    ///
    /// Note: This is a simplified version that doesn't do full recursive subdirectory
    /// checking (which would require reading subdirectories). It only checks if the
    /// subdirectory NAME pattern matches.
    pub fn matches(&self, dirpath_name: &str, dirnames: &[String], filenames: &[String]) -> bool {
        // Check directory name pattern
        if !self.directory_name.is_empty() && self.directory_name != "*" {
            match PatternMatcher::new(vec![self.directory_name.clone()]) {
                Ok(matcher) => {
                    if !matcher.matches(dirpath_name) {
                        return false;
                    }
                }
                Err(_) => return false,
            }
        }

        // Check required file patterns - each pattern must match at least one file
        for file_pattern in &self.files {
            let matcher = match PatternMatcher::new(vec![file_pattern.clone()]) {
                Ok(m) => m,
                Err(_) => return false,
            };

            let has_match = filenames.iter().any(|filename| matcher.matches(filename));
            if !has_match {
                return false;
            }
        }

        // Check required subdirectory patterns - each pattern must match at least one subdirectory name
        for subdir_pattern in &self.directories {
            if !subdir_pattern.directory_name.is_empty() && subdir_pattern.directory_name != "*" {
                let matcher = match PatternMatcher::new(vec![subdir_pattern.directory_name.clone()])
                {
                    Ok(m) => m,
                    Err(_) => return false,
                };

                let has_match = dirnames.iter().any(|dirname| matcher.matches(dirname));
                if !has_match {
                    return false;
                }
            }
        }

        true
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
