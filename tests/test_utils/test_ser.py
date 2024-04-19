import json
from typing import ClassVar, Dict

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
    class ASD:
        pass

    class D(msgspec.Struct):
        a: A
        # x: ASD

    c = C(f1="f1", f3="f3")
    d = D(a=c)

    pd = dumps(d)
    assert json.loads(pd) == {"a": {"__typename__": "c", "f1": "f1", "f3": "f3"}}

    d2 = loads(D, pd)
    assert d2 == d

    class E(A):
        __typename__: ClassVar = "e"
        d: D

    e = E(d=d, f1="")

    pe = dumps(e)
    assert json.loads(pe) == {"__typename__": "e", "d": {"a": {"__typename__": "c", "f1": "f1", "f3": "f3"}}, "f1": ""}
    e2 = loads(A, pe)
    assert e2 == e


def test_int_keys():
    class A(PolyStruct):
        __typename__: ClassVar = "a"
        a: Dict[int, int]

    a = A(a={1: 1})

    data = dumps(a)
    assert loads(A, data) == a
