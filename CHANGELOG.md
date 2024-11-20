## 0.5.3 (2024-11-19)

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
