<!-- markdownlint-disable MD033 MD041 -->
<div align="center">
  <picture>
    <img alt="" src="logo.png" width="128">
  </picture>
  <p>
    <b>Pathvein</b>
    <br />
    Rich and deep file structure pattern matching
  </p>
  <p>
    <a href="https://github.com/alexjbuck/pathvein/actions/workflows/check.yaml">
      <img alt="Checks" src="https://github.com/alexjbuck/pathvein/actions/workflows/check.yaml/badge.svg">
    </a>
    <a href="https://pypi.org/project/pathvein/">
      <img alt="PyPI" src="https://img.shields.io/pypi/v/pathvein?color=yellow">
    </a>
  </p>
</div>
<!-- markdownlint-restore MD033 MD041 -->

## Library usage

```python
from pathvein import scan, shuffle, FileStructurePattern

# Construct a FileStructurePattern
pattern = FileStructurePattern(directory_name = "...",                            # str
                               files = ["*.csv","*.config"],                      # list[str]
                               directories = [FileStructurePattern(...)],         # list[Self]
                               optional_files = ["*.py", "main.rs"],              # list[str]
                               optional_directories = [FileStructurePattern(...)] # list[Self]

# Export a pattern to a file
Path("pattern.config").write_text(pattern.to_json())

# Recursively scan a directory path for directory structures that match the requirements
matches = scan(source=Path("source"),                       # Path
               pattern_spec_paths=[Path("pattern.config")]) # list[Path]

# Recursively scan a source path for pattern-spec directory structures and copy them to the destination
shuffle(source=Path("source"),                       # Path
        destination=Path("dest"),                    # Path
        pattern_spec_paths=[Path("pattern.config")], # list[Self]
        overwrite=False,                             # bool
        dryrun=False)                                # bool
```

## CLI usage

```shell
# Install using your favorite python package installer
$ uv pip install pathvein[cli]

# View the commandline interface help
$ pathvein --help
uv run pathvein -h

 Usage: pathvein [OPTIONS] COMMAND [ARGS]...

╭─ Options ─────────────────────────────────────────────────────────────────────────────╮
│ --install-completion            Install completion for the current shell.             │
│ --show-completion               Show completion for the current shell, to copy it or  │
│                                 customize the installation.                           │
│ --help                -h        Show this message and exit.                           │
╰───────────────────────────────────────────────────────────────────────────────────────╯
╭─ Commands ────────────────────────────────────────────────────────────────────────────╮
│ scan                                                                                  │
│ shuffle                                                                               │
╰───────────────────────────────────────────────────────────────────────────────────────╯

# Scan a directory path
# pathvein scan <scan path> --pattern <pattern file>
$ pathvein scan source_dir --pattern pattern.config
/source_dir/first/match/path
/source_dir/second/match/path
/source_dir/third/match/path
...


# Scan a directory path and move all matches to a destination directory
# pathvein shuffle <scan path> <dest path> -p <pattern file>
pathvein shuffle source_dir dest_dir -p pattern.config -p additional.config
```

