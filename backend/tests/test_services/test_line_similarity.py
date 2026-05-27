from pathlib import Path
import pytest
from app.services.methods.line_similarity import LineSimilarityMethod, _similarity


def test_similarity_identical():
    lines = ["def foo():", "    return 1", "x = 2"]
    assert _similarity(lines, lines) == pytest.approx(1.0)


def test_similarity_disjoint():
    a = ["def foo():", "    return 1"]
    b = ["class Bar:", "    pass"]
    s = _similarity(a, b)
    assert s < 0.3


def test_similarity_partial():
    a = ["line1", "line2", "line3", "line4"]
    b = ["line1", "line2", "totally_different", "also_different"]
    s = _similarity(a, b)
    assert 0.2 < s < 0.8


def test_similarity_empty():
    assert _similarity([], ["x"]) == pytest.approx(0.0)
    assert _similarity(["x"], []) == pytest.approx(0.0)


def test_line_similarity_method_identical(tmp_path):
    ra = tmp_path / "a"
    rb = tmp_path / "b"
    ra.mkdir(); rb.mkdir()
    content = "def foo():\n    return 1\n\ndef bar():\n    return 2\n"
    (ra / "m.py").write_text(content)
    (rb / "m.py").write_text(content)

    method = LineSimilarityMethod()
    result = method.compare(ra, [ra / "m.py"], rb, [rb / "m.py"], "python")
    assert result.score == pytest.approx(1.0)


def test_line_similarity_method_half_overlap(tmp_path):
    ra = tmp_path / "a"
    rb = tmp_path / "b"
    ra.mkdir(); rb.mkdir()
    lines_a = "\n".join(f"line{i}" for i in range(10))
    lines_b = "\n".join(f"line{i}" for i in range(5)) + "\n" + "\n".join(f"unique{i}" for i in range(5))
    (ra / "m.py").write_text(lines_a)
    (rb / "m.py").write_text(lines_b)

    method = LineSimilarityMethod()
    result = method.compare(ra, [ra / "m.py"], rb, [rb / "m.py"], "python")
    assert 0.3 < result.score < 0.8
