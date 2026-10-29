#!/usr/bin/env python3
"""CodeWordForge seeded acceptance test (run with the pagesmith venv
python, which provides reportlab).

Generates a small book (3 puzzles, 11x11, fixed seed) and asserts the
guarantees the product sells:
  - every 3+ run in every grid is a real word, every 2-run is a valid
    two-letter word, no isolated letters
  - the letter<->number mapping is a bijection and the number grid
    matches the solution cell for cell
  - the given letters agree with the solution
  - cell conservation per puzzle
  - determinism: rebuilding with the same seed reproduces puzzle 1
    exactly (solution grid + mapping)
  - PDF page count = 1 title + N puzzles + 1 solutions divider + N
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pypdf import PdfReader

from codeword_forge import build_book, generate_puzzle, verify_puzzle

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out")
CHECKS = []


def check(name, ok, detail=""):
    CHECKS.append((name, bool(ok), detail))
    print(("PASS " if ok else "FAIL ") + name + (f" — {detail}" if detail else ""))


os.makedirs(OUT, exist_ok=True)
s = build_book(3, os.path.join(OUT, "book"), size=11, givens=3, base_seed=7)
check("all 3 puzzles built", len(s["puzzles"]) == 3 and s["verdict"],
      f"failures={s['failures']}")
for i, p in enumerate(s["puzzles"], 1):
    check(f"puzzle {i} independent re-verify clean", verify_puzzle(p) == [])
    letters = sum(1 for row in p["solution"] for ch in row if ch)
    blocks = sum(1 for row in p["solution"] for ch in row if not ch)
    check(f"puzzle {i} cell conservation", letters + blocks == 121,
          f"{letters}+{blocks}")
    check(f"puzzle {i} givens == 3", len(p["givens"]) == 3)
    check(f"puzzle {i} letters used >= 14", p["letters_used"] >= 14,
          f"{p['letters_used']}")
pages = len(PdfReader(s["pdf_path"]).pages)
check("PDF pages = 1 + 3 + 1 + 3", pages == 8, f"pages={pages}")

p_again = generate_puzzle(11, seed=7, givens_count=3)
first = s["puzzles"][0]
check("deterministic regeneration",
      p_again is not None and p_again["solution"] == first["solution"]
      and p_again["mapping"] == first["mapping"])

passed = sum(1 for _, ok, _ in CHECKS if ok)
print(f"\n{passed}/{len(CHECKS)} checks passed")
sys.exit(0 if passed == len(CHECKS) else 1)
