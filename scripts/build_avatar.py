"""Generate the profile avatar: a pixel MB monogram with one pixel out of line.

Same palette and same pixel grammar as the header and the project covers, so the
avatar, the profile and the portfolio read as one system. GitHub crops avatars to
a circle, so every drawn cell stays inside the inscribed circle.

    python scripts/build_avatar.py
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BG, INK, ACCENT = "#08090B", "#F5F7FA", "#F0883E"
GRID, CELL = 15, 32           # 15 x 15 cells of 32px -> 480px
SIZE = GRID * CELL

# 7 rows x 5 columns per letter, one empty column between them.
LETTERS = [
    ["X...X",
     "XX.XX",
     "X.X.X",
     "X...X",
     "X...X",
     "X...X",
     "X...X"],
    ["XXXX.",
     "X...X",
     "X...X",
     "XXXX.",
     "X...X",
     "X...X",
     "XXXX."],
]
COL0, ROW0 = 2, 4             # top-left cell of the monogram inside the grid
ODD = (11, 10)            # the one pixel that steps out of the grid


def cells():
    """Yield (col, row) for every lit pixel of the monogram."""
    for i, letter in enumerate(LETTERS):
        for r, line in enumerate(letter):
            for c, ch in enumerate(line):
                if ch == "X":
                    yield COL0 + i * 6 + c, ROW0 + r


def svg() -> str:
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{SIZE}" height="{SIZE}" '
           f'viewBox="0 0 {SIZE} {SIZE}" role="img" aria-label="MB monogram">',
           f'<rect width="{SIZE}" height="{SIZE}" fill="{BG}"/>']
    for c, r in cells():
        x, y = c * CELL, r * CELL
        if (c, r) == ODD:     # one pixel leaves the grid — the only anomaly
            out.append(f'<rect x="{x + CELL * 0.34:.1f}" y="{y + CELL * 0.34:.1f}" '
                       f'width="{CELL}" height="{CELL}" fill="{ACCENT}"/>')
        else:
            out.append(f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" fill="{INK}"/>')
    out.append("</svg>")
    return "\n".join(out)


def main():
    path = ROOT / "assets" / "avatar.svg"
    path.write_text(svg(), encoding="utf-8")
    print(f"{path.relative_to(ROOT)}  {path.stat().st_size} bytes  {SIZE}x{SIZE}")


if __name__ == "__main__":
    main()
