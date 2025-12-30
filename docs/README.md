# Pathvein Documentation

This directory contains the source files for the Pathvein documentation site.

## Building Docs Locally

### Install Dependencies

```shell
pip install -e '.[docs]'
# or with uv
uv pip install -e '.[docs]'
```

### Build and Serve

```shell
# Serve with live reload (recommended for development)
mkdocs serve

# Build static site
mkdocs build

# Build with strict mode (fail on warnings)
mkdocs build --strict
```

The documentation will be available at http://localhost:8000

## Versioned Documentation with mike

This project uses [mike](https://github.com/jimporter/mike) for versioned documentation.

### Deploying Locally

```shell
# Deploy current version as "latest"
mike deploy latest

# Deploy a specific version
mike deploy 0.9.0 stable --update-aliases

# Set default version
mike set-default latest

# List all versions
mike list

# Serve versioned docs locally
mike serve
```

### Deploying to GitHub Pages

Documentation is automatically deployed by GitHub Actions:

- **On push to main**: Deployed as `latest` and `main`
- **On new tag (v*)**: Deployed as the version number and aliased as `stable`

The workflow is defined in `.github/workflows/docs.yaml`

### Version Management

mike stores versions in the `gh-pages` branch. Each version is in its own directory:

```
gh-pages/
├── latest/          # Latest main branch
├── main/            # Alias to latest
├── 0.9.0/           # Specific version
├── stable/          # Alias to latest stable release
└── versions.json    # Version metadata
```

## Documentation Structure

```
docs/
├── index.md                    # Home page
├── getting-started/
│   ├── installation.md         # Installation guide
│   └── quick-start.md          # Quick start tutorial
├── guide/
│   ├── patterns.md             # Working with patterns
│   ├── scanning.md             # Scanning directories
│   └── shuffling.md            # Shuffling/copying files
├── api/
│   ├── index.md                # API reference overview
│   ├── functions.md            # Core functions
│   ├── pattern.md              # FileStructurePattern
│   ├── types.md                # Data types
│   └── backend.md              # Backend info
└── about/
    ├── changelog.md            # Version history
    └── architecture.md         # Technical architecture
```

## Writing Documentation

### Markdown Files

Documentation is written in GitHub-flavored Markdown with extensions:

- **Admonitions**: `!!! note`, `!!! warning`, etc.
- **Code highlighting**: Fenced code blocks with language
- **Tables**: Standard Markdown tables
- **Cross-references**: `[link text](../path/to/page.md)`

### API Documentation

API reference pages use mkdocstrings to auto-generate docs from docstrings:

```markdown
## Function Name

::: pathvein.lib.function_name
    options:
      show_root_heading: true
      show_source: true
```

This automatically includes:
- Function signature
- Docstring (including Rust-exposed functions via PyO3)
- Type annotations
- Source code

### Docstring Style

Pathvein uses Google-style docstrings:

```python
def my_function(arg1: str, arg2: int) -> bool:
    """Short description.

    Longer description with more details.

    Args:
        arg1: Description of arg1
        arg2: Description of arg2

    Returns:
        Description of return value

    Raises:
        ValueError: When something is wrong

    Example:
        >>> my_function("hello", 42)
        True
    """
```

## Configuration

### mkdocs.yml

Main configuration file:
- Site metadata
- Theme configuration (Material for MkDocs)
- Navigation structure
- Plugin settings (mkdocstrings, search)
- Markdown extensions

### mike Configuration

Version provider is configured in `mkdocs.yml`:

```yaml
extra:
  version:
    provider: mike
```

This enables the version selector in the documentation site.

## Customization

### Theme Colors

Edit `mkdocs.yml`:

```yaml
theme:
  palette:
    - scheme: default
      primary: indigo    # Change this
      accent: indigo     # And this
```

### Navigation

Edit the `nav:` section in `mkdocs.yml`:

```yaml
nav:
  - Home: index.md
  - Getting Started:
    - Installation: getting-started/installation.md
```

### Adding Pages

1. Create new `.md` file in appropriate directory
2. Add to `nav:` section in `mkdocs.yml`
3. Commit and push

## Troubleshooting

### Build Fails

```shell
# Check for errors with strict mode
mkdocs build --strict

# Check mkdocstrings can find modules
python -c "import pathvein; print(pathvein.__file__)"
```

### Missing API Documentation

Ensure pathvein is installed in development mode:

```shell
pip install -e .
```

### Version Not Appearing

Check the gh-pages branch:

```shell
git checkout gh-pages
ls -la
cat versions.json
git checkout -
```

## Resources

- [MkDocs Documentation](https://www.mkdocs.org/)
- [Material for MkDocs](https://squidfunk.github.io/mkdocs-material/)
- [mkdocstrings](https://mkdocstrings.github.io/)
- [mike Documentation](https://github.com/jimporter/mike)
