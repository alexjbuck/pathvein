## 0.5.3 (2024-11-19)

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
