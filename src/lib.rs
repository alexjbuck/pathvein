use pyo3::prelude::*;

mod pattern;
mod walk;

/// High-performance file structure pattern matching with Rust
#[pymodule]
fn _pathvein_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(walk::walk_parallel, m)?)?;
    m.add_function(wrap_pyfunction!(walk::scan_parallel, m)?)?;
    m.add_function(wrap_pyfunction!(pattern::match_pattern, m)?)?;
    m.add_class::<pattern::PatternMatcher>()?;
    m.add_class::<walk::ScanResult>()?;
    Ok(())
}
