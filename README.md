<!-- markdownlint-disable MD033 MD041 -->
<div align="center">
  <picture>
    <img alt="" src="pathvein.png" width="96">
  </picture>
  <p>
    <b>Pathvein</b>
    <br />
    Deep file structure matching
  </p>
  <p>
    <a href="https://github.com/alexjbuck/pathvein/actions/workflows/check.yaml">
      <img alt="Checks" src="https://github.com/alexjbuck/pathvein/actions/workflows/check.yaml/badge.svg">
    </a>
  </p>
</div>
<!-- markdownlint-restore MD033 MD041 -->

# Pathvein

Rich and deep file structure pattern matching.

## Library usage

```python
from pathvein import scan, shuffle, FileStructurePattern

# Construct a FileStructurePattern
pattern = FileStructurePattern(directory_name = "...",                            # str
                               files = ["*.csv","*.config"],                      # list[str]
                               directories = [FileStructurePattern(...)],         # list[Self]
                               optional_files = ["*.py", "main.rs"],              # list[str]
                               optional_directories = [FileStructurePattern(...)] # list[Self]
Path("pattern.config").write_text(pattern.to_json())


# Recursively scan a directory path for directory structures that match the requirements
matches = scan(source=Path("source"),
               pattern_spec_paths=[Path("pattern.config")])

# Recursively scan a source path for pattern-spec directory structures and copy them to the destination
shuffle(source=Path("source"),
        destination=Path("dest"),
        pattern_spec_paths=[Path("pattern.config")],
        overwrite=False,
        dryrun=False)
```

## CLI usage

```shell
# Install using your favorite python package installer
uv pip install pathvein[cli]

# View the commandline interface help
pathvein --help

# Scan a directory path
# pathvein scan <scan path> --pattern <pattern file>
pathvein scan source_dir --pattern pattern.config


# Scan a directory path and move all matches to a destination directory
# pathvein shuffle <scan path> <dest path> -p <pattern file>
pathvein shuffle source_dir dest_dir -p pattern.config -p additional.config
```

