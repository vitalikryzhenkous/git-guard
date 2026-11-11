"""Хуки pre-commit / pre-push. Печатает только: репо, коммит, файл, тип — без значений."""
import json, os, subprocess, sys, tempfile
from git_guard import config, exclude, rules, terms

ZERO = "0" * 40


def git(repo, *a, inp=None):
    return subprocess.run(["git", "-C", repo, *a], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", input=inp).stdout


def changes(repo, ref):
    """[(path, blob_sha)] для staged (ref=None) или коммита ref."""
    if ref is None:
        out = git(repo, "diff", "--cached", "--raw", "-z", "--no-renames", "--diff-filter=ACMR")
    else:
        out = git(repo, "diff-tree", "-r", "--raw", "-z", "--no-renames", "--root",
                  "--no-commit-id", "--diff-filter=ACMR", ref)
    t, res = out.split("\0"), []
    for i in range(0, len(t) - 1, 2):
        res.append((t[i + 1], t[i].split()[3]))
    return res


def sizes(repo, shas):
    out = git(repo, "cat-file", "--batch-check", inp="\n".join(shas) + "\n") if shas else ""
    return [int(l.split()[2]) if len(l.split()) == 3 and l.split()[2].isdigit() else 0
            for l in out.splitlines()]


def added_lines(repo, ref):
    args = ["diff", "--cached"] if ref is None else ["show", "--format=", ref]
    p = git(repo, *args, "-U0", "--no-color", "--no-renames")
    fname = None
    for line in p.splitlines():
        if line.startswith("+++ "):
            fname = line[6:] if line[4:6] == "b/" else None
        elif line.startswith("+") and fname:
            yield fname, line[1:]


def check_commit(repo, ref, cfg, pat, big_ok):
    """Список (label, file, type, blocking)."""
    label = "staged" if ref is None else ref[:10]
    ch = changes(repo, ref)
    res = []
    if not big_ok:
        if len(ch) > cfg["max_files"]:
            res.append((label, "-", f"files>{cfg['max_files']}", True))
        for (path, _), sz in zip(ch, sizes(repo, [b for _, b in ch])):
            if sz > cfg["max_bytes"]:
                res.append((label, path, "size>1MB", True))
    for path, _ in ch:
        kind = rules.denied_path(path, cfg)
        if kind:
            res.append((label, path, kind, True))
    if pat:
        seen = set()
        for f, line in added_lines(repo, ref):
            if f not in seen and pat.search(line):
                seen.add(f)
                test = rules.is_test_path(f, cfg)
                res.append((label, f, "term(test-path:warn)" if test else "term", not test))
    return res


def gitleaks(repo, log_opts=None):
    with tempfile.TemporaryDirectory() as td:
        rep = os.path.join(td, "r.json")
        cmd = ["gitleaks", "git", repo, "--redact", "--no-banner", "--exit-code", "0", "-f", "json", "-r", rep]
        cmd += ["--staged"] if log_opts is None else ["--log-opts", log_opts]
        subprocess.run(cmd, capture_output=True, cwd=repo)
        try:
            data = json.load(open(rep))
        except (OSError, ValueError):
            return [("-", "-", "gitleaks-error", True)]
    return [((r.get("Commit") or "staged")[:10], r.get("File", ""), "secret:" + r.get("RuleID", "?"), True)
            for r in data or []]


def push_range(repo, remote, lines):
    """[(range_for_gitleaks, [commits])] по строкам stdin pre-push."""
    out = []
    for ln in lines:
        p = ln.split()
        if len(p) != 4 or p[1] == ZERO:
            continue
        _, local, _, remote_sha = p
        if remote_sha == ZERO:
            spec = [local, "--not", f"--remotes={remote}"]
        else:
            spec = [f"{remote_sha}..{local}"]
        commits = git(repo, "rev-list", *spec).split()
        out.append((" ".join(spec), commits))
    return out


def report(repo, results):
    name = os.path.basename(repo)
    for label, f, t, _ in sorted(set(results)):
        print(f"git-guard ✗ {name}\t{label}\t{f}\t{t}", file=sys.stderr)
    return any(b for *_, b in results)


def chain(repo, name, args, stdin_text):
    for d in (".githooks", "scripts/hooks", ".git/hooks"):
        h = os.path.join(repo, d, name)
        if os.path.isfile(h) and os.access(h, os.X_OK):
            return subprocess.run([h, *args], cwd=repo, input=stdin_text, text=True).returncode
    return 0


def run(name, args, repo=None, stdin_text=""):
    repo = repo or git(os.getcwd(), "rev-parse", "--show-toplevel").strip()
    if exclude.is_excluded(repo):
        print(f"git-guard: {os.path.basename(repo)} excluded", file=sys.stderr)
        return chain(repo, name, args, stdin_text)
    cfg = config.load(repo)
    pat = terms.pattern(terms.load())
    big_ok = os.environ.get("GUARD_ALLOW_BIG") == "1"
    if name == "pre-commit":
        res = check_commit(repo, None, cfg, pat, big_ok) + gitleaks(repo)
    else:
        res = []
        for spec, commits in push_range(repo, args[0] if args else "origin", stdin_text.splitlines()):
            for c in commits:
                res += check_commit(repo, c, cfg, pat, big_ok)
            if commits:
                res += gitleaks(repo, spec)
    if report(repo, res):
        return 1
    return chain(repo, name, args, stdin_text)


if __name__ == "__main__":
    sys.exit(run(sys.argv[1], sys.argv[2:], stdin_text="" if sys.argv[1] == "pre-commit" else sys.stdin.read()))
