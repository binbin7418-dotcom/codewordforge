#!/usr/bin/env python3
"""
CodeWordForge — codeword puzzle book interior generator (KDP-ready).

A codeword puzzle is a crossword grid where every letter is replaced
by a number: the same number always means the same letter, and a few
letters are given as a starting key. Solvers love them; making them by
hand takes hours. CodeWordForge places interlocking words from a
built-in common-word list, builds the number key, picks the given
letters — and verifies every puzzle before it goes in the book:

  * every horizontal/vertical run of 3+ cells is a real placed word
  * every 2-cell run is a valid two-letter word
  * no letter cell is isolated (every cell belongs to a word run)
  * the letter<->number mapping is a bijection (checked both ways)
  * the given letters match the solution exactly
  * cell conservation: letters + blocks = grid size, per puzzle

If a candidate grid fails any check it is discarded and regenerated
with the next seed — failed puzzles never reach the PDF.

Output: one print-ready interior PDF (puzzle pages, then a solutions
section) at the trim size you pick, plus a build report with the
per-puzzle verification numbers.

Local only. No network. Uses reportlab + the built-in word list.
"""
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from word_list import WORDS, TWO_LETTER

WORD_SET = set(WORDS)


def _runs(grid, size):
    """All maximal letter runs (row-wise and column-wise) as strings."""
    out = []
    for r in range(size):
        run = ""
        for c in range(size):
            ch = grid[r][c]
            if ch:
                run += ch
            else:
                if run:
                    out.append(run)
                run = ""
        if run:
            out.append(run)
    for c in range(size):
        run = ""
        for r in range(size):
            ch = grid[r][c]
            if ch:
                run += ch
            else:
                if run:
                    out.append(run)
                run = ""
        if run:
            out.append(run)
    return out


def verify_grid(grid, size, placed):
    """Return a list of problems (empty = valid codeword grid)."""
    problems = []
    runs = _runs(grid, size)
    placed_set = set(placed)
    for run in runs:
        if len(run) >= 3 and run not in placed_set and run not in WORD_SET:
            problems.append(f"run '{run}' is not a placed word")
        elif len(run) == 2 and run not in TWO_LETTER and run not in placed_set:
            problems.append(f"2-run '{run}' is not a valid word")
    # isolation: every letter cell must sit in a run of length >= 2
    def run_len_at(r, c, dr, dc):
        n = 1
        rr, cc = r + dr, c + dc
        while 0 <= rr < size and 0 <= cc < size and grid[rr][cc]:
            n += 1
            rr += dr
            cc += dc
        rr, cc = r - dr, c - dc
        while 0 <= rr < size and 0 <= cc < size and grid[rr][cc]:
            n += 1
            rr -= dr
            cc -= dc
        return n
    letters = 0
    for r in range(size):
        for c in range(size):
            if grid[r][c]:
                letters += 1
                if run_len_at(r, c, 0, 1) < 2 and run_len_at(r, c, 1, 0) < 2:
                    problems.append(f"isolated letter at {r},{c}")
    if letters + sum(1 for r in range(size) for c in range(size)
                     if not grid[r][c]) != size * size:
        problems.append("cell conservation failed")
    return problems


def _can_place(grid, size, word, r, c, dr, dc):
    """Crossword-strict placement test. Returns crossings or -1.

    Strict rules (this is what makes the final grid provable):
    letter conflicts fail; a non-crossing cell's perpendicular
    neighbours must be empty (so no accidental side-runs can form);
    both end caps must be empty/outside (so the run IS the word).
    Under these rules every run in the finished grid is a placed word
    by construction — verify_grid then proves it independently.
    """
    crossings = 0
    for i, ch in enumerate(word):
        rr, cc = r + dr * i, c + dc * i
        if not (0 <= rr < size and 0 <= cc < size):
            return -1
        cell = grid[rr][cc]
        if cell:
            if cell != ch:
                return -1
            crossings += 1
        else:
            pr, pc = (1, 0) if dr == 0 else (0, 1)
            for s in (-1, 1):
                nr, nc = rr + pr * s, cc + pc * s
                if 0 <= nr < size and 0 <= nc < size and grid[nr][nc]:
                    return -1
    for (rr, cc) in ((r - dr, c - dc), (r + dr * len(word), c + dc * len(word))):
        if 0 <= rr < size and 0 <= cc < size and grid[rr][cc]:
            return -1
    return crossings


def generate_puzzle(size, seed, givens_count=3, target_words=None):
    """Generate one verified puzzle. Returns dict or None."""
    if target_words is None:
        target_words = max(12, round(size * size / 7))
    rng = random.Random(seed)
    pool = [w for w in WORDS if 3 <= len(w) <= size]
    for _attempt in range(40):
        grid = [[""] * size for _ in range(size)]
        placed = []
        candidates = pool[:]
        rng.shuffle(candidates)
        candidates.sort(key=len, reverse=True)
        # seed word across the middle
        first = candidates.pop(0)
        r0, c0 = size // 2, max(0, (size - len(first)) // 2)
        for i, ch in enumerate(first):
            grid[r0][c0 + i] = ch
        placed.append(first)
        # multi-pass fill: full position scan, best-crossing spot wins
        for _pass in range(3):
            if len(placed) >= target_words:
                break
            on_grid = {ch for row in grid for ch in row if ch}
            remaining = []
            for word in candidates:
                if len(placed) >= target_words:
                    remaining.append(word)
                    continue
                if not on_grid.intersection(word):
                    remaining.append(word)
                    continue
                best = None
                L = len(word)
                for dr, dc in ((0, 1), (1, 0)):
                    rmax = size - (L if dr else 1)
                    cmax = size - (L if dc else 1)
                    for r in range(rmax + 1):
                        for c in range(cmax + 1):
                            cr = _can_place(grid, size, word, r, c, dr, dc)
                            if cr >= 1 and (best is None or cr > best[0]):
                                best = (cr, r, c, dr, dc)
                if best is not None:
                    _cr, r, c, dr, dc = best
                    for i, ch in enumerate(word):
                        grid[r + dr * i][c + dc * i] = ch
                    placed.append(word)
                else:
                    remaining.append(word)
            candidates = remaining
        if len(placed) < max(8, target_words * 0.55):
            continue
        problems = verify_grid(grid, size, placed)
        if problems:
            continue
        letters_used = sorted({ch for row in grid for ch in row if ch})
        if len(letters_used) < 14:
            continue
        numbers = list(range(1, len(letters_used) + 1))
        rng.shuffle(numbers)
        mapping = dict(zip(letters_used, numbers))       # letter -> number
        inverse = {v: k for k, v in mapping.items()}     # number -> letter
        # givens: prefer frequent letters
        freq = {}
        for row in grid:
            for ch in row:
                if ch:
                    freq[ch] = freq.get(ch, 0) + 1
        by_freq = sorted(letters_used, key=lambda ch: -freq[ch])
        givens = {mapping[ch]: ch for ch in by_freq[:givens_count]}
        number_grid = [[mapping[ch] if ch else 0 for ch in row] for row in grid]
        return {"size": size, "solution": grid, "placed": placed,
                "mapping": mapping, "inverse": inverse, "givens": givens,
                "number_grid": number_grid,
                "letters_used": len(letters_used),
                "letter_cells": sum(freq.values())}
    return None


def verify_puzzle(p):
    """Full independent re-check of a generated puzzle dict."""
    problems = verify_grid(p["solution"], p["size"], p["placed"])
    m, inv = p["mapping"], p["inverse"]
    if len(m) != len(set(m.values())):
        problems.append("mapping is not injective")
    if any(inv.get(n) != ch for ch, n in m.items()):
        problems.append("inverse mapping inconsistent")
    for num, ch in p["givens"].items():
        if m.get(ch) != num:
            problems.append(f"given {num}={ch} contradicts the solution")
    for r in range(p["size"]):
        for c in range(p["size"]):
            ch = p["solution"][r][c]
            expected = m[ch] if ch else 0
            if p["number_grid"][r][c] != expected:
                problems.append(f"number grid mismatch at {r},{c}")
                return problems
    return problems


def build_book(count, outdir, size=15, givens=3, base_seed=42,
               trim="6x9", title="Codeword Puzzle Book"):
    os.makedirs(outdir, exist_ok=True)
    puzzles, failures = [], 0
    for i in range(count):
        p = generate_puzzle(size, seed=base_seed + i * 977,
                            givens_count=givens)
        if p is None:
            failures += 1
            continue
        problems = verify_puzzle(p)
        if problems:
            failures += 1
            continue
        p["problems"] = problems
        puzzles.append(p)
    pdf_path = os.path.join(outdir, "codewordforge_interior.pdf")
    pages = _write_pdf(pdf_path, puzzles, size, trim, title)
    L = ["# CodeWordForge — book build & verification report", "",
         f"Puzzles requested: {count}  ·  Built & verified: {len(puzzles)}"
         f"  ·  Generation failures (discarded): {failures}",
         f"Grid: {size}x{size}  ·  Given letters per puzzle: {givens}",
         f"Interior PDF: {os.path.basename(pdf_path)} ({pages} pages)", "",
         "## Per puzzle"]
    for i, p in enumerate(puzzles, 1):
        L.append(f"- Puzzle {i}: {len(p['placed'])} words placed, "
                 f"{p['letter_cells']} letter cells, "
                 f"{p['letters_used']} distinct letters, "
                 f"verification PASS (runs valid, mapping bijective, "
                 f"givens consistent, cells conserved)")
    L += ["", "## Honest limits",
          "- Numbers run 1..N for the N distinct letters in each puzzle",
          "  (a 15x15 grid rarely uses all 26 letters); the key strip on",
          "  each page shows exactly the numbers in play.",
          "- Words come from a built-in common-English list ("
          f"{len(WORDS)} words); no proper nouns.",
          "- Interior only: no cover, no ISBN — KDP cover is a separate step."]
    report_path = os.path.join(outdir, "book_report.md")
    with open(report_path, "w", encoding="utf-8") as fh:
        fh.write("\n".join(L) + "\n")
    return {"puzzles": puzzles, "failures": failures, "pdf_path": pdf_path,
            "pages": pages, "report_path": report_path,
            "verdict": len(puzzles) == count}


def _write_pdf(pdf_path, puzzles, size, trim, title):
    from reportlab.lib.pagesizes import inch
    from reportlab.pdfgen import canvas

    page_sizes = {"6x9": (6 * inch, 9 * inch), "7x10": (7 * inch, 10 * inch),
                  "8.5x11": (8.5 * inch, 11 * inch)}
    pw, ph = page_sizes.get(trim, page_sizes["6x9"])
    c = canvas.Canvas(pdf_path, pagesize=(pw, ph))
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(pw / 2, ph / 2 + 20, title)
    c.setFont("Helvetica", 11)
    c.drawCentredString(pw / 2, ph / 2 - 6,
                        f"{len(puzzles)} codeword puzzles with solutions")
    c.drawCentredString(pw / 2, ph / 2 - 24,
                        "Each number stands for one letter. "
                        "Use the given letters to start.")
    c.showPage()

    def draw_grid(c, p, with_letters):
        n = p["size"]
        cell = min((pw - 72) / n, 26)
        grid_w = cell * n
        x0 = (pw - grid_w) / 2
        ytop = ph - 96
        for r in range(n):
            for col in range(n):
                x = x0 + col * cell
                y = ytop - (r + 1) * cell
                ch = p["solution"][r][col]
                if not ch:
                    c.setFillColorRGB(0.12, 0.12, 0.12)
                    c.rect(x, y, cell, cell, stroke=0, fill=1)
                    continue
                c.setFillColorRGB(1, 1, 1)
                c.setStrokeColorRGB(0.35, 0.35, 0.35)
                c.rect(x, y, cell, cell, stroke=1, fill=1)
                num = p["number_grid"][r][col]
                c.setFillColorRGB(0.25, 0.25, 0.25)
                c.setFont("Helvetica", cell * 0.26)
                c.drawString(x + 1.5, y + cell - cell * 0.32, str(num))
                shown = None
                if with_letters:
                    shown = ch
                elif num in p["givens"]:
                    shown = p["givens"][num]
                if shown:
                    c.setFillColorRGB(0, 0, 0)
                    c.setFont("Helvetica-Bold", cell * 0.5)
                    c.drawCentredString(x + cell / 2, y + cell * 0.18, shown)
        return ytop - n * cell

    for i, p in enumerate(puzzles, 1):
        c.setFont("Helvetica-Bold", 15)
        c.drawString(36, ph - 48, f"Puzzle {i}")
        yend = draw_grid(c, p, with_letters=False)
        # key strip
        nums = sorted(p["inverse"])
        c.setFont("Helvetica", 8.5)
        c.drawString(36, yend - 22, "Key (given letters filled in):")
        kx, ky = 36, yend - 48
        per_row = 13
        for j, num in enumerate(nums):
            x = kx + (j % per_row) * ((pw - 72) / per_row)
            y = ky - (j // per_row) * 30
            c.rect(x, y, 26, 22, stroke=1, fill=0)
            c.setFont("Helvetica", 7)
            c.drawString(x + 2, y + 13, str(num))
            if num in p["givens"]:
                c.setFont("Helvetica-Bold", 11)
                c.drawCentredString(x + 15, y + 3, p["givens"][num])
        c.showPage()
    c.setFont("Helvetica-Bold", 16)
    c.drawString(36, ph - 60, "Solutions")
    c.showPage()
    for i, p in enumerate(puzzles, 1):
        c.setFont("Helvetica-Bold", 13)
        c.drawString(36, ph - 48, f"Solution {i}")
        draw_grid(c, p, with_letters=True)
        c.showPage()
    pages = c.getPageNumber()
    c.save()
    return pages


def main(argv):
    if len(argv) != 3:
        print("usage: codeword_forge.py <puzzle-count> <outdir>")
        return 2
    s = build_book(int(argv[1]), argv[2])
    print(f"puzzles={len(s['puzzles'])} failures={s['failures']} "
          f"pages={s['pages']} verdict={s['verdict']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
