# Installation

## PyPI Installation

Pathvein is available on PyPI and can be installed with pip, pipx, or uv:

### Full Installation (Recommended)

For the full experience including the CLI:

```shell
pip install 'pathvein[cli]'
```

Or with pipx for isolated CLI installation:

```shell
pipx install 'pathvein[cli]'
```

Or run directly with uv:

```shell
uvx --with 'pathvein[cli]' pathvein
```

### Library Only

For programmatic use only (no CLI):

```shell
pip install pathvein
```

### With S3 Support

To work with S3 and other cloud storage:

```shell
pip install 'pathvein[s3]'
```

### All Extras

To install everything:

```shell
pip install 'pathvein[cli,s3]'
```

## Building from Source

To build from source (requires Rust toolchain for full performance):

```shell
git clone https://github.com/alexjbuck/pathvein.git
cd pathvein
pip install .
```

If you don't have Rust installed, pathvein will fall back to pure Python automatically.

### Installing Rust

To get the Rust-powered performance improvements, install the Rust toolchain:

```shell
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
```

Or visit [rustup.rs](https://rustup.rs/) for other installation methods.

## Verifying Installation

Check that pathvein is installed correctly:

```shell
python -c "import pathvein; print(pathvein.__version__)"
```

Check which backend is active:

```shell
python -c "from pathvein import get_backend_info; print(get_backend_info())"
```

You should see either `rust` (best performance) or `python` (fallback) as the backend.

## Requirements

- Python 3.8 or higher
- Optional: Rust 1.70+ for building with the Rust backend
- Optional: typer for CLI functionality
- Optional: fsspec and universal-pathlib for S3 support

## Next Steps

Now that you have pathvein installed, check out the [Quick Start Guide](quick-start.md) to learn the basics!
