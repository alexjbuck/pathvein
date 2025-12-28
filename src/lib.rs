use pyo3::prelude::*;

mod walk;
mod pattern;

/// High-performance file structure pattern matching with Rust
#[pymodule]
fn _pathvein_rs(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(walk::walk_parallel, m)?)?;
    m.add_function(wrap_pyfunction!(pattern::match_pattern, m)?)?;
    m.add_class::<pattern::PatternMatcher>()?;
    Ok(())
}
