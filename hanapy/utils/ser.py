from functools import lru_cache
from typing import Any, ClassVar, Dict, Type, TypeVar, Union

import msgspec
from ordered_set import OrderedSet


@lru_cache
def __get_root_type__(cls: Type["PolyStruct"]) -> Type["PolyStruct"]:
    for cls_ in cls.mro():
        if not issubclass(cls_, PolyStruct):
            continue
        if cls_.__is_root__():
            return cls_
    return PolyStruct


class PolyStructMeta(type):
    __typename__: str
    __struct__: Type[msgspec.Struct]

    def __new__(cls, name, bases, namespace):
        inst = super().__new__(cls, name, bases, namespace)
        namespace = namespace.copy()
        for drop in ["__classcell__", "__init__", "__init_subclass__"]:
            if drop in namespace:
                del namespace[drop]

        base_cls = msgspec.Struct
        for cls_ in inst.mro():
            if hasattr(cls_, "__struct__"):
                base_cls = cls_.__struct__
                break
        if "__annotations__" not in namespace:
            namespace["__annotations__"] = {}
        namespace["__annotations__"]["__typename__"] = str
        namespace["__typename__"] = inst.__typename__
        inst.__struct__ = type(inst.__name__ + "_Struct", (base_cls,), namespace, kw_only=True)
        return inst


class PolyStruct(metaclass=PolyStructMeta):
    __typename__: ClassVar[str] = ""
    __root__: ClassVar[bool] = True
    __class_map__: ClassVar[Dict[str, Type["PolyStruct"]]] = {}
    __struct__: ClassVar[Type[msgspec.Struct]]

    def __init__(self, **kwargs):
        for field, default in zip(
            self.__struct__.__struct_fields__,
            self.__struct__.__struct_defaults__,  # type: ignore[attr-defined]
        ):
            if field == "__typename__":
                continue

            if default is msgspec.NODEFAULT and field not in kwargs:
                raise ValueError(f"Missing {field} field for {self.__class__.__name__}")
            setattr(self, field, kwargs.pop(field, default))
        if len(kwargs) != 0:
            raise ValueError(f"Extra fields for {self.__class__.__name__}: {list(kwargs)}")

    def __init_subclass__(cls, *args, **kwargs) -> None:
        super().__init_subclass__(*args, **kwargs)
        # cls.__struct__ = type(cls.__name__, (cls, msgspec.Struct), cls)
        if not cls.__is_root__():
            if not cls.__typename__:
                raise ValueError(f"{cls.__name__} does not have __typename__")
            root = __get_root_type__(cls)
            root.__class_map__[cls.__typename__] = cls

    @classmethod
    def __is_root__(cls) -> bool:
        return bool(cls.__dict__.get("__root__"))

    def to_dict(self) -> Any:
        data = msgspec.to_builtins(self, enc_hook=encode)
        return data

    def __eq__(self, other):
        if self.__class__ != other.__class__:
            return False
        return self.__dict__ == other.__dict__

    def __str__(self):
        fields = ",".join(f"{k}={v}" for k, v in self.__dict__.items())
        return f"{self.__class__.__name__}[{fields}]"

    def __repr__(self):
        return str(self)


def encode(value):
    # print("encode", value)
    if isinstance(value, PolyStruct):
        return value.__struct__(**value.__dict__)
    if isinstance(value, OrderedSet):
        return list(value)
    raise NotImplementedError


def decode(cls: Type, value):
    if isinstance(cls, type) and issubclass(cls, PolyStruct):
        if cls.__is_root__():
            typename = value.pop("__typename__", None)
            if typename is not None:
                cls = cls.__class_map__[typename]
        struct = msgspec.convert(value, type=cls.__struct__, str_keys=True, dec_hook=decode)
        return cls(**{f: getattr(struct, f) for f in struct.__struct_fields__ if f != "__typename__"})
    raise NotImplementedError


T = TypeVar("T", bound=Union[PolyStruct, msgspec.Struct])


def dumps(obj: Union[T, Any], module=msgspec.json) -> Any:
    try:
        data = msgspec.to_builtins(obj, enc_hook=encode)
    except TypeError:
        print(dict(obj.__dict__))
        raise
    return module.encode(data)


def loads(cls: Type[T], data: Any, module=msgspec.json) -> T:
    obj: dict = module.decode(data, type=cls, dec_hook=decode)

    return msgspec.convert(obj, cls)
