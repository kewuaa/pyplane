from typing import Optional, Union
from pathlib import Path

import pygame as pg
path = Path(__file__).parent


def load(name: str) -> Optional[Union[pg.Surface, list[pg.Surface, ...]]]:
    """加载图片资源。

    :param name: 资源名称
    :return: 返回加载好的资源或资源列表，不存在则返回 None
    """

    pth = path / name
    if not pth.exists():
        return
    if pth.is_dir():
        return [
            pg.image.load(path)
            for path in pth.iterdir()
        ]
    else:
        return pg.image.load(pth)
