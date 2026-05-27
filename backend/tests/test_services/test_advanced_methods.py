"""Tests for Phase 4 advanced comparison methods."""
import pytest
from pathlib import Path

from app.services.methods.ast_structure import AstStructureMethod, _subtree_hash, _subtree_fingerprints
from app.services.methods.token_ngram import TokenNgramMethod, _tokenise, _fingerprint
from app.services.methods.call_graph import CallGraphMethod, _build_call_graph
from app.services.methods.import_analysis import ImportAnalysisMethod, _extract_imports
from app.services.methods.identifier_similarity import IdentifierSimilarityMethod
from app.services.methods.complexity_profile import ComplexityProfileMethod, _complexity_histogram


# ── AST Structure ────────────────────────────────────────────────────────────

def test_ast_structure_identical(tmp_path):
    ra, rb = tmp_path / "a", tmp_path / "b"
    ra.mkdir(); rb.mkdir()
    code = "def foo(x):\n    if x > 0:\n        return x\n    return -x\n"
    (ra / "m.py").write_text(code)
    (rb / "m.py").write_text(code)

    m = AstStructureMethod()
    r = m.compare(ra, [ra / "m.py"], rb, [rb / "m.py"], "python")
    assert r.score > 0.8, f"Expected > 0.8, got {r.score}"


def test_ast_structure_renamed_vars_high_score(tmp_path):
    ra, rb = tmp_path / "a", tmp_path / "b"
    ra.mkdir(); rb.mkdir()
    # Same structure, different variable names
    (ra / "m.py").write_text("def compute(alpha, beta):\n    return alpha + beta\n")
    (rb / "m.py").write_text("def process(x, y):\n    return x + y\n")

    m = AstStructureMethod()
    r = m.compare(ra, [ra / "m.py"], rb, [rb / "m.py"], "python")
    # Renamed vars should still show structural similarity
    assert r.score > 0.5, f"Expected > 0.5, got {r.score}"


def test_ast_structure_unrelated_low_score(tmp_path):
    ra, rb = tmp_path / "a", tmp_path / "b"
    ra.mkdir(); rb.mkdir()
    (ra / "m.py").write_text("class Foo:\n    def bar(self):\n        for i in range(10):\n            print(i)\n")
    (rb / "m.py").write_text("x = 1\n")

    m = AstStructureMethod()
    r = m.compare(ra, [ra / "m.py"], rb, [rb / "m.py"], "python")
    assert r.score < 0.5, f"Expected < 0.5, got {r.score}"


# ── Token N-gram / Winnowing ─────────────────────────────────────────────────

def test_token_ngram_identical(tmp_path):
    ra, rb = tmp_path / "a", tmp_path / "b"
    ra.mkdir(); rb.mkdir()
    code = "def foo(x, y):\n    return x * y + x\n"
    (ra / "m.py").write_text(code)
    (rb / "m.py").write_text(code)

    m = TokenNgramMethod()
    r = m.compare(ra, [ra / "m.py"], rb, [rb / "m.py"], "python")
    assert r.score > 0.7, f"Expected > 0.7, got {r.score}"


def test_token_ngram_reformatted_copy(tmp_path):
    ra, rb = tmp_path / "a", tmp_path / "b"
    ra.mkdir(); rb.mkdir()
    # Same logic, different whitespace/style
    (ra / "m.py").write_text("def f(a,b,c):\n    return a+b+c\n")
    (rb / "m.py").write_text("def f( a, b, c ):\n    result = a + b + c\n    return result\n")

    m = TokenNgramMethod()
    r = m.compare(ra, [ra / "m.py"], rb, [rb / "m.py"], "python")
    assert r.score > 0.3, f"Expected > 0.3, got {r.score}"


def test_token_ngram_unrelated_low_score(tmp_path):
    ra, rb = tmp_path / "a", tmp_path / "b"
    ra.mkdir(); rb.mkdir()
    (ra / "m.py").write_text("import os\nprint(os.getcwd())\n")
    (rb / "m.py").write_text("class Tree:\n    def __init__(self): self.root = None\n")

    m = TokenNgramMethod()
    r = m.compare(ra, [ra / "m.py"], rb, [rb / "m.py"], "python")
    assert r.score < 0.6, f"Expected < 0.6, got {r.score}"


# ── Call Graph ────────────────────────────────────────────────────────────────

def test_call_graph_identical(tmp_path):
    ra, rb = tmp_path / "a", tmp_path / "b"
    ra.mkdir(); rb.mkdir()
    code = "def a():\n    b()\ndef b():\n    c()\ndef c():\n    pass\n"
    (ra / "m.py").write_text(code)
    (rb / "m.py").write_text(code)

    m = CallGraphMethod()
    r = m.compare(ra, [ra / "m.py"], rb, [rb / "m.py"], "python")
    assert r.score == pytest.approx(1.0)


def test_call_graph_empty_files(tmp_path):
    ra, rb = tmp_path / "a", tmp_path / "b"
    ra.mkdir(); rb.mkdir()
    (ra / "m.py").write_text("x = 1\n")
    (rb / "m.py").write_text("y = 2\n")

    m = CallGraphMethod()
    r = m.compare(ra, [ra / "m.py"], rb, [rb / "m.py"], "python")
    # Both empty graphs — still produces a result
    assert 0.0 <= r.score <= 1.0


# ── Import Analysis ──────────────────────────────────────────────────────────

def test_import_analysis_identical_imports(tmp_path):
    ra, rb = tmp_path / "a", tmp_path / "b"
    ra.mkdir(); rb.mkdir()
    code = "import os\nimport sys\nfrom pathlib import Path\n"
    (ra / "m.py").write_text(code)
    (rb / "m.py").write_text(code)

    m = ImportAnalysisMethod()
    r = m.compare(ra, [ra / "m.py"], rb, [rb / "m.py"], "python")
    assert r.score == pytest.approx(1.0)


def test_import_analysis_no_overlap(tmp_path):
    ra, rb = tmp_path / "a", tmp_path / "b"
    ra.mkdir(); rb.mkdir()
    (ra / "m.py").write_text("import os\nimport sys\n")
    (rb / "m.py").write_text("import json\nimport re\n")

    m = ImportAnalysisMethod()
    r = m.compare(ra, [ra / "m.py"], rb, [rb / "m.py"], "python")
    assert r.score == pytest.approx(0.0)


# ── Identifier Similarity ────────────────────────────────────────────────────

def test_identifier_similarity_identical(tmp_path):
    ra, rb = tmp_path / "a", tmp_path / "b"
    ra.mkdir(); rb.mkdir()
    code = "def compute_tax(amount, rate):\n    return amount * rate\n"
    (ra / "m.py").write_text(code)
    (rb / "m.py").write_text(code)

    m = IdentifierSimilarityMethod()
    r = m.compare(ra, [ra / "m.py"], rb, [rb / "m.py"], "python")
    assert r.score == pytest.approx(1.0)


def test_identifier_similarity_partial(tmp_path):
    ra, rb = tmp_path / "a", tmp_path / "b"
    ra.mkdir(); rb.mkdir()
    (ra / "m.py").write_text("foo = 1\nbar = 2\nbaz = 3\n")
    (rb / "m.py").write_text("foo = 10\nbar = 20\nqux = 30\n")

    m = IdentifierSimilarityMethod()
    r = m.compare(ra, [ra / "m.py"], rb, [rb / "m.py"], "python")
    # foo and bar shared out of {foo, bar, baz, qux}
    assert 0.3 < r.score < 0.8


# ── Complexity Profile ────────────────────────────────────────────────────────

def test_complexity_profile_identical(tmp_path):
    ra, rb = tmp_path / "a", tmp_path / "b"
    ra.mkdir(); rb.mkdir()
    code = (
        "def simple():\n    return 1\n"
        "def medium(x):\n    if x > 0:\n        return x\n    return -x\n"
        "def complex_fn(x, y):\n    for i in range(x):\n        if i > y:\n            break\n    return i\n"
    )
    (ra / "m.py").write_text(code)
    (rb / "m.py").write_text(code)

    m = ComplexityProfileMethod()
    r = m.compare(ra, [ra / "m.py"], rb, [rb / "m.py"], "python")
    assert r.score == pytest.approx(1.0)


def test_all_nine_methods_run(tmp_path):
    """Smoke test: all 9 methods produce a [0,1] score without error."""
    from app.services.comparison_engine import ALL_METHODS
    ra, rb = tmp_path / "a", tmp_path / "b"
    ra.mkdir(); rb.mkdir()
    code = "import os\ndef foo(x):\n    if x: return x\n    return 0\n"
    (ra / "m.py").write_text(code)
    (rb / "m.py").write_text(code)

    for method in ALL_METHODS:
        result = method.compare(ra, [ra / "m.py"], rb, [rb / "m.py"], "python")
        assert 0.0 <= result.score <= 1.0, f"{method.method_id} returned {result.score}"
        assert result.method_id == method.method_id
