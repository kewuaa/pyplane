from pathlib import Path
import random
import asyncio

import pygame as pg

from . import model
from . import images
from . import config
root_dir = Path(__file__).parent


class PlaneGame:
    """游戏主体。"""

    def __init__(self) -> None:
        # 事件循环
        self._loop = asyncio.get_event_loop()
        # 配置
        self._config = config.load()
        # 初始化 pygame
        pg.init()
        # 设置标题栏
        pg.display.set_caption('Thunder')
        # 隐藏鼠标
        pg.mouse.set_visible(False)
        # 设置允许通过的事件
        pg.event.set_allowed([pg.QUIT, pg.KEYDOWN, pg.KEYUP])

    async def _run(self) -> None:
        """游戏核心逻辑。"""

        delay: float = self._config['frame']['delay']
        screen_width: int = self._config['screen']['width']
        screen_height: int = self._config['screen']['height']
        # 初始化画布
        screen = pg.display.set_mode((screen_width, screen_height))
        # 加载背景图片
        bg = images.load('background.png').convert(screen)
        bg_rect = bg.get_rect()
        bg_rect.centerx = screen_width / 2
        # 加载游戏结束图片
        gameover = images.load('gameover.png').convert(screen)
        gameover_rect = gameover.get_rect()
        gameover_rect.centerx = screen_width / 2
        gameover_rect.centery = screen_height / 3
        gameover_handle = None
        # 加载玩家模型
        player = model.Player()
        enemy_born_interval = 0
        while 1:
            # 获取触发事件
            events = pg.event.get()
            # 处理事件
            for event in events:
                if event.type == pg.QUIT:
                    asyncio.tasks.current_task(self._loop).cancel()

            # 绘制背景
            screen.blit(bg, bg_rect)

            # 检测玩家状态
            if not player.alive:
                screen.blit(gameover, gameover_rect)
                if gameover_handle is None:
                    gameover_handle = self._loop.call_later(
                        1, asyncio.tasks.current_task(self._loop).cancel
                    )

            # 生成敌人
            enemy_born_interval += 1
            if enemy_born_interval > self._config['enemy']['born_interval']:
                model.Enemy(random.randint(1, 5))
                enemy_born_interval = 0

            # 刷新精灵组
            model.refresh(screen, events)

            # 刷新画布
            pg.display.flip()

            # 控制游戏帧率
            try:
                await asyncio.sleep(delay)
            except asyncio.CancelledError:
                break
        pg.quit()
        self._loop.stop()

    def run(self) -> None:
        """运行游戏。"""

        async def shutdown() -> None:
            await self._loop.shutdown_asyncgens()
            await self._loop.shutdown_default_executor()
        self._loop.create_task(self._run())
        try:
            self._loop.run_forever()
        finally:
            for task in asyncio.tasks.all_tasks(self._loop):
                task.cancel()
            self._loop.run_until_complete(shutdown())
            self._loop.close()
