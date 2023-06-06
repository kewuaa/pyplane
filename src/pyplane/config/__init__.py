from pathlib import Path

import tomli
path = Path(__file__).parent
config = {}


def load() -> dict:
    """加载配置文件。"""

    global config
    if not config:
        with open(path / 'config.toml', 'rb') as f:
            config = tomli.load(f)
    return config


