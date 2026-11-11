import os, subprocess
from git_guard import check, doctor


def test_doctor_reports_local_hookspath_and_excluded(mk, monkeypatch):
    root = mk.tmp / "apps"; root.mkdir()
    a, b = root / "a", root / "b"
    for d in (a, b):
        subprocess.run(["git", "init", "-q", str(d)], check=True)
    subprocess.run(["git", "-C", str(a), "config", "core.hooksPath", ".githooks"], check=True)
    ex = mk.tmp / "ex.txt"; ex.write_text(f"{b}\n")
    monkeypatch.setenv("GUARD_EXCLUDE_FILE", str(ex)); monkeypatch.setenv("GUARD_TERMS_FILE", mk.env["GUARD_TERMS_FILE"])
    out = "\n".join(doctor.report(str(root)))
    assert "a\tЛОКАЛЬНЫЙ core.hooksPath" in out and "b\texcluded" in out
    assert out.count("\n  ") >= 2 and "gitleaks:" in out


def test_check_head_tree_counts_types_and_clean_is_clean(mk, capsys, monkeypatch):
    for k, v in mk.env.items(): monkeypatch.setenv(k, v)
    r = mk(); r.write("pipeline.yaml"); r.write("ok.txt")
    r.git("add", "-f", "--", "pipeline.yaml", "ok.txt"); r.git("commit", "-q", "-m", "c", hooks=False)
    assert check.main(str(r.p)) == 1
    assert "denylist=1" in capsys.readouterr().out
    r2 = mk(); r2.write("ok.txt"); r2.git("add", "ok.txt"); r2.git("commit", "-q", "-m", "c", hooks=False)
    assert check.main(str(r2.p)) == 0
    assert "чисто" in capsys.readouterr().out
