# flake8_typing_imports

When an import is added only to satisfy static-analysis tools like `mypy`, `pyright` or `pyre`, it risks incurring redundant runtime overhead. The preferrable way to code such an import is:

```python
from __future__ import annotations
from typing import TYPE_CHECKING
...

if TYPE_CHECKING:
  from my.module import MyAwesomeType


def func(input: MyAwesomeType):
  ...
```

This project is a flake8 extension that alerts on such imports, used only for typing, and suggests moving them to a `TYPE_CHECKING` block.


This won't be uploaded to PyPI until it gathers some more mileage. In the mean time, to use it:
1. Clone the repo,
2. From the repo directory:
```
$ pip install .
```
3. Finally, run flake8 in your preferred way, the simplest being:
```
$ flake8 <path> 
```

