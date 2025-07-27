"""
调用：soup3D.event
事件处理方法库，可添加如鼠标、键盘等事件的处理方式
"""

import typing
import pygame
from pygame.locals import *


__all__ : list[str] = [
    "bind", "check_event"
]

event_menu : dict[str, int] = {
    "on_close": pygame.QUIT,
    "key_down": pygame.KEYDOWN,
    "key_up": pygame.KEYUP,
    "mouse_down": pygame.MOUSEBUTTONDOWN,
    "mouse_up": pygame.MOUSEBUTTONUP,
    "mouse_move": pygame.MOUSEMOTION,
    "mouse_wheel": pygame.MOUSEWHEEL
}


bind_event_dic : dict[int, typing.Callable[[dict[str, any]], None]] = {}


def bind(event : str, funk : typing.Callable[[dict[str, any]], None]) -> None:
    """
    事件绑定函数
    :param event: 事件名称
    :param funk:  绑定的函数，每个事件只能绑定一个函数，函数
                  需要有1个参数
    :return: None
    """
    bind_event_dic[event_menu[event]] = funk


def check_event(events: list[pygame.event.Event]) -> None:
    for event in events:
        if event.type in bind_event_dic:
            bind_event_dic[event.type](event.dict)
