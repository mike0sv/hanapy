from rich import print

from hanapy.runtime.events import ConnectionLostEvent, Event, GameStartedEvent, MessageEvent, PlayerRegisteredEvent


def console_event_handler(text_template: str, propagate: bool = True):
    def handler(event: Event):
        print(text_template.format(**event.__dict__))
        return propagate

    return handler


CONSOLE_EVENT_HANDLERS = {
    PlayerRegisteredEvent: console_event_handler("Player {pid} joined"),
    GameStartedEvent: console_event_handler("Game starting!"),
    ConnectionLostEvent: console_event_handler("Server shut down"),
    MessageEvent: console_event_handler("{text}", propagate=False),
}
