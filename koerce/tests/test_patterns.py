import pytest
import sys
from koerce.patterns import (
    NoMatch,
    Anything,
    Nothing,
    IdenticalTo,
    EqualTo,
    InstanceOf,
    LazyInstanceOf,
    GenericInstanceOf,
    GenericInstanceOf1,
    Replace,
    GenericInstanceOf2,
    GenericInstanceOfN,
    Option,
    ObjectOf,
    MappingOf,
    NoneOf,
    ObjectOfX,
    Pattern,
    SomeOf,
    ListOf,
    PatternList,
    Not,
    SequenceOf,
    AnyOf,
    If,
    AllOf,
    TypeOf,
    IsIn,
    AsType,
    GenericCoercedTo,
    pattern,
    CoercedTo,
    TupleOf,
    DictOf,
    CoercionError,
    Capture,
)
from koerce.builders import Variable, Call, Deferred
from dataclasses import dataclass
from typing import (
    TypeVar,
    Generic,
    Any,
    Literal,
    Callable,
    Sequence,
    Optional,
    Union,
    List,
    Annotated,
)
from koerce.sugar import match


class Min(Pattern):
    __slots__ = ("min",)

    def __init__(self, min):
        self.min = min

    def __repr__(self):
        return f"{self.__class__.__name__}({self.min})"

    def apply(self, value, context):
        if value >= self.min:
            return value
        else:
            return NoMatch

    def equals(self, other):
        return self.min == other.min


various_values = [1, "1", 1.0, object, False, None]


@pytest.mark.parametrize("value", various_values)
def test_anything(value):
    assert Anything().apply(value) == value


@pytest.mark.parametrize("value", various_values)
def test_nothing(value):
    assert Nothing().apply(value) is NoMatch


@pytest.mark.parametrize("value", various_values)
def test_identical_to(value):
    assert IdenticalTo(value).apply(value) == value
    assert IdenticalTo(value).apply(2) is NoMatch
    assert IdenticalTo(value).apply("2") is NoMatch
    assert IdenticalTo(value).apply(True) is NoMatch


@pytest.mark.parametrize(
    ["a", "b", "expected"],
    [
        (1, 1, True),
        (1, 2, False),
        ("1", "1", True),
        ("1", "2", False),
        (1.0, 1.0, True),
        (1.0, 2.0, False),
        (1.0, 1, True),
        (1.0, 2, False),
        (object, object, True),
        ("", "", True),
        (False, False, True),
        (set(), set(), True),
        (set(), frozenset(), True),
        (set(), [], False),
    ],
)
def test_equal_to(a, b, expected):
    pattern = EqualTo(a)
    if expected:
        assert pattern.apply(b) is b
    else:
        assert pattern.apply(b) is NoMatch


@pytest.mark.parametrize(
    ["typ", "value", "expected"],
    [
        (int, 1, True),
        (int, 1.0, False),
        (str, "1", True),
        (str, 1, False),
        (int, True, True),
        (int, False, True),
        (bool, True, True),
        (bool, False, True),
        (bool, 1, False),
        (bool, 0, False),
        (list, [1, 2], True),
        (list, (1, 2), False),
    ],
)
def test_instance_of(typ, value, expected):
    pattern = InstanceOf(typ)
    if expected:
        assert pattern.apply(value) is value
    else:
        assert pattern.apply(value) is NoMatch


@pytest.mark.parametrize(
    ("typ", "value", "expected"),
    [
        (int, 1, True),
        (int, 1.0, False),
        (str, "1", True),
        (str, 1, False),
        (int, True, False),
        (int, False, False),
        (bool, True, True),
        (bool, False, True),
        (bool, 1, False),
        (bool, 0, False),
        (list, [1, 2], True),
        (list, (1, 2), False),
    ],
)
def test_type_of(typ, value, expected):
    pattern = TypeOf(typ)
    if expected:
        assert pattern.apply(value) is value
    else:
        assert pattern.apply(value) is NoMatch


def test_lazy_instance_of():
    # pick a rarely used stdlib module
    assert "graphlib" not in sys.modules
    p = LazyInstanceOf("graphlib.TopologicalSorter")
    assert "graphlib" not in sys.modules

    assert p.apply(1) is NoMatch
    assert "graphlib" not in sys.modules

    import graphlib

    sorter = graphlib.TopologicalSorter()
    assert p.apply(sorter) is sorter
    assert p.apply("foo") is NoMatch


# covariance is reqired at the moment
T = TypeVar("T", covariant=True)
S = TypeVar("S", covariant=True)
U = TypeVar("U", covariant=True)


@dataclass
class My(Generic[T, S]):
    a: T
    b: S
    c: str


@dataclass
class My1(Generic[T]):
    a: T


@dataclass
class My2(Generic[T, S]):
    a: T
    b: S


@dataclass
class My3(Generic[T, S, U]):
    a: T
    b: S
    c: U


def test_generic_instance_of():
    p = GenericInstanceOf(My1[int])
    assert isinstance(p, GenericInstanceOf1)

    p = GenericInstanceOf(My2[int, float])
    assert isinstance(p, GenericInstanceOf2)

    p = GenericInstanceOf(My3[int, float, str])
    assert isinstance(p, GenericInstanceOfN)


def test_generic_instance_of_n():
    p = GenericInstanceOfN(My[int, Any])
    assert p.apply(v := My(1, 2, "3")) is v

    p = GenericInstanceOfN(My[int, int])
    assert p.apply(v := My(1, 2, "3")) is v

    p = GenericInstanceOfN(My[int, float])
    assert p.apply(My(1, 2, "3")) is NoMatch
    assert p.apply(v := My(1, 2.0, "3")) is v

    MyAlias = My[T, str]
    p = GenericInstanceOfN(MyAlias[str])
    assert p.apply(v := My("1", "2", "3")) is v


def test_generic_instance_of_1():
    p = GenericInstanceOf1(My1[int])
    assert p.apply(v := My1(1)) is v
    assert p.apply(My1(1.0)) is NoMatch


def test_generic_instance_of_2():
    p = GenericInstanceOf2(My2[int, float])
    assert p.apply(My2(1, 2)) is NoMatch
    assert p.apply(v := My2(1, 2.0)) is v


# def test_as():
#     class MyInt(int):
#         @classmethod
#         def __coerce__(cls, other):
#             return MyInt(int(other))

#     class MyGenericInt(Generic[T]):
#         value: T

#         @classmethod
#         def __coerce__(cls, other, T):
#             return cls(T(other))

#     assert isinstance(As(int), AsType)
#     assert isinstance(As(MyInt), CoercedTo)
#     assert isinstance(As(MyGenericInt[int]), GenericCoercedTo)


def test_as_type():
    p = AsType(int)
    assert p.apply(1) == 1
    assert p.apply("1") == 1
    assert p.apply("a") is NoMatch


def test_coerced_to():
    class MyInt(int):
        @classmethod
        def __coerce__(cls, other):
            return MyInt(MyInt(other) + 1)

    p = CoercedTo(MyInt)
    assert p.apply(1, context={}) == 2
    assert p.apply("1", context={}) == 2
    with pytest.raises(ValueError):
        p.apply("foo", context={})


def test_generic_coerced_to():
    class DataType:
        def __eq__(self, other):
            return type(self) is type(other)

    class Integer(DataType):
        pass

    class String(DataType):
        pass

    class DataShape:
        def __eq__(self, other):
            return type(self) is type(other)

    class Scalar(DataShape):
        pass

    class Array(DataShape):
        pass

    class Value(Generic[T, S]):
        @classmethod
        def __coerce__(cls, value, T, S):
            if T is String:
                value = str(value)
            elif T is Integer:
                value = int(value)
            else:
                raise CoercionError(f"Cannot coerce {value} to {T}")
            return cls(value, T())

        @property
        def dtype(self) -> T: ...

        @property
        def shape(self) -> S: ...

    class Literal(Value[T, Scalar]):
        __slots__ = ("_value", "_dtype")

        def __init__(self, value, dtype):
            self._value = value
            self._dtype = dtype

        @property
        def dtype(self) -> T:
            return self._dtype

        @property
        def shape(self) -> DataShape:
            return Scalar()

        def __eq__(self, other):
            return (
                type(self) is type(other)
                and self._value == other._value
                and self._dtype == other._dtype
            )

    s = Literal("foo", String())
    i = Literal(1, Integer())

    p = GenericInstanceOf(Literal[String])
    assert p.apply(s) is s
    assert p.apply(i) is NoMatch

    p = GenericCoercedTo(Literal[String])
    assert p.apply("foo") == s
    assert p.apply(1) == Literal("1", String())


def test_not():
    p = Not(InstanceOf(int))
    p1 = ~InstanceOf(int)

    assert p == p1
    assert p.apply(1, context={}) is NoMatch
    assert p.apply("foo", context={}) == "foo"
    # assert p.describe() == "anything except an int"
    # assert p.describe(plural=True) == "anything except ints"


def test_any_of():
    p = AnyOf(InstanceOf(int), InstanceOf(str))
    p1 = InstanceOf(int) | InstanceOf(str)

    assert p == p1
    assert p.apply(1, context={}) == 1
    assert p.apply("foo", context={}) == "foo"
    assert p.apply(1.0, context={}) is NoMatch
    # assert p.describe() == "an int or a str"
    # assert p.describe(plural=True) == "ints or strs"

    p = AnyOf(InstanceOf(int), InstanceOf(str), InstanceOf(float))
    # assert p.describe() == "an int, a str or a float"


def test_all_of():
    def negative(_):
        return _ < 0

    p = AllOf(InstanceOf(int), If(negative))
    p1 = InstanceOf(int) & If(negative)

    assert p == p1
    assert p.apply(1) is NoMatch
    assert p.apply(-1) == -1
    assert p.apply(1.0) is NoMatch
    # assert p.describe() == "an int then a value that satisfies negative()"

    p = AllOf(InstanceOf(int), AsType(float), AsType(str))
    assert p.apply(1) == "1.0"
    assert p.apply(1.0) is NoMatch
    assert p.apply("1") is NoMatch
    # assert p.describe() == "an int, coercible to a float then coercible to a str"


def test_if_function():
    def checker(_):
        return _ == 10

    p = If(checker)
    assert p.apply(10) == 10
    assert p.apply(11) is NoMatch
    # assert p.describe() == "a value that satisfies checker()"
    # assert p.describe(plural=True) == "values that satisfy checker()"


def test_isin():
    p = IsIn([1, 2, 3])
    assert p.apply(1) == 1
    assert p.apply(4) is NoMatch
    # assert p.describe() == "in {1, 2, 3}"
    # assert p.describe(plural=True) == "in {1, 2, 3}"


def test_sequence_of():
    p = SequenceOf(InstanceOf(str), list)
    assert p.apply(["foo", "bar"]) == ["foo", "bar"]
    assert p.apply([1, 2]) is NoMatch
    assert p.apply(1) is NoMatch
    assert p.apply("string") is NoMatch
    # assert p.describe() == "a list of strs"
    # assert p.describe(plural=True) == "lists of strs"

    p = SequenceOf(InstanceOf(int), tuple)
    assert p.apply((1, 2)) == (1, 2)
    assert p.apply([1, 2]) == (1, 2)
    assert p.apply([1, 2, "3"]) is NoMatch


class CustomDict(dict):
    pass


def test_mapping_of():
    p = MappingOf(InstanceOf(str), InstanceOf(int))
    assert p.apply({"foo": 1, "bar": 2}, context={}) == {"foo": 1, "bar": 2}
    assert p.apply({"foo": 1, "bar": "baz"}, context={}) is NoMatch
    assert p.apply(1, context={}) is NoMatch

    p = MappingOf(InstanceOf(str), InstanceOf(str), CustomDict)
    assert p.apply({"foo": "bar"}, context={}) == CustomDict({"foo": "bar"})
    assert p.apply({"foo": 1}, context={}) is NoMatch


def test_capture():
    ctx = {}

    p = Capture("result", InstanceOf(int))
    assert p.apply("10", context=ctx) is NoMatch
    assert ctx == {}

    assert p.apply(12, context=ctx) == 12
    assert ctx == {"result": 12}


def test_none_of():
    def negative(x):
        return x < 0

    p = NoneOf(InstanceOf(int), If(negative))
    assert p.apply(1.0, context={}) == 1.0
    assert p.apply(-1.0, context={}) is NoMatch
    assert p.apply(1, context={}) is NoMatch
    #assert p.describe() == "anything except an int or a value that satisfies negative()"


def test_generic_sequence_of():
    class MyList(list):
        @classmethod
        def __coerce__(cls, value, T=...):
            return cls(value)

    p = SequenceOf(InstanceOf(str), MyList)
    assert p.apply(["foo", "bar"], context={}) == MyList(["foo", "bar"])
    assert p.apply("string", context={}) is NoMatch

    p = SequenceOf(InstanceOf(str), tuple)
    assert p == SequenceOf(InstanceOf(str), tuple)
    assert p.apply(("foo", "bar"), context={}) == ("foo", "bar")
    assert p.apply([], context={}) == ()


def test_list_of():
    p = ListOf(InstanceOf(str))
    assert isinstance(p, SequenceOf)
    assert p.apply(["foo", "bar"], context={}) == ["foo", "bar"]
    assert p.apply([1, 2], context={}) is NoMatch
    assert p.apply(1, context={}) is NoMatch
    # assert p.describe() == "a list of strs"
    # assert p.describe(plural=True) == "lists of strs"


def test_pattern_sequence():
    p = PatternList((InstanceOf(str), InstanceOf(int), InstanceOf(float)))
    assert p.apply(("foo", 1, 1.0), context={}) == ["foo", 1, 1.0]
    assert p.apply(["foo", 1, 1.0], context={}) == ["foo", 1, 1.0]
    assert p.apply(1, context={}) is NoMatch
    # assert p.describe() == "a tuple of (a str, an int, a float)"
    # assert p.describe(plural=True) == "tuples of (a str, an int, a float)"

    p = PatternList((InstanceOf(str),))
    assert p.apply(("foo",), context={}) == ["foo"]
    assert p.apply(("foo", "bar"), context={}) is NoMatch


class Foo:
    __match_args__ = ("a", "b")

    def __init__(self, a, b):
        self.a = a
        self.b = b

    def __eq__(self, other):
        return type(self) is type(other) and self.a == other.a and self.b == other.b


class Bar:
    __match_args__ = ("c", "d")

    def __init__(self, c, d):
        self.c = c
        self.d = d

    def __eq__(self, other):
        return type(self) is type(other) and self.c == other.c and self.d == other.d


def test_object_pattern():
    p = ObjectOf(Foo, 1, b=2)
    o = Foo(1, 2)
    assert p.apply(o) is o
    assert p.apply(Foo(1, 3)) is NoMatch

    p = ObjectOf(Foo, 1, lambda x: x * 2)
    assert p.apply(Foo(1, 2)) == Foo(1, 4)


def test_object_pattern_complex_type():
    p = ObjectOf(Not(Foo), 1, 2)
    o = Bar(1, 2)

    # test that the pattern isn't changing the input object if none of
    # its arguments are changed by subpatterns
    assert p.apply(o) is o
    assert p.apply(Foo(1, 2)) is NoMatch
    assert p.apply(Bar(1, 3)) is NoMatch

    p = ObjectOf(Not(Foo), 1, b=2)
    assert p.apply(Bar(1, 2)) is NoMatch


def test_object_pattern_from_instance_of():
    class MyType:
        __match_args__ = ("a", "b")

        def __init__(self, a, b):
            self.a = a
            self.b = b

    p = pattern(MyType)
    assert p == InstanceOf(MyType)

    p_call = p(1, 2)
    assert p_call == ObjectOf(MyType, 1, 2)


def test_object_pattern_from_coerced_to():
    class MyCoercibleType:
        __match_args__ = ("a", "b")

        def __init__(self, a, b):
            self.a = a
            self.b = b

        @classmethod
        def __coerce__(cls, other):
            a, b = other
            return cls(a, b)

    p = CoercedTo(MyCoercibleType)
    p_call = p(1, 2)
    assert p_call == ObjectOfX(p, 1, 2)


def test_object_pattern_matching_order():
    class Foo:
        __match_args__ = ("a", "b", "c")

        def __init__(self, a, b, c):
            self.a = a
            self.b = b
            self.c = c

        def __eq__(self, other):
            return (
                type(self) is type(other)
                and self.a == other.a
                and self.b == other.b
                and self.c == other.c
            )

    a = Variable("a")
    p = ObjectOf(Foo, Capture(a, InstanceOf(int)), c=a)

    assert p.apply(Foo(1, 2, 3)) is NoMatch
    assert p.apply(Foo(1, 2, 1)) == Foo(1, 2, 1)


def test_object_pattern_matching_dictionary_field():
    a = Bar(1, dict())
    b = Bar(1, {})
    c = Bar(1, None)
    d = Bar(1, {"foo": 1})

    pattern = ObjectOf(Bar, 1, d={})
    assert pattern.apply(a) is a
    assert pattern.apply(b) is b
    assert pattern.apply(c) is NoMatch

    pattern = ObjectOf(Bar, 1, d=None)
    assert pattern.apply(a) is NoMatch
    assert pattern.apply(c) is c

    pattern = ObjectOf(Bar, 1, d={"foo": 1})
    assert pattern.apply(a) is NoMatch
    assert pattern.apply(d) is d


def test_object_pattern_requires_its_arguments_to_match():
    class Empty:
        __match_args__ = ()

    msg = "The type to match has fewer `__match_args__`"
    with pytest.raises(ValueError, match=msg):
        ObjectOf(Empty, 1)

    # if the type matcher (first argument of Object) receives a generic pattern
    # instead of an explicit type, the validation above cannot occur, so test
    # the the pattern still doesn't match when it requires more positional
    # arguments than the object `__match_args__` has
    pattern = ObjectOf(InstanceOf(Empty), "a")
    assert pattern.apply(Empty()) is NoMatch

    pattern = ObjectOf(InstanceOf(Empty), a="a")
    assert pattern.apply(Empty()) is NoMatch


def test_pattern_list():
    p = PatternList([1, 2, InstanceOf(int), SomeOf(...)])
    assert p.apply([1, 2, 3, 4, 5], context={}) == [1, 2, 3, 4, 5]
    assert p.apply([1, 2, 3, 4, 5, 6], context={}) == [1, 2, 3, 4, 5, 6]
    assert p.apply([1, 2, 3, 4], context={}) == [1, 2, 3, 4]
    assert p.apply([1, 2, "3", 4], context={}) is NoMatch

    # subpattern is a simple pattern
    p = PatternList([1, 2, AsType(int), SomeOf(...)])
    assert p.apply([1, 2, 3.0, 4.0, 5.0], context={}) == [1, 2, 3, 4.0, 5.0]

    # subpattern is a sequence
    # p = PatternList([1, 2, 3, SomeOf(AsType(int), at_least=1)])
    # assert p.apply([1, 2, 3, 4.0, 5.0], context={}) == [1, 2, 3, 4, 5]


def test_pattern_list_from_tuple_typehint():
    p = Pattern.from_typehint(tuple[str, int, float])
    assert p == PatternList(
        [InstanceOf(str), InstanceOf(int), InstanceOf(float)], type=tuple
    )
    assert p.apply(["foo", 1, 2.0], context={}) == ("foo", 1, 2.0)
    assert p.apply(("foo", 1, 2.0), context={}) == ("foo", 1, 2.0)
    assert p.apply(["foo", 1], context={}) is NoMatch
    assert p.apply(["foo", 1, 2.0, 3.0], context={}) is NoMatch

    class MyTuple(tuple):
        pass

    p = Pattern.from_typehint(MyTuple[int, bool])
    assert p == PatternList([InstanceOf(int), InstanceOf(bool)], type=MyTuple)
    assert p.apply([1, True], context={}) == MyTuple([1, True])
    assert p.apply(MyTuple([1, True]), context={}) == MyTuple([1, True])
    assert p.apply([1, 2], context={}) is NoMatch


def test_pattern_list_unpack():
    integer = pattern(int)
    floating = pattern(float)

    assert match([1, 2, *floating], [1, 2, 3]) is NoMatch
    assert match([1, 2, *floating], [1, 2, 3.0]) == [1, 2, 3.0]
    assert match([1, 2, *floating], [1, 2, 3.0, 4.0]) == [1, 2, 3.0, 4.0]
    assert match([1, *floating, *integer], [1, 2.0, 3.0, 4]) == [1, 2.0, 3.0, 4]
    assert match([1, *floating, *integer], [1, 2.0, 3.0, 4, 5]) == [
        1,
        2.0,
        3.0,
        4,
        5,
    ]
    assert match([1, *floating, *integer], [1, 2.0, 3, 4.0]) is NoMatch


def test_matching():
    assert match("foo", "foo") == "foo"
    assert match("foo", "bar") is NoMatch

    assert match(InstanceOf(int), 1) == 1
    assert match(InstanceOf(int), "foo") is NoMatch

    assert Capture("pi", InstanceOf(float)) == "pi" @ InstanceOf(float)
    assert Capture("pi", InstanceOf(float)) == "pi" @ InstanceOf(float)

    assert match(Capture("pi", InstanceOf(float)), 3.14, ctx := {}) == 3.14  # noqa: RUF018
    assert ctx == {"pi": 3.14}
    assert match("pi" @ InstanceOf(float), 3.14, ctx := {}) == 3.14  # noqa: RUF018
    assert ctx == {"pi": 3.14}

    assert match("pi" @ InstanceOf(float), 3.14, ctx := {}) == 3.14  # noqa: RUF018
    assert ctx == {"pi": 3.14}

    assert match(InstanceOf(int) | InstanceOf(float), 3) == 3
    assert match(InstanceOf(object) & InstanceOf(float), 3.14) == 3.14


# def test_replace_passes_matched_value_as_underscore():
#     class MyInt:
#         def __init__(self, value):
#             self.value = value

#         def __eq__(self, other):
#             return self.value == other.value

#     p = InstanceOf(int) >> Call(MyInt, value=_)
#     assert p.apply(1, context={}) == MyInt(1)


def test_replace_in_nested_object_pattern():
    # simple example using reference to replace a value
    b = Variable("b")
    p = ObjectOf(Foo, 1, b=Replace(Anything(), b))
    f = p.apply(Foo(1, 2), {"b": 3})
    assert f.a == 1
    assert f.b == 3

    # nested example using reference to replace a value
    d = Variable("d")
    p = ObjectOf(Foo, 1, b=ObjectOf(Bar, 2, d=Replace(Anything(), d)))
    g = p.apply(Foo(1, Bar(2, 3)), {"d": 4})
    assert g.b.c == 2
    assert g.b.d == 4

    # nested example using reference to replace a value with a captured value
    p = ObjectOf(
        Foo,
        1,
        b=Replace(ObjectOf(Bar, 2, d="d" @ Anything()), lambda _, d: Foo(-1, b=d)),
    )
    h = p.apply(Foo(1, Bar(2, 3)), {})
    assert isinstance(h, Foo)
    assert h.a == 1
    assert isinstance(h.b, Foo)
    assert h.b.b == 3

    d = Variable("d")
    p = ObjectOf(Foo, 1, b=ObjectOf(Bar, 2, d=d @ Anything()) >> Call(Foo, -1, b=d))
    h1 = p.apply(Foo(1, Bar(2, 3)), {})
    assert isinstance(h1, Foo)
    assert h1.a == 1
    assert isinstance(h1.b, Foo)
    assert h1.b.b == 3


# def test_replace_decorator():
#     @replace(int)
#     def sub(_):
#         return _ - 1

#     assert match(sub, 1) == 0
#     assert match(sub, 2) == 1


def test_replace_using_deferred():
    x = Deferred(Variable("x"))
    y = Deferred(Variable("y"))

    pat = ObjectOf(Foo, Capture(x), b=Capture(y)) >> Call(Foo, x, b=y)
    assert pat.apply(Foo(1, 2)) == Foo(1, 2)

    pat = ObjectOf(Foo, Capture(x), b=Capture(y)) >> Call(Foo, x, b=(y + 1) * x)
    assert pat.apply(Foo(2, 3)) == Foo(2, 8)

    pat = ObjectOf(Foo, "x" @ Anything(), y @ InstanceOf(Bar)) >> Call(
        Foo, x, b=y.c + y.d
    )
    assert pat.apply(Foo(1, Bar(2, 3))) == Foo(1, 5)


def test_matching_sequence_pattern():
    assert match([], []) == []
    assert match([], [1]) is NoMatch

    assert match([1, 2, 3, 4, SomeOf(...)], list(range(1, 9))) == list(range(1, 9))
    assert match([1, 2, 3, 4, SomeOf(...)], list(range(1, 3))) is NoMatch
    assert match([1, 2, 3, 4, SomeOf(...)], list(range(1, 5))) == list(range(1, 5))
    assert match([1, 2, 3, 4, SomeOf(...)], list(range(1, 6))) == list(range(1, 6))

    assert match([SomeOf(...), 3, 4], list(range(5))) == list(range(5))
    assert match([SomeOf(...), 3, 4], list(range(3))) is NoMatch

    assert match([0, 1, SomeOf(...), 4], list(range(5))) == list(range(5))
    assert match([0, 1, SomeOf(...), 4], list(range(4))) is NoMatch

    assert match([SomeOf(...)], list(range(5))) == list(range(5))
    assert match([SomeOf(...), 2, 3, 4, SomeOf(...)], list(range(8))) == list(range(8))


def test_matching_sequence_pattern_keeps_original_type():
    assert match([1, 2, 3, 4, SomeOf(...)], tuple(range(1, 9))) == list(range(1, 9))
    assert match((1, 2, 3, SomeOf(...)), [1, 2, 3, 4, 5]) == (1, 2, 3, 4, 5)


def test_matching_sequence_with_captures():
    x = Deferred(Variable("x"))

    v = list(range(1, 9))
    assert match([1, 2, 3, 4, SomeOf(...)], v) == v
    assert match([1, 2, 3, 4, "rest" @ SomeOf(...)], v, ctx := {}) == v  # noqa: RUF018
    assert ctx == {"rest": [5, 6, 7, 8]}

    v = list(range(5))
    assert match([0, 1, x @ SomeOf(...), 4], v, ctx := {}) == v  # noqa: RUF018
    assert ctx == {"x": [2, 3]}
    assert match([0, 1, "var" @ SomeOf(...), 4], v, ctx := {}) == v  # noqa: RUF018
    assert ctx == {"var": [2, 3]}

    p = [
        0,
        1,
        "ints" @ SomeOf(int),
        SomeOf("last_float" @ InstanceOf(float)),
        6,
    ]
    v = [0, 1, 2, 3, 4.0, 5.0, 6]
    assert match(p, v, ctx := {}) == v  # noqa: RUF018
    assert ctx == {"ints": [2, 3], "last_float": 5.0}


def test_matching_sequence_remaining():
    three = [1, 2, 3]
    four = [1, 2, 3, 4]
    five = [1, 2, 3, 4, 5]

    assert match([1, 2, 3, SomeOf(int, at_least=1)], four) == four
    assert match([1, 2, 3, SomeOf(int, at_least=1)], three) is NoMatch
    assert match([1, 2, 3, SomeOf(int)], three) == three
    assert match([1, 2, 3, SomeOf(int, at_most=1)], three) == three
    # assert match([1, 2, 3, SomeOf(InstanceOf(int) & Between(0, 10))], five) == five
    # assert match([1, 2, 3, SomeOf(InstanceOf(int) & Between(0, 4))], five) is NoMatch
    assert match([1, 2, 3, SomeOf(int, at_least=2)], four) is NoMatch
    assert match([1, 2, 3, "res" @ SomeOf(int, at_least=2)], five, ctx := {}) == five  # noqa: RUF018
    assert ctx == {"res": [4, 5]}


def test_matching_sequence_complicated():
    pat = [
        1,
        "a" @ SomeOf(InstanceOf(int) & If(lambda x: x < 10)),
        4,
        "b" @ SomeOf(...),
        8,
        9,
    ]
    expected = {
        "a": [2, 3],
        "b": [5, 6, 7],
    }
    assert match(pat, range(1, 10), ctx := {}) == list(range(1, 10))  # noqa: RUF018
    assert ctx == expected

    pat = [1, 2, Capture("remaining", SomeOf(...))]
    expected = {"remaining": [3, 4, 5, 6, 7, 8, 9]}
    assert match(pat, range(1, 10), ctx := {}) == list(range(1, 10))  # noqa: RUF018
    assert ctx == expected

    v = [0, [1, 2, "3"], [1, 2, "4"], 3]
    assert match([0, SomeOf([1, 2, str]), 3], v) == v


from koerce.patterns import SomeChunksOf


def test_pattern_sequence_with_nested_some_of():
    assert SomeChunksOf(1, 2) == SomeOf(1, 2)

    ctx = {}
    res = match([0, "subseq" @ SomeChunksOf(1, 2), 3], [0, 1, 2, 1, 2, 3], ctx)
    assert res == [0, 1, 2, 1, 2, 3]
    assert ctx == {"subseq": [1, 2, 1, 2]}

    res = match([0, "subseq" @ SomeOf(1, 2), 3], [0, 1, 2, 3], ctx)
    assert res == [0, 1, 2, 3]
    assert ctx == {"subseq": [1, 2]}

    assert match([0, SomeOf(1), 2, 3], [0, 2, 3]) == [0, 2, 3]
    assert match([0, SomeOf(1, at_least=1), 2, 3], [0, 2, 3]) is NoMatch
    assert match([0, SomeOf(1, at_least=1), 2, 3], [0, 1, 2, 3]) == [0, 1, 2, 3]
    assert match([0, SomeOf(1, at_least=2), 2, 3], [0, 1, 2, 3]) is NoMatch
    assert match([0, SomeOf(1, at_least=2), 2, 3], [0, 1, 1, 2, 3]) == [0, 1, 1, 2, 3]
    assert match([0, SomeOf(1, at_most=2), 2, 3], [0, 1, 1, 2, 3]) == [0, 1, 1, 2, 3]
    assert match([0, SomeOf(1, at_most=1), 2, 3], [0, 1, 1, 2, 3]) is NoMatch
    assert match([0, SomeOf(1, exactly=1), 2, 3], [0, 2, 3]) is NoMatch
    assert match([0, SomeOf(1, exactly=1), 2, 3], [0, 1, 2, 3]) == [0, 1, 2, 3]
    assert match([0, SomeOf(1, exactly=0), 2, 3], [0, 2, 3]) == [0, 2, 3]
    assert match([0, SomeOf(1, exactly=0), 2, 3], [0, 1, 2, 3]) is NoMatch

    assert match([0, SomeOf(1, SomeOf(2)), 3], [0, 3]) == [0, 3]
    assert match([0, SomeOf(1, SomeOf(2)), 3], [0, 1, 3]) == [0, 1, 3]
    assert match([0, SomeOf(1, SomeOf(2)), 3], [0, 1, 2, 3]) == [0, 1, 2, 3]
    assert match([0, SomeOf(1, SomeOf(2)), 3], [0, 1, 2, 2, 3]) == [0, 1, 2, 2, 3]
    assert match([0, SomeOf(1, SomeOf(2)), 3], [0, 1, 2, 2, 2, 3]) == [0, 1, 2, 2, 2, 3]
    assert match([0, SomeOf(1, SomeOf(2)), 3], [0, 1, 2, 1, 2, 2, 3]) == [
        0,
        1,
        2,
        1,
        2,
        2,
        3,
    ]

    assert match([0, SomeOf(1, SomeOf(2), at_least=1), 3], [0, 1, 2, 3]) == [0, 1, 2, 3]
    assert match([0, SomeOf(1, SomeOf(2), at_least=1), 3], [0, 1, 3]) == [0, 1, 3]
    assert (
        match([0, SomeOf(1, SomeOf(2, at_least=2), at_least=1), 3], [0, 1, 3])
        is NoMatch
    )
    assert (
        match([0, SomeOf(1, SomeOf(2, at_least=2), at_least=1), 3], [0, 1, 2, 3])
        is NoMatch
    )
    assert match(
        [0, SomeOf(1, SomeOf(2, at_least=2), at_least=1), 3], [0, 1, 2, 2, 3]
    ) == [
        0,
        1,
        2,
        2,
        3,
    ]


@pytest.mark.parametrize(
    ("pattern", "value", "expected"),
    [
        (InstanceOf(bool), True, True),
        (InstanceOf(str), "foo", "foo"),
        (InstanceOf(int), 8, 8),
        (InstanceOf(int), 1, 1),
        (InstanceOf(float), 1.0, 1.0),
        (IsIn({"a", "b"}), "a", "a"),
        (IsIn({"a": 1, "b": 2}), "a", "a"),
        (IsIn(["a", "b"]), "a", "a"),
        (IsIn(("a", "b")), "b", "b"),
        (IsIn({"a", "b", "c"}), "c", "c"),
        (TupleOf(InstanceOf(int)), (1, 2, 3), (1, 2, 3)),
        (PatternList((InstanceOf(int), InstanceOf(str))), (1, "a"), [1, "a"]),
        (ListOf(InstanceOf(str)), ["a", "b"], ["a", "b"]),
        (AnyOf(InstanceOf(str), InstanceOf(int)), "foo", "foo"),
        (AnyOf(InstanceOf(str), InstanceOf(int)), 7, 7),
        (
            AllOf(InstanceOf(int), If(lambda v: v >= 3), If(lambda v: v >= 8)),
            10,
            10,
        ),
        (
            MappingOf(InstanceOf(str), InstanceOf(int)),
            {"a": 1, "b": 2},
            {"a": 1, "b": 2},
        ),
    ],
)
def test_various_patterns(pattern, value, expected):
    assert pattern.apply(value, context={}) == expected


@pytest.mark.parametrize(
    ("pattern", "value"),
    [
        (InstanceOf(bool), "foo"),
        (InstanceOf(str), True),
        (InstanceOf(int), 8.1),
        (Min(3), 2),
        (InstanceOf(int), None),
        (InstanceOf(float), 1),
        (IsIn(["a", "b"]), "c"),
        (IsIn({"a", "b"}), "c"),
        (IsIn({"a": 1, "b": 2}), "d"),
        (TupleOf(InstanceOf(int)), (1, 2.0, 3)),
        (ListOf(InstanceOf(str)), ["a", "b", None]),
        # (AnyOf(InstanceOf(str), Min(4)), 3.14),
        # (AnyOf(InstanceOf(str), Min(10)), 9),
        # (AllOf(InstanceOf(int), Min(3), Min(8)), 7),
        (DictOf(InstanceOf(int), InstanceOf(str)), {"a": 1, "b": 2}),
    ],
)
def test_various_not_matching_patterns(pattern, value):
    assert pattern.apply(value, context={}) is NoMatch


@pattern
def endswith_d(s, **ctx):
    if not s.endswith("d"):
        return NoMatch
    return s


def test_pattern_decorator():
    assert endswith_d.apply("abcd", context={}) == "abcd"
    assert endswith_d.apply("abc", context={}) is NoMatch


@pytest.mark.parametrize(
    ("annot", "expected"),
    [
        (int, InstanceOf(int)),
        (str, InstanceOf(str)),
        (bool, InstanceOf(bool)),
        (Optional[int], Option(InstanceOf(int))),
        (Optional[Union[str, int]], Option(AnyOf(InstanceOf(str), InstanceOf(int)))),
        (Union[int, str], AnyOf(InstanceOf(int), InstanceOf(str))),
        (Annotated[int, Min(3)], AllOf(InstanceOf(int), Min(3))),
        (list[int], SequenceOf(InstanceOf(int), list)),
        (
            tuple[int, float, str],
            PatternList(
                (InstanceOf(int), InstanceOf(float), InstanceOf(str)), type=tuple
            ),
        ),
        (tuple[int, ...], TupleOf(InstanceOf(int))),
        (
            dict[str, float],
            DictOf(InstanceOf(str), InstanceOf(float)),
        ),
        # (FrozenDict[str, int], FrozenDictOf(InstanceOf(str), InstanceOf(int))),
        (Literal["alpha", "beta", "gamma"], IsIn(("alpha", "beta", "gamma"))),
        # (
        #     Callable[[str, int], str],
        #     CallableWith((InstanceOf(str), InstanceOf(int)), InstanceOf(str)),
        # ),
        # (Callable, InstanceOf(CallableABC)),
    ],
)
def test_pattern_from_typehint(annot, expected):
    assert Pattern.from_typehint(annot) == expected


@pytest.mark.skipif(sys.version_info < (3, 10), reason="requires python3.10 or higher")
def test_pattern_from_typehint_uniontype():
    # uniontype marks `type1 | type2` annotations and it's different from
    # Union[type1, type2]
    validator = Pattern.from_typehint(str | int | float)
    assert validator == AnyOf(InstanceOf(str), InstanceOf(int), InstanceOf(float))


def test_pattern_from_typehint_disable_coercion():
    class MyFloat(float):
        @classmethod
        def __coerce__(cls, obj):
            return cls(float(obj))

    p = Pattern.from_typehint(MyFloat, allow_coercion=True)
    assert isinstance(p, CoercedTo)

    p = Pattern.from_typehint(MyFloat, allow_coercion=False)
    assert isinstance(p, InstanceOf)


class PlusOne:
    __slots__ = ("value",)

    def __init__(self, value):
        self.value = value

    @classmethod
    def __coerce__(cls, obj):
        return cls(obj + 1)

    def __eq__(self, other):
        return type(self) is type(other) and self.value == other.value


class PlusOneRaise(PlusOne):
    @classmethod
    def __coerce__(cls, obj):
        if isinstance(obj, cls):
            return obj
        else:
            raise ValueError("raise on coercion")


class PlusOneChild(PlusOne):
    pass


class PlusTwo(PlusOne):
    @classmethod
    def __coerce__(cls, obj):
        return obj + 2


def test_pattern_from_coercible_protocol():
    s = Pattern.from_typehint(PlusOne)
    assert s.apply(1, context={}) == PlusOne(2)
    assert s.apply(10, context={}) == PlusOne(11)


def test_pattern_coercible_bypass_coercion():
    s = Pattern.from_typehint(PlusOneRaise)
    # bypass coercion since it's already an instance of SomethingRaise
    assert s.apply(PlusOneRaise(10), context={}) == PlusOneRaise(10)
    # but actually call __coerce__ if it's not an instance
    with pytest.raises(ValueError, match="raise on coercion"):
        s.apply(10, context={})


def test_pattern_coercible_checks_type():
    s = Pattern.from_typehint(PlusOneChild)
    v = Pattern.from_typehint(PlusTwo)

    assert s.apply(1, context={}) == PlusOneChild(2)

    assert PlusTwo.__coerce__(1) == 3
    assert v.apply(1, context={}) is NoMatch


class DoubledList(list[T]):
    @classmethod
    def __coerce__(cls, obj):
        return cls(list(obj) * 2)


def test_pattern_coercible_sequence_type():
    s = Pattern.from_typehint(Sequence[PlusOne])
    # with pytest.raises(TypeError, match=r"Sequence\(\) takes no arguments"):
    assert s.apply([1, 2, 3], context={}) == [PlusOne(2), PlusOne(3), PlusOne(4)]

    s = Pattern.from_typehint(list[PlusOne])
    assert s == SequenceOf(CoercedTo(PlusOne), list)
    assert s.apply([1, 2, 3], context={}) == [PlusOne(2), PlusOne(3), PlusOne(4)]

    s = Pattern.from_typehint(tuple[PlusOne, ...])
    assert s == TupleOf(CoercedTo(PlusOne))
    assert s.apply([1, 2, 3], context={}) == (PlusOne(2), PlusOne(3), PlusOne(4))

    s = Pattern.from_typehint(DoubledList[PlusOne])
    assert s == SequenceOf(CoercedTo(PlusOne), DoubledList)
    assert s.apply([1, 2, 3], context={}) == DoubledList(
        [PlusOne(2), PlusOne(3), PlusOne(4), PlusOne(2), PlusOne(3), PlusOne(4)]
    )


def test_pattern_function():
    class MyNegativeInt(int):
        @classmethod
        def __coerce__(cls, other):
            return cls(-int(other))

    class Box(Generic[T]):
        value: T

    def f(x):
        return x > 0

    # ... is treated the same as Any()
    assert pattern(...) == Anything()
    assert pattern(Anything()) == Anything()
    assert pattern(True) == EqualTo(True)

    # plain types are converted to InstanceOf patterns
    assert pattern(int) == InstanceOf(int)
    # no matter whether the type implements the coercible protocol or not
    assert pattern(MyNegativeInt) == InstanceOf(MyNegativeInt)

    # generic types are converted to GenericInstanceOf patterns
    assert pattern(Box[int]) == GenericInstanceOf(Box[int])
    # no matter whethwe the origin type implements the coercible protocol or not
    assert pattern(Box[MyNegativeInt]) == GenericInstanceOf(Box[MyNegativeInt])

    # sequence typehints are converted to the appropriate sequence checkers
    assert pattern(List[int]) == ListOf(InstanceOf(int))  # noqa: UP006

    # spelled out sequences construct a more advanced pattern sequence
    assert pattern([int, str, 1]) == PatternList(
        [InstanceOf(int), InstanceOf(str), EqualTo(1)]
    )

    # matching deferred to user defined functions
    # assert pattern(f) == Custom(f)

    # matching mapping values
    assert pattern({"a": 1, "b": 2}) == EqualTo({"a": 1, "b": 2})
