import random

import pygame as pg
from pygame.sprite import Sprite, Group, collide_mask
from pygame import locals

from . import bullet
from .. import images
from .. import config
screen_config = config.load()['screen']
player_g = Group()
player_bullet_g = Group()
enemy_g = Group()


def refresh(screen: pg.surface, events: list[pg.event.Event, ...]) -> None:
    """刷新并重绘精灵组。

    :param screen: 屏幕对象
    :param events: 触发事件
    """

    player_g.update(screen, events)
    player_bullet_g.update(screen, events)
    enemy_g.update(screen, events)
    player_g.draw(screen)
    player_bullet_g.draw(screen)
    enemy_g.draw(screen)


class _Plane(Sprite):
    """飞机模型。"""

    BOMB = images.load('bomb')

    def __init__(
        self,
        speed: int,
        life: int,
        image: pg.Surface,
        *groups: Group
    ) -> None:
        """初始化。

        :param speed: 速度
        :param life: 生命值
        :param image: 模型图片
        :param groups: 所属精灵组
        """

        super().__init__(*groups)
        self._speed = speed
        self._life = life
        self._bomb_img = (self.BOMB[i // 6] for i in range(len(self.BOMB) * 6))
        self._bomb = type('Bomb', (Sprite,), {})()
        self._bomb.image = self.BOMB[0]
        self._bomb.rect = self._bomb.image.get_rect()
        self.image = image.copy()
        self.rect = self.image.get_rect()
        self.alive = 1

    def switch_image(self, image: pg.Surface) -> None:
        """更换模型图像。"""

        # pos = self.rect.x, self.rect.y
        self.image = image
        # self.rect = image.get_rect()
        # self.rect.x, self.rect.y = pos

    def _move(self) -> None:
        """移动。"""

        raise NotImplementedError

    def _attack(self) -> None:
        """攻击。"""

        raise NotImplementedError

    def _check_attacked(self) -> None:
        """检查是否被攻击。"""

        raise NotImplementedError

    def update(self, screen: pg.Surface, events: list[pg.event.Event, ...]) -> None:
        self._move()
        self._attack()
        self._check_attacked()
        if not self.alive:
            try:
                self._bomb.image = next(self._bomb_img)
                self._bomb.rect.centerx = self.rect.centerx
                self._bomb.rect.centery = self.rect.centery
            except StopIteration:
                self._bomb.kill()
                super().kill()

    def kill(self) -> None:
        self._life -= 1
        if self._life < 1:
            # super().kill()
            self._bomb.add(self.groups())
            self.alive = 0


class Player(_Plane):
    """玩家模型。"""

    IMAGE = images.load('player/player.png')
    TURN_LEFT_IMAGE = images.load('player/left1.png'), images.load('player/left2.png')
    TURN_RIGHT_IMAGE = images.load('player/right1.png'), images.load('player/right2')
    LIFE_IMAGE = images.load('life.png')

    def __init__(
        self,
        *groups: Group
    ) -> None:
        """初始化。

        :param groups: 所属精灵组
        """

        super().__init__(
            config.load()['player']['speed'],
            3,
            self.IMAGE,
            *groups
        )
        self._tail_flame = images.load('player/tail_flame.png')
        self._tail_flame = type('TailFlame', (Sprite,), {})()
        self._tail_flame.image = images.load('player/tail_flame.png')
        self._tail_flame.rect = self._tail_flame.image.get_rect()
        self.rect.bottom = screen_config['height']
        self.rect.centerx = screen_config['width'] / 2
        # 攻击间隔
        self._attack_interval = 0
        # 无敌时间
        self._invincible = 0
        # 倾斜状态
        self._tilt = 0
        player_g.add(self)

    def _move_left(self) -> None:
        """左移。"""

        self._tilt -= 1
        if self._tilt < 0:
            self.switch_image(self.TURN_LEFT_IMAGE[0 if self._tilt > -300 else 1])
        x = self.rect.centerx - self._speed
        self.rect.centerx = max(0, x)

    def _move_right(self) -> None:
        """右移。"""

        self._tilt += 1
        if self._tilt > 0:
            self.switch_image(self.TURN_RIGHT_IMAGE[0 if self._tilt < 300 else 1])
        x = self.rect.centerx + self._speed
        self.rect.centerx = min(screen_config['width'], x)

    def _move_up(self) -> None:
        """上移。"""

        self._tail_flame.rect.centerx = self.rect.centerx
        self._tail_flame.rect.top = self.rect.bottom
        y = self.rect.centery - self._speed
        self.rect.centery = max(0, y)

    def _move_down(self) -> None:
        """下移。"""

        y = self.rect.centery + self._speed
        self.rect.centery = min(screen_config['height'], y)

    def _move(self) -> None:
        key_states = pg.key.get_pressed()
        if key_states[locals.K_UP]:
            self._move_up()
        if key_states[locals.K_DOWN]:
            self._move_down()
        if key_states[locals.K_LEFT]:
            self._move_left()
        else:
            if self._tilt < 0:
                self._tilt += 1
        if key_states[locals.K_RIGHT]:
            self._move_right()
        else:
            if self._tilt > 0:
                self._tilt -= 1

    def _attack(self) -> None:
        key_states = pg.key.get_pressed()
        if key_states[locals.K_SPACE]:
            self._attack_interval += 1
            if self._attack_interval > config.load()['player']['attack_interval']:
                bullet.PlayerBullet(
                    (self.rect.centerx, self.rect.top),
                    player_bullet_g
                )
                self._attack_interval = 0

    def _check_attacked(self) -> None:
        if self._invincible:
            self._invincible -= 1
        else:
            for sprite in enemy_g:
                if collide_mask(sprite, self):
                    sprite.kill()
                    self.kill()

    def update(self, screen: pg.Surface, events: list[pg.event.Event, ...]) -> None:
        super().update(screen, events)
        for event in events:
            if event.type == pg.KEYUP:
                if event.key == locals.K_UP:
                    self._tail_flame.kill()
            elif event.type == pg.KEYDOWN:
                if event.key == locals.K_UP:
                    self._tail_flame.add(player_g)
        if self.alive:
            for i in range(1, self._life + 1):
                screen.blit(
                    self.LIFE_IMAGE,
                    (
                        screen_config['width'] - i * self.LIFE_IMAGE.get_width(),
                        screen_config['height'] - self.LIFE_IMAGE.get_height()
                    )
                )
        if self._tilt == 0:
            self.switch_image(self.IMAGE)

    def kill(self) -> None:
        super().kill()
        self._invincible = config.load()['player']['invincible_time']


class Enemy(_Plane):
    """敌人。"""

    IMAGE = [
        images.load(f'enemy/{i}.png') for i in range(1, 6)
    ]

    def __init__(self, rank: int, *groups: Group) -> None:
        """初始化。

        :param rank: 敌人等级
        :param groups: 所属精灵组
        """

        super().__init__(
            config.load()['enemy']['speed'],
            rank,
            self.IMAGE[rank - 1],
            *groups
        )
        self.rect.centerx = random.randint(0, screen_config['width'])
        self.rect.bottom = 0
        # 攻击间隔
        self._attack_interval = 0
        enemy_g.add(self)

    def _move(self) -> None:
        self.rect.y += self._speed
        if self.rect.top > screen_config['height']:
            self.kill()

    def _attack(self) -> None:
        self._attack_interval += 1
        if self._attack_interval > config.load()['enemy']['attack_interval']:
            bullet.EnemyBullet(
                (self.rect.centerx, self.rect.bottom),
                self.groups()
            )
            self._attack_interval = 0

    def _check_attacked(self) -> None:
        for blt in player_bullet_g:
            if collide_mask(blt, self):
                blt.kill()
                self.kill()
