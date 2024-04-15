from functools import lru_cache
from typing import Any, ClassVar, Dict, Type, TypeVar

import msgspec


@lru_cache
def __get_root_type__(cls: Type["PolyStruct"]) -> Type["PolyStruct"]:
    for cls_ in cls.mro():
        if not issubclass(cls_, PolyStruct):
            continue
        if cls_.__is_root__():
            return cls_
    return PolyStruct


class PolyStruct(msgspec.Struct):
    __typename__: ClassVar[str] = ""
    __root__: ClassVar[bool] = False
    __class_map__: ClassVar[Dict[str, Type["PolyStruct"]]] = {}

    def __init_subclass__(cls, *args, **kwargs) -> None:
        super().__init_subclass__(*args, **kwargs)
        if cls.__typename__ and not cls.__is_root__():
            root = __get_root_type__(cls)  # type: ignore[arg-type]
            root.__class_map__[cls.__typename__] = cls

    @classmethod
    def __is_root__(cls) -> bool:
        return bool(cls.__dict__.get("__root__"))

    def to_dict(self) -> Any:
        return msgspec.to_builtins(self)


def dumps(obj: PolyStruct, module=msgspec.json) -> Any:
    data = msgspec.to_builtins(obj)
    data["__typename__"] = obj.__typename__
    return module.encode(data)


T = TypeVar("T", bound=PolyStruct)


def loads(cls: Type[T], data: Any, module=msgspec.json) -> T:
    obj: dict = module.decode(data)
    if cls.__is_root__():
        typename = obj.pop("__typename__", None)
        if typename is not None:
            cls = cls.__class_map__[typename]  # type: ignore[assignment]
    return msgspec.convert(obj, cls)
