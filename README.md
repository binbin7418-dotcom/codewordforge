# CodeWordForge

Generate verified codeword puzzle book interiors (KDP-ready PDF):
interlocking word grids, one-to-one number keys, given letters, and a
solutions section.

## Run (dev)

```
python gui.py                        # desktop app (needs reportlab)
python codeword_forge.py 50 out/     # 50-puzzle book
<venv python> test/acceptance_test.py
```

## How it works

`codeword_forge.py` places words crossword-strict: letter conflicts
fail, non-crossing cells need empty perpendicular neighbours, and end
caps must be clear — so every run in a finished grid is a placed word
by construction. A multi-pass full-scan fill picks the best-crossing
spot for each word. `verify_puzzle` then re-proves everything
independently: run validity (3+ = real word, 2 = valid two-letter
word), no isolated letters, mapping bijection both ways, givens
consistent with the solution, cell conservation. Failed candidates
are discarded and regenerated with the next seed.

The word list (`word_list.py`, 1,325 words) is corpus-harvested from
real prose and intersected with a dictionary set — real English by
construction, no hand-typed filler.

## Scope

Interior PDF only (no cover/ISBN). Numbers run 1..N over the letters
each puzzle actually uses.
