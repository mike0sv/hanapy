import asyncio
import logging
from typing import Optional, Type

import aioconsole

from hanapy.core.action import Action, StateUpdate
from hanapy.core.config import GameResult
from hanapy.core.player import PlayerActor, PlayerMemo, PlayerView
from hanapy.runtime.base import ET, HanapyClient, HanapyServer
from hanapy.runtime.events import (
    ActionEvent,
    ActionVerificationEvent,
    GameEndedEvent,
    GameStartedEvent,
    MemoInitEvent,
    ObserveUpdateEvent,
    PlayerRegisteredEvent,
    StartGameEvent,
    UpdatePlayerMemoEvent,
    WaitForActionEvent,
)
from hanapy.types import PlayerID

logger = logging.getLogger(__name__)


class ServerPlayerActor(PlayerActor):
    def __init__(self, pid: PlayerID, server: HanapyServer):
        super().__init__(pid)
        self.pid = pid
        self.server = server

    async def on_game_start(self, view: PlayerView) -> PlayerMemo:
        await self.server.send_event(self.pid, GameStartedEvent(pid=self.pid, view=view))
        return (await self.server.wait_for_event(self.pid, MemoInitEvent)).memo

    async def wait_for_event_type(self, event_type: Type[ET]) -> ET:
        return await self.server.wait_for_event(self.pid, event_type)

    async def get_next_action(self, view: PlayerView) -> Action:
        await self.server.send_event(self.pid, WaitForActionEvent(pid=self.pid, view=view))
        return (await self.wait_for_event_type(ActionEvent)).action

    async def observe_update(self, view: PlayerView, update: StateUpdate, new_view: PlayerView) -> PlayerMemo:
        await self.server.send_event(
            self.pid, ObserveUpdateEvent(pid=self.pid, view=view, new_view=new_view, update=update)
        )
        return (await self.wait_for_event_type(UpdatePlayerMemoEvent)).memo

    async def on_game_end(self, view: PlayerView, game_result: GameResult):
        await self.server.send_event(self.pid, GameEndedEvent(pid=self.pid, view=view, game_result=game_result))

    async def on_valid_action(self):
        await self.server.send_event(self.pid, ActionVerificationEvent(pid=self.pid, success=True, msg=""))

    async def on_invalid_action(self, msg: str):
        await self.server.send_event(self.pid, ActionVerificationEvent(pid=self.pid, success=False, msg=msg))


class ClientPlayerProxy:
    def __init__(self, pid: PlayerID, client: HanapyClient, player: PlayerActor):
        self.pid = pid
        self.client = client
        self.player = player
        self.player_num: int = -1
        self.player_count = 1
        self.running = True

    async def observe(self):
        observe = await self.client.wait_for_event(ObserveUpdateEvent)
        memo = await self.player.observe_update(observe.view, observe.update, observe.new_view)
        await self.client.send_event(UpdatePlayerMemoEvent(pid=self.pid, memo=memo))

    async def game_ended_handler(self, event: GameEndedEvent) -> bool:
        await self.player.on_game_end(event.view, event.game_result)
        self.running = False
        return True

    async def player_registered_handler(self, event: PlayerRegisteredEvent) -> bool:
        logger.debug(f"Incrementing player count on {event}")
        self.player_count += 1
        return True

    async def run(self, is_host: bool, auto_start_players: Optional[int]):
        await self.client.connect()
        self.player_num = await self.client.register(self.pid)

        if is_host:
            await self.wait_for_start(auto_start_players)

        logger.debug("running client game proxy loop")
        game_started_event = await self.client.wait_for_event(GameStartedEvent)

        self.client.add_event_handler(GameEndedEvent, self.game_ended_handler)
        memo = await self.player.on_game_start(game_started_event.view)
        await self.client.send_event(MemoInitEvent(pid=self.pid, memo=memo))
        current_player = game_started_event.view.state.current_player
        player_count = game_started_event.view.config.player_count

        while self.running and await self.client.is_running():
            while current_player != self.player_num:
                await self.observe()
                current_player = (current_player + 1) % player_count
            wait = await self.client.wait_for_event(WaitForActionEvent)
            success = False
            while not success:
                action = await self.player.get_next_action(wait.view)
                await self.client.send_event(ActionEvent(pid=self.pid, action=action))
                verification = await self.client.wait_for_event(ActionVerificationEvent)
                if verification.success:
                    success = True
                    await self.player.on_valid_action()
                else:
                    await self.player.on_invalid_action(verification.msg)
            await self.observe()
            current_player = (current_player + 1) % player_count

    async def wait_for_start(self, auto_start_players: Optional[int]):
        # todo use callbacks or smth
        async def console_start():
            while True:
                msg = await aioconsole.ainput("Enter 'start'\n")
                if msg == "start":
                    break

        start_triggers = [console_start()]
        if auto_start_players is not None:
            self.client.add_event_handler(PlayerRegisteredEvent, self.player_registered_handler)

            async def wait_for_players():
                while True:
                    if self.player_count == auto_start_players:
                        break
                    await asyncio.sleep(0.1)

            print(f"Game will start when there are {auto_start_players} players")
            start_triggers.append(wait_for_players())
        finished, unfinished = await asyncio.wait(start_triggers, return_when=asyncio.FIRST_COMPLETED)
        for u in unfinished:
            u.cancel()
        await self.client.send_event(StartGameEvent(pid=self.pid))
