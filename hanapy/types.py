from typing import TYPE_CHECKING, Awaitable, Callable, Dict, List, Type, TypeVar, Union

if TYPE_CHECKING:
    from hanapy.runtime.events import Event

PlayerID = str

ET = TypeVar("ET", bound="Event")
EventHandler = Union[Callable[[ET], bool], Callable[[ET], Awaitable[bool]]]
EventHandlers = Dict[Type[ET], List[EventHandler]]
