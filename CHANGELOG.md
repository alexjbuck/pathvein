# pathvein

## 0.9.0

### Minor Changes

- [#43](https://github.com/alexjbuck/pathvein/pull/43) [`fbabb50`](https://github.com/alexjbuck/pathvein/commit/fbabb501f48f258512c0084b013e1c0944893f20) Thanks [@alexjbuck](https://github.com/alexjbuck)! - Add a method to find the possible mission root directories of a pattern-file set

- [#43](https://github.com/alexjbuck/pathvein/pull/43) [`fbabb50`](https://github.com/alexjbuck/pathvein/commit/fbabb501f48f258512c0084b013e1c0944893f20) Thanks [@alexjbuck](https://github.com/alexjbuck)! - Added threaded copy operations to concurrently process files

### Patch Changes

- [#34](https://github.com/alexjbuck/pathvein/pull/34) [`e466a9d`](https://github.com/alexjbuck/pathvein/commit/e466a9d3ce3aa88dab2974abe06b35bdd5ee53bc) Thanks [@alexjbuck](https://github.com/alexjbuck)! - Changed private path utils to public

## 0.8.0

### Minor Changes

- [#31](https://github.com/alexjbuck/pathvein/pull/31) [`68fc485`](https://github.com/alexjbuck/pathvein/commit/68fc485cd4643694a33f5b1ab6a4b966a842d9c6) Thanks [@alexjbuck](https://github.com/alexjbuck)! - Added cacheing to the path walk functionality.

  Specifically cached the results of `_iterdir` which powers the core of the path `walk` function.

## 0.7.1

### Patch Changes

- [#24](https://github.com/alexjbuck/pathvein/pull/24) [`b08dadb`](https://github.com/alexjbuck/pathvein/commit/b08dadb1df7c050edea9d0846a7991928f0531bc) Thanks [@alexjbuck](https://github.com/alexjbuck)! - Added support for static type checking with `py.typed`

## 0.7.0

### Minor Changes

- [#21](https://github.com/alexjbuck/pathvein/pull/21) [`d605cdd`](https://github.com/alexjbuck/pathvein/commit/d605cddd09ba2eaf3e749c643e94d7c4ad3ebeee) Thanks [@alexjbuck](https://github.com/alexjbuck)! - Implemented and tested s3 path support

## 0.6.2

### Patch Changes

- [#15](https://github.com/alexjbuck/pathvein/pull/15) [`bd3f34a`](https://github.com/alexjbuck/pathvein/commit/bd3f34a6ea8038171b84c00f03b2af02e3b391eb) Thanks [@alexjbuck](https://github.com/alexjbuck)! - Fix CI to remove use of make

## 0.6.1

### Patch Changes

- 6901fdf: (ci) Fix configuration for creating GitHub releases from changesets
- b4674f8: (docs) Update README to reflect breaking changes to the API
- b4674f8: Bump cross-spawn version to 7.0.6 to resolve security audit

  Security audit recommends >=6.0.6 and flags <6.0.6

## 0.6.0

### Minor Changes

- c6e5589: BREAKING CHANGE: Change the library scan and shuffle API.

  The library scan and shuffle functions have been made orthogonal and to accept in-memory objects
  instead of taking file paths.

  Added `shuffle_to` and `shuffle_with` to allow shuffling to a fixed destination or shuffling to
  a destination defined by some function for each match result from `scan`.

- c6e5589: Add initial prop-testing suite. Coverage improving

### Patch Changes

- c6e5589: Fix bug preventing pattern matching to occur during scan
- c6e5589: Remove shutil copy and pathlib.Path.walk or os.walk

## 0.5.6

### Patch Changes

- 76fb3ba: Update README

## 0.5.5

### Patch Changes

- 7d7878a: Resize logo in readme

## 0.5.4

### Patch Changes

- 4f1ff47: Fix type annotation error in typer cli arguments
- 4f1ff47: Fix logging
- 9853a72: Update ci and add yarn ecosystem to use changesets
- 4f1ff47: Update README

## 0.5.2

### Patch Changes

- 9853a72: Update ci and add yarn ecosystem to use changesets

### Fix

- **uv**: Fix lockfile

## 0.5.1 (2024-11-19)

### Fix

- **ci**: Change runs-on setting for build and check workflow

## 0.5.0 (2024-11-19)

### Feat

- **library**: Restructure pathvein library and extract cli into separate optional module

### Fix

- **uv**: Update lockfile

## 0.4.0 (2024-11-16)

### Feat

- **ci**: Add CI pipeline to create GitLab releases on new tags

### Fix

- **uv**: Add updated uv.lock file

## 0.3.0 (2024-11-16)

### BREAKING CHANGE

- Entry point is now called `org`, which is also `organizer.cli`

### Feat

- **project**: Refactor into package and update pyproject to support building wheel and sdist

## 0.2.0 (2024-11-15)

### Feat

- **project**: Add commitizen as a dev dependency
