# flake8_typing_imports

When an import is made only to satisfy typing static analysis tools like `mypy`, `pyright` or `pyre`, it risks incurring redundant runtime overhead. The preferrable way to code such an import is:

```python
from __future__ import annotations
from typing import TYPE_CHECKING
...

if TYPE_CHECKING:
  from my.module import MyAwesomeType


def func(input: MyAwesomeType):
  ...
```

This project is a flake8 plugin that alerts on such imports, used only for typing, and suggests moving them to a `TYPE_CHECKING` block.
