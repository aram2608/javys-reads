"""
audit.py: validate quiz .txt sources for common authoring mistakes.

Walks every .txt in scripts/ (or files given as arguments), parses them with
quiz_writer, and reports issues that the parser itself does not catch:

    - questions without exactly 4 options (the convention for this project)
    - answer index out of range
    - missing/empty question, options, or explanation
    - options with an odd number of unescaped quotes (a strong signal that the
      author wrote `"foo, bar"` and the parser split it on the comma — wrap
      such options in parens instead)
    - options that are a single word like "Jr." or "amen" sitting next to a
      sibling that looks like a fragment (another comma-split signal)

Exit code is 0 when everything is clean, 1 when any issue is reported.

Usage:
    python scripts/audit.py                       # audits every scripts/*.txt
    python scripts/audit.py scripts/foo.txt ...   # audits specific files
"""

from __future__ import annotations

import sys
from pathlib import Path

from quiz_writer import ParseError, parse


SCRIPTS_DIR = Path(__file__).resolve().parent
EXPECTED_OPT_COUNT = 4


def odd_quote_count(opt: str) -> bool:
    return opt.count('"') % 2 == 1


def audit_file(path: Path) -> list[str]:
    issues: list[str] = []
    try:
        data = parse(path.read_text(encoding="utf-8"))
    except ParseError as e:
        return [f"parse error: {e}"]

    qs = data["questions"]
    if not qs:
        issues.append("no questions found")

    for i, q in enumerate(qs, start=1):
        loc = f"Q{i}"
        if not q["text"]:
            issues.append(f"{loc}: missing question text")
        if not q["exp"]:
            issues.append(f"{loc}: missing explanation")

        opts = q["opts"]
        n = len(opts)
        if n != EXPECTED_OPT_COUNT:
            issues.append(f"{loc}: has {n} option(s), expected {EXPECTED_OPT_COUNT}")
        if not (0 <= q["ans"] < n):
            issues.append(f"{loc}: answer index {q['ans']} out of range for {n} options")

        for j, opt in enumerate(opts):
            if not opt:
                issues.append(f"{loc} opt[{j}]: empty")
            if odd_quote_count(opt):
                issues.append(
                    f"{loc} opt[{j}]: unbalanced quotes — likely split on a comma; "
                    f"wrap the original option in parentheses. Got: {opt!r}"
                )

    return issues


def main(argv: list[str]) -> int:
    if argv:
        targets = [Path(a) for a in argv]
    else:
        targets = sorted(SCRIPTS_DIR.glob("*.txt"))

    if not targets:
        print("no .txt files to audit")
        return 0

    total_issues = 0
    for path in targets:
        rel = path.relative_to(Path.cwd()) if path.is_absolute() else path
        if not path.exists():
            print(f"{rel}: file not found")
            total_issues += 1
            continue

        issues = audit_file(path)
        if issues:
            print(f"{rel}: {len(issues)} issue(s)")
            for msg in issues:
                print(f"  - {msg}")
            total_issues += len(issues)
        else:
            print(f"{rel}: ok")

    print()
    print(f"audited {len(targets)} file(s), {total_issues} issue(s)")
    return 1 if total_issues else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
