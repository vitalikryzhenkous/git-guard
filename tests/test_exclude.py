import os, random, string, subprocess
from git_guard import audit, exclude


def make_repo(path):
    path.mkdir()
    g = lambda *a: subprocess.run(["git", "-C", str(path), *a], check=True, capture_output=True)
    g("init", "-q"); g("config", "user.email", "t@t"); g("config", "user.name", "t")
    rnd = random.Random(7)
    tok = "ghp_" + "".join(rnd.choices(string.ascii_letters + string.digits, k=36))
    (path / "a.txt").write_text(f"token = {tok}\n")
    g("add", "a.txt"); g("commit", "-q", "-m", "x")


def test_excluded_repo_skipped_and_other_checked(tmp_path, monkeypatch):
    a, b = tmp_path / "excl", tmp_path / "incl"
    make_repo(a); make_repo(b)
    ex = tmp_path / "exclude.txt"
    ex.write_text(f"# comment\n{a}\n")
    monkeypatch.setenv("GUARD_EXCLUDE_FILE", str(ex))
    out_a = audit.audit_repo(str(a), None)
    out_b = audit.audit_repo(str(b), None)
    assert out_a == ["excl\t-\t-\texcluded"]
    assert any("secret:" in l for l in out_b)          # ✗ неисключённый проверяется
    assert not any("excluded" in l for l in out_b)


def test_no_exclude_file_means_nothing_excluded(tmp_path, monkeypatch):
    monkeypatch.setenv("GUARD_EXCLUDE_FILE", str(tmp_path / "missing.txt"))
    assert exclude.load() == set()
