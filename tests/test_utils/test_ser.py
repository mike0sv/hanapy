import json
from typing import ClassVar

import msgspec

from hanapy.utils.ser import PolyStruct, dumps, loads


class A(PolyStruct):
    __root__: ClassVar = True
    f1: str


class B(A):
    __typename__: ClassVar = "b"

    f2: str


class C(A):
    __typename__: ClassVar = "c"
    f3: str


def test_dumps_loads():
    b = B(f1="f1", f2="f2")
    c = C(f1="f1", f3="f3")

    pb = dumps(b)
    assert json.loads(pb) == {"__typename__": "b", "f1": "f1", "f2": "f2"}
    pc = dumps(c)
    assert json.loads(pc) == {"__typename__": "c", "f1": "f1", "f3": "f3"}

    b2 = loads(A, pb)
    assert b2 == b
    c2 = loads(A, pc)
    assert c2 == c


def test_dumps_loads_nested():
    class D(msgspec.Struct):
        a: A

    c = C(f1="f1", f3="f3")
    d = D(a=c)

    pd = dumps(d)
    assert json.loads(pd) == {"a": {"__typename__": "c", "f1": "f1", "f3": "f3"}}

    d2 = loads(A, pd)
    assert d2 == d
