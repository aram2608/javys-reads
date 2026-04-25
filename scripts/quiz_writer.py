"""
quiz_writer.py: parse a .txt quiz definition and emit a standalone HTML quiz.

Grammar:
    @STYLE
        Style block. Run program with --styles to see all available quiz-engine
        styles. Defaults to a predefined style if now used.
    STYLE@

    $TITLE  My Book Title
    $AUTHOR Author Name

    {
        ? Question text
        % Option A, Option B, Option C, Option D
        ! 0
        > Explanation shown after answering
    }

    {
        ? Question two
        % A, B, C, D
        ! 3
        > Explanation
    }

Run:
    python scripts/quiz_writer.py dummy.txt
    python scripts/quiz_writer.py dummy.txt -o out/my-quiz.html
"""

import argparse
import io
import json
from pathlib import Path
from typing import TypedDict


class Question(TypedDict):
    text: str
    opts: list[str]
    ans: int
    exp: str


class QuizData(TypedDict):
    title: str
    author: str
    questions: list[Question]
    style: str


STYLE_OPTS = """\
    --qe-font-serif:  Georgia, serif;
    --qe-font-body:   system-ui, sans-serif;
    --qe-font-label:  monospace;
    --qe-surface:     rgba(255,255,255,0.05);
    --qe-border:      rgba(255,255,255,0.12);
    --qe-border-hi:   rgba(255,255,255,0.30);
    --qe-text:        #f0f0f0;
    --qe-text-muted:  #888;
    --qe-accent:      #c8a96e;
    --qe-accent-lo:   rgba(200,169,110,0.06);
    --qe-btn-bg:           #444;
    --qe-btn-text:         #f0f0f0;
    --qe-btn-hover-bg:     #555;
    --qe-btn-hover-text:   #f0f0f0;
    --qe-correct:          #7ec87e;
    --qe-correct-bg:       rgba(100,200,100,0.07);
    --qe-wrong:            #c87e7e;
    --qe-wrong-bg:         rgba(200,100,100,0.07);
    --qe-hero-bg:          transparent;
    --qe-hero-text:        #f0f0f0;
    --qe-score-color:      #c8a96e;
    --qe-denom-color:      #888;
    --qe-bd-bg:            rgba(255,255,255,0.02);
    --qe-bd-border:        rgba(255,255,255,0.07);
"""

STYLE = """\
        :root {{
            --qe-font-serif:  Georgia, serif;
            --qe-font-body:   system-ui, sans-serif;
            --qe-font-label:  monospace;
            --qe-surface:     rgba(255,255,255,0.05);
            --qe-border:      rgba(255,255,255,0.12);
            --qe-border-hi:   rgba(255,255,255,0.30);
            --qe-text:        #f0f0f0;
            --qe-text-muted:  #888;
            --qe-accent:      #c8a96e;
            --qe-accent-lo:   rgba(200,169,110,0.06);
            --qe-btn-bg:           #444;
            --qe-btn-text:         #f0f0f0;
            --qe-btn-hover-bg:     #555;
            --qe-btn-hover-text:   #f0f0f0;
            --qe-correct:          #7ec87e;
            --qe-correct-bg:       rgba(100,200,100,0.07);
            --qe-wrong:            #c87e7e;
            --qe-wrong-bg:         rgba(200,100,100,0.07);
            --qe-hero-bg:          transparent;
            --qe-hero-text:        #f0f0f0;
            --qe-score-color:      #c8a96e;
            --qe-denom-color:      #888;
            --qe-bd-bg:            rgba(255,255,255,0.02);
            --qe-bd-border:        rgba(255,255,255,0.07);
        }}

        * {{ margin: 0; padding: 0; box-sizing: border-box; }}

        body {{
            background: #111;
            color: #f0f0f0;
            font-family: system-ui, sans-serif;
            min-height: 100vh;
        }}

        .container {{
            max-width: 700px;
            margin: 0 auto;
            padding: 56px 24px 80px;
        }}

        header {{ margin-bottom: 56px; }}

        h1 {{
            font-family: Georgia, serif;
            font-size: clamp(2rem, 6vw, 3rem);
            margin-bottom: 6px;
        }}

        .subtitle {{
            font-size: 0.85rem;
            color: #888;
            letter-spacing: 0.1em;
            text-transform: uppercase;
            margin-top: 8px;
        }}
"""

TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        {style}
    </style>
    <link rel="stylesheet" href="../quiz-engine.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>{title}</h1>
            <div class="subtitle">{author}</div>
        </header>
        <div id="quiz-root"></div>
    </div>

    <script>
        window.QUIZ = {{
            questions: {questions_json},
            verdicts: [
                {{ min: 0.8, v: "Excellent",  n: "Outstanding recall." }},
                {{ min: 0.6, v: "Good",       n: "Solid understanding." }},
                {{ min: 0.4, v: "Fair",       n: "Worth revisiting." }},
                {{ min: 0.0, v: "Try again",  n: "Time for a reread." }}
            ]
        }};
    </script>
    <script src="../quiz-engine.js"></script>
</body>
</html>
"""


class ParseError(Exception):
    def __init__(self, line_no: int, msg: str):
        super().__init__(f"line {line_no}: {msg}")


def parse(text: str) -> QuizData:
    """
    Return { title, author, questions: [{text, opts, ans, exp}], style }.
    Raises ParseError on malformed input.
    """
    title = ""
    author = ""
    style = ""
    questions: list[Question] = []

    lines = text.splitlines()
    i = 0

    while i < len(lines):
        raw = lines[i]
        line = raw.strip()
        i += 1

        # Comments
        if not line or line.startswith("#"):
            continue

        if line.startswith("$TITLE"):
            title = line[len("$TITLE") :].strip()

        elif line.startswith("$AUTHOR"):
            author = line[len("$AUTHOR") :].strip()

        elif line.startswith("@STYLE"):
            style_buffer = io.StringIO()
            while i < len(lines):
                raw = lines[i]
                line = raw.strip()
                i += 1

                if line == "STYLE@":
                    break
                _ = style_buffer.write(line)
            else:
                raise ParseError(i, "style block never closed")

            style = style_buffer.getvalue()

            style_buffer.close()

        elif line == "{":
            q_text = ""
            opts: list[str] = []
            answer_text = ""
            explanation = ""
            block_start = i

            while i < len(lines):
                raw = lines[i]
                line = raw.strip()
                i += 1

                if line in ("}", "},"):
                    break

                if line.startswith("?"):
                    q_text = line[1:].strip()
                elif line.startswith("%"):
                    opts = [o.strip() for o in line[1:].split(",")]
                elif line.startswith("!"):
                    answer_text = line[1:].strip()
                elif line.startswith(">"):
                    explanation = line[1:].strip()
                elif line:
                    raise ParseError(i, f"unexpected token: {line!r}")
            else:
                raise ParseError(block_start, "question block never closed")

            if not q_text:
                raise ParseError(block_start, "question block missing '?' line")
            if not opts:
                raise ParseError(block_start, "question block missing '%' line")
            if not answer_text:
                raise ParseError(block_start, "question block missing '!' line")

            # try to cast the index
            try:
                ans_idx = int(answer_text)
            except TypeError:
                raise ParseError(
                    block_start, f"answer {answer_text!r} not found in options {opts}"
                )

            q: Question = {
                "text": q_text,
                "opts": opts,
                "ans": ans_idx,
                "exp": explanation,
            }
            questions.append(q)

        elif line:
            raise ParseError(i, f"unexpected token: {line!r}")

    return {
        "title": title,
        "author": author,
        "questions": questions,
        "style": style,
    }


def render(data: QuizData) -> str:
    questions_json = json.dumps(data["questions"], indent=4, ensure_ascii=False)
    return TEMPLATE.format(
        title=data["title"] or "Quiz",
        author=data["author"] or "",
        questions_json=questions_json,
        style=data["style"] or STYLE,
    )


def main() -> None:
    ap = argparse.ArgumentParser(description="Convert a .txt quiz file to HTML.")
    _ = ap.add_argument("file", nargs="?", help="Input .txt file")
    _ = ap.add_argument(
        "-o", "--output", help="Output .html file (default: same name as input)"
    )
    _ = ap.add_argument(
        "--styles",
        action="store_true",
        help="Print the modifiable styles used by the quiz-engine.",
    )

    args = ap.parse_args()

    if args.styles:
        print(STYLE_OPTS)
        return

    if not args.file:
        ap.error("the following arguments are required: file")

    src = Path(args.file)
    dest = Path(args.output) if args.output else src.with_suffix(".html")

    text = src.read_text(encoding="utf-8")
    data = parse(text)
    html = render(data)
    _ = dest.write_text(html, encoding="utf-8")

    print(f"wrote {dest}  ({len(data['questions'])} questions)")


if __name__ == "__main__":
    main()
