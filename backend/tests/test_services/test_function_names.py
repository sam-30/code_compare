from pathlib import Path
import pytest
from app.services.methods.function_names import FunctionNamesMethod, _jaccard
from app.services.parser import extract_function_names


def test_jaccard_identical():
    s = {"foo", "bar", "baz"}
    assert _jaccard(s, s) == pytest.approx(1.0)


def test_jaccard_disjoint():
    assert _jaccard({"a", "b"}, {"c", "d"}) == pytest.approx(0.0)


def test_jaccard_partial():
    a = {"foo", "bar", "baz"}
    b = {"foo", "bar", "qux"}
    j = _jaccard(a, b)
    assert j == pytest.approx(2 / 4)


def test_jaccard_both_empty():
    assert _jaccard(set(), set()) == pytest.approx(1.0)


def test_extract_function_names_python(tmp_path):
    f = tmp_path / "m.py"
    f.write_text(
        "def alpha(): pass\n"
        "def beta(): pass\n"
        "class Gamma:\n"
        "    def delta(self): pass\n"
    )
    names = extract_function_names(f)
    assert "alpha" in names
    assert "beta" in names
    assert "Gamma" in names
    assert "delta" in names


def test_extract_function_names_js(tmp_path):
    f = tmp_path / "m.js"
    f.write_text(
        "function sayHello() {}\n"
        "class Greeter {\n"
        "  greet() {}\n"
        "}\n"
    )
    names = extract_function_names(f)
    assert "sayHello" in names
    assert "Greeter" in names


def test_function_names_method_identical(tmp_path):
    ra = tmp_path / "a"
    rb = tmp_path / "b"
    ra.mkdir(); rb.mkdir()
    code = "def foo(): pass\ndef bar(): pass\n"
    (ra / "m.py").write_text(code)
    (rb / "m.py").write_text(code)

    method = FunctionNamesMethod()
    result = method.compare(ra, [ra / "m.py"], rb, [rb / "m.py"], "python")
    assert result.score == pytest.approx(1.0)


def test_function_names_method_disjoint(tmp_path):
    ra = tmp_path / "a"
    rb = tmp_path / "b"
    ra.mkdir(); rb.mkdir()
    (ra / "m.py").write_text("def alpha(): pass\n")
    (rb / "m.py").write_text("def omega(): pass\n")

    method = FunctionNamesMethod()
    result = method.compare(ra, [ra / "m.py"], rb, [rb / "m.py"], "python")
    assert result.score == pytest.approx(0.0)
