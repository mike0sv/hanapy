import logging
from typing import Type

import aioconsole

from hanapy.core.action import Action, StateUpdate
from hanapy.core.player import PlayerActor, PlayerMemo, PlayerView
from hanapy.runtime.base import ET, HanapyClient, HanapyServer
from hanapy.runtime.events import (
    ActionEvent,
    GameStartedEvent,
    ObserveUpdateEvent,
    StartGameEvent,
    UpdatePlayerMemoEvent,
    WaitForActionEvent,
)
from hanapy.runtime.types import PlayerID

logger = logging.getLogger(__name__)


class ServerPlayerActor(PlayerActor):
    def __init__(self, pid: PlayerID, server: HanapyServer):
        self.pid = pid
        self.server = server

    async def on_game_start(self, view: PlayerView):
        await self.server.send_event(self.pid, GameStartedEvent(pid=self.pid, view=view))

    async def wait_for_event_type(self, event_type: Type[ET]) -> ET:
        return await self.server.wait_for_event(self.pid, event_type)

    async def get_next_action(self, view: PlayerView) -> Action:
        # print(self.server.send_event)
        await self.server.send_event(self.pid, WaitForActionEvent(pid=self.pid, view=view))
        return (await self.wait_for_event_type(ActionEvent)).action

    async def observe_update(self, view: PlayerView, update: StateUpdate) -> PlayerMemo:
        await self.server.send_event(self.pid, ObserveUpdateEvent(pid=self.pid, view=view, update=update))
        return (await self.wait_for_event_type(UpdatePlayerMemoEvent)).memo


class ClientPlayerProxy:
    def __init__(self, pid: PlayerID, client: HanapyClient, player: PlayerActor):
        self.pid = pid
        self.client = client
        self.player = player
        self.player_num: int = -1

    async def observe(self):
        observe = await self.client.wait_for_event(ObserveUpdateEvent)
        memo = await self.player.observe_update(observe.view, observe.update)
        await self.client.send_event(UpdatePlayerMemoEvent(pid=self.pid, memo=memo))

    async def run(self, is_host: bool):
        await self.client.connect()
        self.player_num = await self.client.register(self.pid)

        # todo use callback
        if is_host:
            while True:
                msg = await aioconsole.ainput("Enter 'start'\n")
                if msg == "start":
                    await self.client.send_event(StartGameEvent(pid=self.pid))
                    break

        logger.debug("running client game proxy loop")
        game_started_event = await self.client.wait_for_event(GameStartedEvent)
        await self.player.on_game_start(game_started_event.view)
        current_player = game_started_event.view.state.current_player
        max_players = game_started_event.view.state.config.players

        while await self.client.is_running():
            while current_player != self.player_num:
                await self.observe()
                current_player = (current_player + 1) % max_players
            wait = await self.client.wait_for_event(WaitForActionEvent)
            action = await self.player.get_next_action(wait.view)
            await self.client.send_event(ActionEvent(pid=self.pid, action=action))
            await self.observe()
            current_player = (current_player + 1) % max_players
