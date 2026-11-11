"""Ручная проверка репо: staged, а если пусто — всё дерево HEAD. Только счётчики по типам."""
import os, subprocess, sys, tempfile, json
from collections import Counter
from git_guard import config, exclude, hook, rules, terms


def tree_files(repo):
    out = hook.git(repo, "ls-tree", "-r", "-z", "HEAD")
    res = []
    for e in out.split("\0"):
        if e:
            meta, path = e.split("\t", 1)
            res.append((path, meta.split()[2]))
    return res


def check_tree(repo, cfg, pat):
    ch = tree_files(repo)
    res = []
    for (path, _), sz in zip(ch, hook.sizes(repo, [b for _, b in ch])):
        if sz > cfg["max_bytes"]:
            res.append(("HEAD", path, "size>1MB", True))
        kind = rules.denied_path(path, cfg)
        if kind:
            res.append(("HEAD", path, kind, True))
    if pat:
        for path, sha in ch:
            blob = subprocess.run(["git", "-C", repo, "cat-file", "blob", sha], capture_output=True).stdout
            if len(blob) <= cfg["max_bytes"] and pat.search(blob.decode("utf-8", "replace")):
                res.append(("HEAD", path, "term", True))
    with tempfile.TemporaryDirectory() as td:
        arc = subprocess.run(["git", "-C", repo, "archive", "HEAD"], capture_output=True).stdout
        subprocess.run(["tar", "-x", "-C", td], input=arc, capture_output=True)
        rep = os.path.join(td, "..", os.path.basename(td) + ".json")
        cmd = ["gitleaks", "dir", td, "--redact", "--no-banner", "--exit-code", "0", "-f", "json", "-r", rep]
        if os.path.exists(os.path.join(td, ".gitleaksignore")):
            cmd += ["-i", os.path.join(td, ".gitleaksignore")]
        subprocess.run(cmd, capture_output=True)
        try:
            data = json.load(open(rep)); os.remove(rep)
        except (OSError, ValueError):
            data = None
    if data is None:
        res.append(("HEAD", "-", "gitleaks-error", True))
    res += [("HEAD", r.get("File", "").replace(td + "/", ""), "secret:" + r.get("RuleID", "?"), True) for r in data or []]
    return res


def main(repo):
    name = os.path.basename(repo)
    if exclude.is_excluded(repo):
        print(f"{name}: excluded"); return 0
    try:
        cfg = config.load(repo)
    except config.ConfigError as e:
        print(f"{name}: config-error: {e}"); return 1
    pat = terms.pattern(terms.load())
    staged = hook.git(repo, "diff", "--cached", "--name-only").strip()
    if staged:
        res = hook.check_commit(repo, None, cfg, pat, False) + hook.gitleaks(repo); mode = "staged"
    else:
        res = check_tree(repo, cfg, pat); mode = "HEAD-tree"
    c = Counter(t.split("(")[0].split(":")[0] if not t.startswith("secret") else t for _, _, t, _ in set(res))
    print(f"{name}: {mode}; terms загружено {len(terms.load())}; " + (", ".join(f"{k}={v}" for k, v in sorted(c.items())) or "чисто"))
    return 1 if any(b for *_, b in res) else 0


if __name__ == "__main__":
    sys.exit(max([main(os.path.abspath(a)) for a in sys.argv[1:]] or [main(os.getcwd())]))
