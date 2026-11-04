"""Enforce the per-branch work-ledger convention structurally, not by memory.

A branch whose cumulative diff touches a **non-trivial** path must add a work ledger under
``.specs/backlog/<kebab>_YYYYMMDD_HHMMSS.md`` carrying at least one ``- [ ]`` / ``- [x]`` checkbox.
It was the last rule of the flow enforced by memory in a repo that makes every other convention
structural, so it is wired into both pre-commit and CI (gate parity), like ``check_typing.py``.

Four design points that are easy to get wrong, all deliberate here:

0. **Bot PRs are exempt, keyed on the AUTHOR.** A gate demanding a human-authored artifact
   permanently blocks every bot PR that trips it — nobody can satisfy it, so the real effect is
   training people to reach for ``--admin``. The exemption reads the PR author from the event
   payload (never ``GITHUB_ACTOR``, which is whoever *triggered* the run) and fails closed when
   the author cannot be resolved. Keyed on the author and never the path: a human branch
   touching the same files still owes the ledger. See ``pr_author_login`` / ``is_bot_author``.


1. **"Non-trivial" is decided BY PATH, reusing the PR gate's classifier — but PER PATH.**
   ``pr_gate.classify_risk(list)`` returns the single *most-dangerous* class and ranks ``tests``
   above ``ci``, so a branch touching both ``bin/`` and ``tests/`` collapses to ``tests`` and would
   wrongly escape the requirement. The ledger question is *set membership* ("does ANY path fall in
   a ledger class?"), so the classifier is called **one path at a time**. Reusing it means no drift
   on what "src"/"ci" mean; asking per path means asking the right question.

2. **Diff-based, not per-commit.** The ledger is a per-*branch* artifact, so a later source-only
   commit on a branch that already has one must pass. Diff against ``merge-base(HEAD, <default>)``.
   Off a feature branch the merge-base is HEAD, the diff is empty, and this is a no-op.

3. **Diff the INDEX (``git diff --cached <base>``), not the working tree.** pre-commit runs on
   *staged* content and plain ``git diff`` ignores untracked files, so a brand-new-but-unstaged
   ledger would be invisible and the gate would demand a ledger that is sitting right there. With
   ``--cached`` the comparison sees branch commits + staged files; in CI (clean tree) it reduces to
   the branch's cumulative diff.

CI must check out with ``fetch-depth: 0`` — a shallow clone has no common ancestor to resolve.
"""

import importlib.util
import json
import os
import pathlib
import re
import subprocess
import sys
import types


BOT_LOGIN_SUFFIX = "[bot]"


def is_bot_author(str_login: str) -> bool:
    """Return whether a GitHub login belongs to a bot account.

    Parameters
    ----------
    str_login : str
        A GitHub login, e.g. ``dependabot[bot]`` or ``octocat``. An empty or ``None``-ish
        value is treated as human, so an unresolved author fails CLOSED.

    Returns
    -------
    bool
        ``True`` only for a login carrying GitHub's ``[bot]`` suffix.
    """
    return bool(str_login) and str_login.endswith(BOT_LOGIN_SUFFIX)


def pr_author_login() -> str:
    """Return the PR author's login from the GitHub event payload (I/O seam).

    ⚠️ This must be the PR **author**, never ``GITHUB_ACTOR``. The actor is whoever
    *triggered* the run, so an actor-keyed exemption dies the moment a human touches the
    bot's PR (update-branch, re-run, fixup) — i.e. the act of unblocking it defeats the fix,
    and every retry looks like "the fix doesn't work".

    ``GITHUB_ACTOR`` is consulted **only** when there is no PR payload at all (a ``push``
    run, a local pre-commit), where there is no author to confuse it with.

    Returns
    -------
    str
        The author login, or ``""`` when it cannot be resolved — which the caller treats as
        human, so the gate fails closed rather than exempting everyone.
    """
    str_event_path = os.environ.get("GITHUB_EVENT_PATH", "")

    if str_event_path:
        try:
            dict_event = json.loads(pathlib.Path(str_event_path).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return ""
        dict_pr = dict_event.get("pull_request") or {}
        return str((dict_pr.get("user") or {}).get("login") or "")

    return os.environ.get("GITHUB_ACTOR", "")


LEDGER_CLASSES = frozenset({"src", "ci"})

LEDGER_DIR = ".specs/backlog"
LEDGER_RE = re.compile(r"^\.specs/backlog/[a-z0-9]+(?:-[a-z0-9]+)*_\d{8}_\d{6}\.md$")
CHECKBOX_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+(?:\[[ x]\]|\[~\][ \t]+[a-z]+/\S)", re.M)
FENCE_RE = re.compile(
    r"^[ \t]*(?:(?P<b>`{3,})[^\n]*$.*?(?:^[ \t]*(?P=b)`*[ \t]*$|\Z)"
    r"|(?P<t>~{3,})[^\n]*$.*?(?:^[ \t]*(?P=t)~*[ \t]*$|\Z))",
    re.M | re.S,
)

_BIN = pathlib.Path(__file__).resolve().parent


def _load_pr_gate() -> types.ModuleType | None:
    """Load ``bin/pr_gate.py`` by path (``bin/`` is not a package).

    Returns
    -------
    module or None
        The ``pr_gate`` module, or ``None`` when it is absent (the gate is an opt-in tier).
    """
    path_gate = _BIN / "pr_gate.py"
    if not path_gate.is_file():
        return None
    cls_spec = importlib.util.spec_from_file_location("pr_gate", path_gate)
    cls_module = importlib.util.module_from_spec(cls_spec)
    cls_spec.loader.exec_module(cls_module)
    return cls_module


def _git(list_args: list) -> str:
    """Run a read-only git command and return stdout (empty string on failure).

    Parameters
    ----------
    list_args : list of str
        Arguments after ``git``.

    Returns
    -------
    str
        Captured stdout, stripped.
    """
    try:
        cls_proc = subprocess.run(  # noqa: S603
            ["git", *list_args],  # noqa: S607
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return ""
    return cls_proc.stdout.strip()


def default_branch() -> str:
    """Return the repository's default branch name (``main``/``master``, else ``main``).

    Returns
    -------
    str
        The default branch name.
    """
    str_ref = _git(["symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD"])
    if str_ref:
        return str_ref.removeprefix("origin/")
    for str_candidate in ("main", "master"):
        if _git(["rev-parse", "--verify", "--quiet", str_candidate]):
            return str_candidate
    return "main"


def merge_heads() -> list:
    """Return every incoming commit of a merge in progress (several for an octopus).

    Mid-merge the index already holds the incoming side's files but HEAD is still the
    pre-merge tip, so a base taken from HEAD alone charges the incoming delta to this branch.
    ``rev-parse MERGE_HEAD`` resolves only the first line, so the file itself is read.

    Returns
    -------
    list of str
        One commit hash per incoming head; empty when no merge is in progress.
    """
    str_path = _git(["rev-parse", "--git-path", "MERGE_HEAD"])
    if not str_path or not pathlib.Path(str_path).is_file():
        return []
    return pathlib.Path(str_path).read_text(encoding="utf-8").split()


def base_candidates() -> list:
    """Return the refs a base may come from, best first.

    A CI checkout of a pull request has neither ``origin/HEAD`` nor a local ``main``, only
    ``origin/main``. The remote-tracking ref is tried first because it reflects what the PR
    will actually merge into; a local branch can be behind it or carry unpushed commits.

    When ``GITHUB_BASE_REF`` is set the PR's base is known, so ONLY that branch is a
    candidate: falling back to another default would diff against the wrong branch and
    pass or fail for the wrong reason.

    Returns
    -------
    list of str
        ``origin/<name>`` then ``<name>``, for ``GITHUB_BASE_REF`` alone when set, else for
        the detected default branch, ``main`` and ``master``; duplicates dropped.
    """
    str_base_ref = os.environ.get("GITHUB_BASE_REF", "")
    list_names = [str_base_ref] if str_base_ref else [default_branch(), "main", "master"]
    list_refs = [
        str_ref for str_name in list_names for str_ref in (f"origin/{str_name}", str_name)
    ]
    return list(dict.fromkeys(list_refs))


def ref_exists(str_ref: str) -> bool:
    """Return whether ``str_ref`` names a commit in this repository.

    Parameters
    ----------
    str_ref : str
        Any ref or revision.

    Returns
    -------
    bool
        ``True`` when it resolves to a commit.
    """
    return bool(_git(["rev-parse", "--verify", "--quiet", f"{str_ref}^{{commit}}"]))


def resolve_base(list_refs: list) -> str:
    """Return the merge-base of HEAD and the first EXISTING ref, counting a merge in progress.

    An existing ref with no common ancestor (a shallow fetch, an orphan branch) is a failure,
    never a reason to try the next candidate: that would diff against the wrong branch. The
    one exception is the ``origin/<name>`` / ``<name>`` pair, where the later base wins, so a
    stale remote-tracking ref cannot charge a newer local branch's commits to this one.

    Parameters
    ----------
    list_refs : list of str
        Candidate refs, best first (see ``base_candidates``).

    Returns
    -------
    str
        The base commit; empty when no candidate exists or the chosen one has no merge-base.
    """
    list_found = [str_ref for str_ref in list_refs if ref_exists(str_ref)]
    if not list_found:
        return ""
    str_name = list_found[0].removeprefix("origin/")
    str_best = ""
    for str_ref in list_found:
        if str_ref.removeprefix("origin/") != str_name:
            continue
        str_base = _git(["merge-base", str_ref, "HEAD", *merge_heads()])
        if str_base and (not str_best or _git(["merge-base", str_best, str_base]) == str_best):
            str_best = str_base
    return str_best


def is_unborn_branch() -> bool:
    """Return whether HEAD names a branch that has no commit yet.

    Distinguishes a genuinely empty repository (nothing to diff, so nothing to check) from
    "git could not run here" (not a repository, git missing, ``safe.directory`` refusal),
    where ``symbolic-ref`` fails too.

    Returns
    -------
    bool
        ``True`` only when ``HEAD`` is a symbolic ref that does not resolve.
    """
    return bool(_git(["symbolic-ref", "--quiet", "HEAD"])) and not _git(
        ["rev-parse", "--verify", "--quiet", "HEAD"]
    )


def fail_closed(str_cause: str, str_remedy: str) -> int:
    """Report that the gate could not look, and fail.

    "Could not look" must never print the same verdict as "nothing to check".

    Parameters
    ----------
    str_cause : str
        What could not be resolved, e.g. the refs that were tried.
    str_remedy : str
        The fix that matches that cause.

    Returns
    -------
    int
        Always 1.
    """
    print(
        f"❌ work-ledger check {str_cause}. {str_remedy}",
        file=sys.stderr,
    )
    return 1


def changed_paths(str_base: str) -> list:
    """Return the branch's cumulative changed paths, INDEX included.

    Parameters
    ----------
    str_base : str
        The merge-base commit to diff against.

    Returns
    -------
    list of str
        Repository-relative paths.
    """
    str_out = _git(["diff", "--cached", "--name-only", str_base])
    return [p for p in str_out.splitlines() if p]


def needs_ledger(list_paths: list, cls_gate: types.ModuleType) -> bool:
    """Return whether ANY changed path falls in a ledger-requiring class.

    Parameters
    ----------
    list_paths : list of str
        The branch's changed paths.
    cls_gate : module
        The loaded ``pr_gate`` module (its classifier is the single source of truth).

    Returns
    -------
    bool
        ``True`` when at least one path is in ``LEDGER_CLASSES``.
    """
    return any(cls_gate.classify_risk([p]) in LEDGER_CLASSES for p in list_paths)


def find_ledger_problems(list_paths: list) -> list:
    """Return problems with the branch's ledger (empty when a valid ledger was added).

    Parameters
    ----------
    list_paths : list of str
        The branch's changed paths.

    Returns
    -------
    list of str
        One message per problem.
    """
    list_ledgers = [p for p in list_paths if p.startswith(f"{LEDGER_DIR}/") and p.endswith(".md")]
    if not list_ledgers:
        return [
            f"❌ this branch changes src/ or ci paths but adds no work ledger "
            f"under {LEDGER_DIR}/. "
            f"Create {LEDGER_DIR}/<kebab-topic>_YYYYMMDD_HHMMSS.md with a '- [ ]' checklist."
        ]
    list_problems = []
    for str_ledger in list_ledgers:
        if not LEDGER_RE.match(str_ledger):
            list_problems.append(
                f"❌ {str_ledger}: name must match {LEDGER_DIR}/<kebab-topic>_YYYYMMDD_HHMMSS.md"
            )
            continue
        path_ledger = pathlib.Path(str_ledger)
        if path_ledger.is_file() and not CHECKBOX_RE.search(
            FENCE_RE.sub("", path_ledger.read_text(encoding="utf-8"))
        ):
            list_problems.append(
                f"❌ {str_ledger}: contains no '- [ ]' / '- [x]' (lowercase) / "
                f"'- [~] <type>/<branch>' checkbox outside a code fence"
            )
    return [] if len(list_problems) < len(list_ledgers) else list_problems


def main() -> int:
    """Check the branch's ledger requirement.

    Returns
    -------
    int
        0 when satisfied (or not applicable), 1 on a violation.
    """
    str_author = pr_author_login()
    if is_bot_author(str_author):
        print(f"✅ work-ledger check skipped — PR authored by a bot ({str_author}).")
        return 0

    cls_gate = _load_pr_gate()
    if cls_gate is None:
        print("bin/pr_gate.py absent — skipping the work-ledger check.")
        return 0

    str_head = _git(["rev-parse", "--verify", "--quiet", "HEAD"])
    if not str_head:
        return (
            0
            if is_unborn_branch()
            else fail_closed(
                "could not resolve HEAD",
                "Run it inside a git checkout, with git installed and the directory trusted "
                "(safe.directory).",
            )
        )
    list_refs = base_candidates()
    str_base = resolve_base(list_refs)
    if not str_base:
        return fail_closed(
            f"could not resolve a base branch (tried {', '.join(list_refs)})",
            "In CI, check out with 'fetch-depth: 0' so the base branch and a common "
            "ancestor exist; locally, fetch the base or set origin/HEAD.",
        )

    list_paths = [] if str_base == str_head else changed_paths(str_base)
    if not list_paths or not needs_ledger(list_paths, cls_gate):
        return 0

    list_problems = find_ledger_problems(list_paths)
    for str_problem in list_problems:
        print(str_problem)
    return 1 if list_problems else 0


if __name__ == "__main__":
    for cls_stream in (sys.stdout, sys.stderr):
        if hasattr(cls_stream, "reconfigure"):
            cls_stream.reconfigure(encoding="utf-8", errors="replace")

    sys.exit(main())
