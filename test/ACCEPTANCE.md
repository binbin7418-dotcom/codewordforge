# CodeWordForge — Acceptance

Seeded test (pagesmith venv python: reportlab + pypdf):
`test/acceptance_test.py` — full output: `test/acceptance_results.txt`

**Result: 15/15 checks passed.**

Builds a 3-puzzle 11×11 book with fixed seed 7 and asserts the
guarantees the product sells:

- All 3 puzzles built, 0 generation failures
- Each puzzle passes an independent re-verification (verify_puzzle
  returns zero problems): valid word runs, valid two-letter runs,
  no isolated letters, bijective mapping, consistent givens
- Cell conservation exact per puzzle (73+48, 69+52, 70+51 = 121)
- Exactly 3 givens per puzzle; ≥14 distinct letters (measured 19)
- PDF page count exact: 1 title + 3 puzzles + 1 solutions divider
  + 3 solutions = 8 pages
- Determinism: regenerating with seed 7 reproduces puzzle 1's
  solution grid and mapping exactly
- Default-size spot check (15×15, seed 42001): 25 words, 128 letter
  cells, 20 distinct letters, verified clean in 0.7 s
- Word list provenance: 1,325 words, corpus ∩ dictionary (see
  word_list.py header); GUI + engine compile clean
