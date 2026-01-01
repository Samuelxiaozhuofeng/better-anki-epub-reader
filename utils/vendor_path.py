from __future__ import annotations

import os
import sys
from contextlib import contextmanager
from typing import Iterator

_VENDOR_REFCOUNT = 0
_VENDOR_ADDED_BY_US = False


def _vendor_dir() -> str:
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), "vendor")


@contextmanager
def vendored_sys_path() -> Iterator[None]:
    """临时把本插件的 vendor/ 追加到 sys.path。

    目的：避免像 sys.path.insert(0, vendor) 这种全局置顶污染，导致其它插件导入到错误的依赖。
    """

    global _VENDOR_REFCOUNT, _VENDOR_ADDED_BY_US

    vendor_dir = _vendor_dir()
    if not os.path.isdir(vendor_dir):
        yield
        return

    _VENDOR_REFCOUNT += 1
    try:
        if vendor_dir not in sys.path:
            sys.path.append(vendor_dir)
            _VENDOR_ADDED_BY_US = True
        yield
    finally:
        _VENDOR_REFCOUNT -= 1
        if _VENDOR_REFCOUNT <= 0:
            _VENDOR_REFCOUNT = 0
            if _VENDOR_ADDED_BY_US:
                # 只移除我们添加的 vendor 路径；不回滚整个 sys.path，避免影响其它插件的动态注入。
                try:
                    while vendor_dir in sys.path:
                        sys.path.remove(vendor_dir)
                finally:
                    _VENDOR_ADDED_BY_US = False
