"""Build the reference as a printable book: `uv run python docs/reference/_print/book.py`.

Pandoc turns each chapter's Markdown into Typst through `filter.lua`; `template.typ` sets the
book; Typst writes the PDF. Figures are printed in light mode, without their own title and
subtitle (the book's caption replaces them). Everything is rebuilt from the sources each time.

    --reader      the reader's edition, without the planner boxes
    --pages       also write every page as a PNG, for review (build/pages/)
    --out PATH    where to write the PDF (default: build/the-factory.pdf, or -reader.pdf)

Needs `pandoc` (3.x) and `typst` (0.15) on the PATH, or installed by winget on Windows.
"""

from __future__ import annotations

import argparse
import datetime
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

HERE = Path(__file__).resolve().parent
REFERENCE = HERE.parent
REPO = REFERENCE.parent.parent
BUILD = HERE / "build"
sys.path.insert(0, str(REFERENCE))

from diagram_kit import svg_size, themed  # noqa: E402

TITLE = "The Factory"
SUBTITLE = "A reference: the idea, the machine, and its first implementation"
DESCRIBES = "537fc20"  # the commit of v1 the book describes (see the preface)
REPO_URL = f"https://github.com/pkrahmer/factory/blob/{DESCRIBES}"
CROP_TOP = 84  # px: a figure's own title and subtitle, which the caption replaces
PARTS = {  # first chapter number -> (part number, title)
    1: ("I", "The idea"),
    4: ("II", "The machine"),
    12: ("III", "Around the machine"),
    18: ("IV", "Looking back"),
}
WINDOWS_TOOLS = {
    "pandoc": Path(os.environ.get("LOCALAPPDATA", "")) / "Pandoc" / "pandoc.exe",
    "typst": Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft/WinGet/Links/typst.exe",
}


@dataclass(frozen=True)
class Chapter:
    folder: str  # "02-concepts", "a-glossary" or "preface"
    source: Path

    @property
    def number(self) -> int | None:
        match = re.match(r"(\d+)-", self.folder)
        return int(match.group(1)) if match else None


def tool(name: str) -> str:
    found = shutil.which(name)
    if found:
        return found
    fallback = WINDOWS_TOOLS.get(name)
    if fallback and fallback.is_file():
        return str(fallback)
    sys.exit(f"{name} is not installed (winget install {name})")


def chapters() -> list[Chapter]:
    """The preface, then the numbered chapters, then the appendices, as far as they exist."""
    found = [Chapter("preface", REFERENCE / "README.md")]
    folders = sorted(p for p in REFERENCE.iterdir() if (p / "README.md").is_file())
    numbered = [p for p in folders if re.match(r"\d\d-", p.name)]
    appendices = [p for p in folders if re.match(r"[a-z]-", p.name)]
    found += [Chapter(p.name, p / "README.md") for p in numbered + appendices]
    return found


def print_figure(source: Path, target: Path) -> None:
    """The figure in light mode, cropped below its own title and subtitle."""
    svg = themed(source.read_text(encoding="utf-8"), "light")
    width, height = svg_size(svg)
    cropped = height - CROP_TOP
    svg = svg.replace(
        f'viewBox="0 0 {width} {height}"', f'viewBox="0 {CROP_TOP} {width} {cropped}"'
    )
    svg = svg.replace(f'height="{height}"', f'height="{cropped}"', 1)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(svg, encoding="utf-8", newline="\n")


def figures(found: list[Chapter]) -> None:
    for chapter in found:
        if chapter.folder == "preface":
            continue
        for svg in sorted(chapter.source.parent.glob("*.svg")):
            print_figure(svg, BUILD / "figures" / chapter.folder / svg.name)


def convert(chapter: Chapter, planner: bool, included: str) -> str:
    """The chapter as Typst, through the filter. Returns the file name inside build/chapters."""
    out = BUILD / "chapters" / f"{chapter.folder}.typ"
    out.parent.mkdir(parents=True, exist_ok=True)
    meta = {
        "chapter": chapter.folder,
        "planner": "true" if planner else "false",
        "included": included,
        "figdir": "/build/figures",
        "figfs": (BUILD / "figures").as_posix(),
        "repo_url": REPO_URL,
    }
    # `smart` reads straight quotes and apostrophes as quotation marks, so Typst sets them curly
    reader = "gfm+smart"
    args = [tool("pandoc"), "-f", reader, "-t", "typst", "--lua-filter", str(HERE / "filter.lua")]
    for key, value in meta.items():
        args += ["-M", f"{key}={value}"]
    args += [str(chapter.source.relative_to(REPO)), "-o", str(out)]
    subprocess.run(args, cwd=REPO, check=True)
    body = out.read_text(encoding="utf-8")
    out.write_text('#import "/template.typ": *\n\n' + body, encoding="utf-8", newline="\n")
    return out.name


def span(found: list[Chapter]) -> str:
    numbered = [c.number for c in found if c.number is not None]
    return f"chapters {min(numbered)} to {max(numbered)}" if numbered else "the preface"


def front_pages(planner: bool, found: list[Chapter]) -> list[str]:
    """The title page, and on its back what this copy is and where it comes from."""
    built = subprocess.run(
        ["git", "rev-parse", "--short", "HEAD"],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    today = datetime.date.today().isoformat()
    kind = (
        "with the planner boxes" if planner else "the reader's edition, without the planner boxes"
    )
    edition = "" if planner else " · reader's edition"
    return [
        f'#title-page("{TITLE}", "{SUBTITLE}", [Draft · {span(found)}{edition} \\',
        "github.com/pkrahmer/factory])",
        "#edition-page[",
        f"#strong[{TITLE}] \\",
        SUBTITLE,
        "",
        f"Built on {today} from commit `{built}` of github.com/pkrahmer/factory; {kind}.",
        f"It describes v1 as of commit `{DESCRIBES}`. This draft contains {span(found)}; the",
        "chapters not yet written appear in cross-references as plain text.",
        "",
        "Every figure in this book is generated from code; its source and a full description",
        "for readers who cannot see it are in the repository beside the chapter. Links to v1's",
        f"files point to commit `{DESCRIBES}`.",
        "]",
    ]


def main_typ(found: list[Chapter], files: dict[str, str], planner: bool) -> str:
    lines = [
        '#import "/template.typ": *',
        f"#show: book.with(title: {TITLE!r})".replace("'", '"'),
        *front_pages(planner, found),
        "#contents()",
        "#figures-list()",
        f'#include "chapters/{files["preface"]}"',
        "#to-recto()",
        '#set page(numbering: "1")',
        "#counter(page).update(1)",
    ]
    appendix_started = False
    for chapter in found[1:]:
        if chapter.number in PARTS:
            number, title = PARTS[chapter.number]
            lines.append(f'#part-page("{number}", "{title}")')
        if chapter.number is None and not appendix_started:
            lines.append('#part-page("", "Appendices")')
            appendix_started = True
        lines.append(f'#include "chapters/{files[chapter.folder]}"')
    return "\n".join(lines) + "\n"


def build(planner: bool, out: Path, pages: bool) -> None:
    # Intermediate files are rebuilt every time; finished PDFs of other editions stay.
    for stale in ("chapters", "figures", "pages"):
        shutil.rmtree(BUILD / stale, ignore_errors=True)
    found = chapters()
    figures(found)
    included = ",".join(c.folder for c in found)
    files = {c.folder: convert(c, planner, included) for c in found}
    main = BUILD / "main.typ"
    main.write_text(main_typ(found, files, planner), encoding="utf-8", newline="\n")
    typst = tool("typst")
    subprocess.run([typst, "compile", "--root", str(HERE), str(main), str(out)], check=True)
    print(f"book: {out}")
    if pages:
        page_images(typst, main)


def page_images(typst: str, main: Path) -> None:
    """Every page as a PNG, and an overview sheet of them in spreads, for review."""
    pattern = BUILD / "pages" / "page-{0p}.png"
    pattern.parent.mkdir(parents=True, exist_ok=True)
    args = [typst, "compile", "--root", str(HERE), "--ppi", "60", str(main), str(pattern)]
    subprocess.run(args, check=True)
    names = sorted(p.name for p in pattern.parent.glob("page-*.png"))
    # The first page is a right-hand page, so an empty cell opens the first spread.
    cells = ["[]"] + [f'image("pages/{name}", width: 100%)' for name in names]
    sheet = BUILD / "sheet.typ"
    page = "#set page(width: 420mm, height: auto, margin: 6mm, fill: luma(200))\n"
    gaps = "column-gutter: (0mm, 6mm) * 3, row-gutter: 6mm"
    grid = f"#grid(columns: 6, {gaps}, {', '.join(cells)})\n"
    sheet.write_text(page + grid, encoding="utf-8", newline="\n")
    subprocess.run([typst, "compile", str(sheet), str(BUILD / "sheet.png")], check=True)
    print(f"pages: {pattern.parent}, overview: {BUILD / 'sheet.png'}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--reader", action="store_true", help="leave out the planner boxes")
    parser.add_argument("--pages", action="store_true", help="also write PNGs of every page")
    parser.add_argument("--out", type=Path, help="where to write the PDF")
    args = parser.parse_args(argv)
    planner = not args.reader
    name = "the-factory.pdf" if planner else "the-factory-reader.pdf"
    out = (args.out or BUILD / name).resolve()
    build(planner, out, args.pages)
    return 0


if __name__ == "__main__":
    sys.exit(main())
