from pathlib import Path
import pytest
from app.services.methods.file_hash import FileHashMethod, _hash_file, _normalise


def test_normalise_strips_comments():
    code = "x = 1\n# this is a comment\ny = 2\n"
    result = _normalise(code)
    assert "# this is a comment" not in result
    assert "x = 1" in result


def test_normalise_strips_blank_lines():
    code = "x = 1\n\n\ny = 2\n"
    result = _normalise(code)
    lines = result.splitlines()
    assert all(ln.strip() for ln in lines)


def test_hash_identical_files(tmp_path):
    content = "def foo():\n    return 42\n"
    f1 = tmp_path / "a.py"
    f2 = tmp_path / "b.py"
    f1.write_text(content)
    f2.write_text(content)
    assert _hash_file(f1) == _hash_file(f2)


def test_hash_whitespace_normalized(tmp_path):
    f1 = tmp_path / "a.py"
    f2 = tmp_path / "b.py"
    f1.write_text("x = 1\ny = 2\n")
    f2.write_text("x = 1\n\n\ny = 2\n")  # extra blank lines
    assert _hash_file(f1) == _hash_file(f2)


def test_hash_different_files(tmp_path):
    f1 = tmp_path / "a.py"
    f2 = tmp_path / "b.py"
    f1.write_text("x = 1\n")
    f2.write_text("y = 2\n")
    assert _hash_file(f1) != _hash_file(f2)


def test_file_hash_method_identical_repos(tmp_path):
    repo_a = tmp_path / "a"
    repo_b = tmp_path / "b"
    repo_a.mkdir()
    repo_b.mkdir()
    (repo_a / "main.py").write_text("def hello():\n    return 1\n")
    (repo_b / "main.py").write_text("def hello():\n    return 1\n")

    method = FileHashMethod()
    files_a = [repo_a / "main.py"]
    files_b = [repo_b / "main.py"]
    result = method.compare(repo_a, files_a, repo_b, files_b, "python")

    assert result.score == pytest.approx(1.0)


def test_file_hash_method_disjoint_repos(tmp_path):
    repo_a = tmp_path / "a"
    repo_b = tmp_path / "b"
    repo_a.mkdir()
    repo_b.mkdir()
    (repo_a / "main.py").write_text("def foo(): return 1\n")
    (repo_b / "main.py").write_text("def bar(): return 99\n")

    method = FileHashMethod()
    result = method.compare(repo_a, [repo_a / "main.py"], repo_b, [repo_b / "main.py"], "python")
    assert result.score == pytest.approx(0.0)


def test_file_hash_method_empty_b(tmp_path):
    repo_a = tmp_path / "a"
    repo_b = tmp_path / "b"
    repo_a.mkdir()
    repo_b.mkdir()
    (repo_a / "main.py").write_text("x=1\n")

    method = FileHashMethod()
    result = method.compare(repo_a, [repo_a / "main.py"], repo_b, [], "python")
    assert result.score == pytest.approx(0.0)
