---
"pathvein": minor
---

BREAKING CHANGE: Change the library scan and shuffle API.

The library scan and shuffle functions have been made orthogonal and to accept in-memory objects
instead of taking file paths.

Added `shuffle_to` and `shuffle_with` to allow shuffling to a fixed destination or shuffling to 
a destination defined by some function for each match result from `scan`.
