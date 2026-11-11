import os, random, string, subprocess
import pytest

HOOKS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "hooks")
SYN_TERM = "zorblax"


def fake_token():
    return "ghp_" + "".join(random.Random(7).choices(string.ascii_letters + string.digits, k=36))


class Repo:
    def __init__(self, path, env):
        self.p, self.env = path, env
        path.mkdir()
        self.git("init", "-q", "-b", "main"); self.git("config", "user.email", "t@t"); self.git("config", "user.name", "t")

    def git(self, *a, hooks=True, check=True, stdin=None):
        pre = ["-c", "core.excludesFile=/dev/null", "-c", f"core.hooksPath={HOOKS if hooks else '/dev/null'}"]
        r = subprocess.run(["git", "-C", str(self.p), *pre, *a], capture_output=True, text=True, env=self.env, input=stdin)
        if check and r.returncode:
            raise AssertionError(r.stderr)
        return r

    def write(self, rel, text="x\n", size=None):
        f = self.p / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(text if size is None else "a" * size)

    def commit(self, *files, hooks=True, msg="c", env_extra=None):
        for f in files:
            self.git("add", "--", f)
        if env_extra:
            self.env = {**self.env, **env_extra}
        return self.git("commit", "-q", "-m", msg, hooks=hooks, check=False)


@pytest.fixture
def mk(tmp_path, monkeypatch):
    terms = tmp_path / "terms.txt"
    terms.write_text(f"{SYN_TERM}\n")
    env = {**os.environ, "GUARD_TERMS_FILE": str(terms), "GUARD_EXCLUDE_FILE": str(tmp_path / "none.txt"),
           "GUARD_ALLOW_BIG": ""}
    env.pop("GUARD_ALLOW_BIG")
    n = [0]
    def make():
        n[0] += 1
        return Repo(tmp_path / f"r{n[0]}", dict(env))
    make.tmp, make.env = tmp_path, env
    return make
