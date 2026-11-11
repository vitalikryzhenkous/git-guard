import os, subprocess
from tests.conftest import SYN_TERM, fake_token

BLOCK = lambda r: r.returncode != 0 and "git-guard ✗" in r.stderr


def test_denylist_name_blocks_and_clean_passes(mk):
    r = mk(); r.write("pipeline.yaml")
    res = r.commit("pipeline.yaml"); assert BLOCK(res) and "denylist" in res.stderr
    r2 = mk(); r2.write("ok.txt")
    assert r2.commit("ok.txt").returncode == 0


def test_env_blocked_but_example_allowed(mk):
    r = mk(); r.write(".env")
    assert BLOCK(r.commit(".env"))
    r2 = mk(); r2.write(".env.example")
    assert r2.commit(".env.example").returncode == 0


def test_repo_config_denies_profile_yaml(mk):
    r = mk(); r.write("profile.yaml")
    assert r.commit("profile.yaml").returncode == 0           # в общем минимуме нет
    r2 = mk(); r2.write(".git-guard.yaml", "deny_names:\n  - profile.yaml\ndeny_dirs:\n  - reports\n"); r2.write("profile.yaml"); r2.write("reports/a.txt")
    assert BLOCK(r2.commit("profile.yaml"))
    assert BLOCK(r2.commit("reports/a.txt"))


def test_too_many_files_blocks_and_override(mk):
    r = mk()
    fs = [f"f{i}.txt" for i in range(31)]
    for f in fs: r.write(f)
    assert BLOCK(r.commit(*fs))
    assert r.commit(env_extra={"GUARD_ALLOW_BIG": "1"}).returncode == 0
    r2 = mk(); fs = [f"f{i}.txt" for i in range(30)]
    for f in fs: r2.write(f)
    assert r2.commit(*fs).returncode == 0


def test_big_file_blocks_and_override(mk):
    r = mk(); r.write("big.txt", size=1_100_000)
    assert BLOCK(r.commit("big.txt"))
    assert r.commit(env_extra={"GUARD_ALLOW_BIG": "1"}).returncode == 0


def test_suspicious_paths_block(mk):
    for rel in ("Users/x/a.txt", "AppData/Local/a.txt", "Chrome-profile/a.txt"):
        r = mk(); r.write(rel)
        assert BLOCK(r.commit(rel)), rel
    r = mk(); r.write("src/profile_view.py")                  # файл, не каталог — чисто
    assert r.commit("src/profile_view.py").returncode == 0


def test_secret_blocks_and_clean_passes(mk):
    r = mk(); r.write("a.txt", f"token = {fake_token()}\n")
    res = r.commit("a.txt"); assert BLOCK(res) and "secret:" in res.stderr and fake_token() not in res.stderr
    r2 = mk(); r2.write("a.txt", "hello\n")
    assert r2.commit("a.txt").returncode == 0


def test_term_blocks_whole_word_case_insensitive_never_printed(mk):
    r = mk(); r.write("n.txt", f"met {SYN_TERM.upper()} today\n")
    res = r.commit("n.txt"); assert BLOCK(res) and SYN_TERM not in res.stderr.lower()
    r2 = mk(); r2.write("n.txt", f"{SYN_TERM}es are fine\n")   # не целое слово
    assert r2.commit("n.txt").returncode == 0


def test_term_in_test_path_only_warns(mk):
    r = mk(); r.write("tests/fixtures/a.txt", f"{SYN_TERM}\n")
    res = r.commit("tests/fixtures/a.txt")
    assert res.returncode == 0 and "test-path:warn" in res.stderr


def test_repo_hook_chained(mk):
    r = mk(); r.write(".githooks/pre-commit", "#!/bin/sh\nexit 1\n"); os.chmod(r.p / ".githooks/pre-commit", 0o755)
    r.write("a.txt")
    assert r.commit("a.txt").returncode != 0                   # свой хук репо заблокировал
    (r.p / ".githooks/pre-commit").write_text("#!/bin/sh\nexit 0\n")
    assert r.commit("a.txt").returncode == 0


def test_excluded_repo_skipped(mk):
    r = mk(); ex = mk.tmp / "ex.txt"; ex.write_text(f"{r.p}\n")
    r.write("pipeline.yaml")
    res = r.commit("pipeline.yaml", env_extra={"GUARD_EXCLUDE_FILE": str(ex)})
    assert res.returncode == 0 and "excluded" in res.stderr


def _pair(mk):
    r = mk(); bare = mk.tmp / "bare.git"
    subprocess.run(["git", "init", "-q", "--bare", str(bare)], check=True)
    r.git("remote", "add", "origin", str(bare))
    r.write("base.txt"); assert r.commit("base.txt").returncode == 0
    r.git("push", "-q", "origin", "main")
    return r


def test_prepush_blocks_bad_commit_in_range(mk):
    r = _pair(mk)
    r.write("pipeline.yaml"); r.commit("pipeline.yaml", hooks=False)     # плохой коммит мимо хука
    r.write("ok.txt"); assert r.commit("ok.txt").returncode == 0          # поверх чистый
    res = r.git("push", "origin", "main", check=False)
    assert res.returncode != 0 and "denylist" in res.stderr


def test_prepush_new_branch_secret_blocks(mk):
    r = _pair(mk); r.git("switch", "-q", "-c", "feat")
    r.write("a.txt", f"token = {fake_token()}\n"); r.commit("a.txt", hooks=False)
    res = r.git("push", "origin", "feat", check=False)
    assert res.returncode != 0 and "secret:" in res.stderr


def test_prepush_clean_range_passes(mk):
    r = _pair(mk)
    r.write("ok.txt"); assert r.commit("ok.txt").returncode == 0
    assert r.git("push", "origin", "main", check=False).returncode == 0
