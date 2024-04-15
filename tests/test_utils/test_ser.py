import json
from typing import ClassVar

from hanapy.utils.ser import PolyStruct, dumps, loads


def test_dumps_loads():
    class A(PolyStruct):
        __root__: ClassVar = True
        f1: str

    class B(A):
        __typename__: ClassVar = "b"

        f2: str

    class C(A):
        __typename__: ClassVar = "c"
        f3: str

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
