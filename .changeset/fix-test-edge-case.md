---
"pathvein": patch
---

Fix test failure: filter out special directory names from test strategies
- Update valid_name_strategy to exclude '.' and '..' as complete filenames
- Prevents Hypothesis from generating invalid filesystem references in tests
- Resolves IsADirectoryError when tests attempted to create files with these reserved names
