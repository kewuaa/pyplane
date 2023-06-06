from typing import Sequence

from pygame.sprite import Sprite, Group
import pygame as pg

from .. import images
from .. import config


class Bullet(Sprite):
    """子弹。"""

    def __init__(
        self,
        speed: int,
        pos: Sequence[int],
        image: pg.Surface,
        *groups: Group
    ) -> None:
        super().__init__(*groups)
        self._speed = speed
        self.image = image
        self.rect = image.get_rect()
        self.rect.centerx = pos[0]
        self.rect.top = pos[1]

    def _should_be_killed(self) -> bool:
        """是否需要销毁。"""

        raise NotImplementedError

    def update(self, screen: pg.Surface, event: list[pg.event.Event, ...]) -> None:
        self.rect.y -= self._speed
        if self._should_be_killed():
            self.kill()


class PlayerBullet(Bullet):
    """玩家子弹。"""

    IMAGE = images.load('player/bullet.png')

    def __init__(self, pos: Sequence[int], *groups: Group) -> None:
        super().__init__(
            config.load()['player']['bullet_speed'],
            pos, self.IMAGE, *groups
        )

    def _should_be_killed(self) -> bool:
        """是否需要销毁。"""

        return self.rect.bottom < 0

class EnemyBullet(Bullet):
    """敌人子弹。"""

    IMAGE = images.load('enemy/bullet.png')

    def __init__(self, pos: Sequence[int], *groups: Group) -> None:
        super().__init__(
            -config.load()['enemy']['bullet_speed'],
            pos, self.IMAGE, *groups
        )

    def _should_be_killed(self) -> None:
        """是否需要销毁。"""

        return self.rect.top > config.load()['screen']['height']
