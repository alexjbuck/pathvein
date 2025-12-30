# Changelog

All notable changes to pathvein are documented in this file.

## 0.9.0

### Minor Changes

- [#43](https://github.com/alexjbuck/pathvein/pull/43) Add a method to find the possible mission root directories of a pattern-file set
- [#43](https://github.com/alexjbuck/pathvein/pull/43) Added threaded copy operations to concurrently process files

### Patch Changes

- [#34](https://github.com/alexjbuck/pathvein/pull/34) Changed private path utils to public

## 0.8.0

### Minor Changes

- [#31](https://github.com/alexjbuck/pathvein/pull/31) Added caching to the path walk functionality

  Specifically cached the results of `_iterdir` which powers the core of the path `walk` function.

## 0.7.1

### Patch Changes

- [#24](https://github.com/alexjbuck/pathvein/pull/24) Added support for static type checking with `py.typed`

## 0.7.0

### Minor Changes

- [#21](https://github.com/alexjbuck/pathvein/pull/21) Implemented and tested s3 path support

## 0.6.2

### Patch Changes

- [#15](https://github.com/alexjbuck/pathvein/pull/15) Fix CI to remove use of make

## 0.6.1

### Patch Changes

- Fix configuration for creating GitHub releases from changesets
- Update README to reflect breaking changes to the API
- Bump cross-spawn version to 7.0.6 to resolve security audit

## 0.6.0

### Minor Changes

- **BREAKING CHANGE**: Change the library scan and shuffle API

  The library scan and shuffle functions have been made orthogonal and to accept in-memory objects
  instead of taking file paths.

  Added `shuffle_to` and `shuffle_with` to allow shuffling to a fixed destination or shuffling to
  a destination defined by some function for each match result from `scan`.

- Add initial prop-testing suite. Coverage improving

### Patch Changes

- Fix bug preventing pattern matching to occur during scan
- Remove shutil copy and pathlib.Path.walk or os.walk

## 0.5.6

### Patch Changes

- Update README

## 0.5.5

### Patch Changes

- Resize logo in readme

## 0.5.4

### Patch Changes

- Fix type annotation error in typer cli arguments
- Fix logging
- Update ci and add yarn ecosystem to use changesets
- Update README

## 0.5.2

### Patch Changes

- Update ci and add yarn ecosystem to use changesets
- Fix uv lockfile

## 0.5.1

### Fix

- Change runs-on setting for build and check workflow

## 0.5.0

### Features

- Restructure pathvein library and extract cli into separate optional module

### Fix

- Update uv lockfile

## 0.4.0

### Features

- Add CI pipeline to create GitLab releases on new tags

### Fix

- Add updated uv.lock file

## 0.3.0

### BREAKING CHANGE

- Entry point is now called `org`, which is also `organizer.cli`

### Features

- Refactor into package and update pyproject to support building wheel and sdist

## 0.2.0

### Features

- Add commitizen as a dev dependency
