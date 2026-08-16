# Token discipline

1. **`.clineignore` excludes** `data/`, `*.parquet`, `*.geojson`, `*.tif`,
   `*.zip`, `.venv/`, `site/`, `.git/`. Non-negotiable — one accidental
   `read_file` on a 40 MB GeoJSON ends the project.
2. **Never inspect data by reading it.** Use `python -m kinetiek.peek <name>` —
   shape, dtypes, null counts, 5 rows, hard-capped at 40 lines.
3. **One task = one deliverable.** One ingest module, or one figure, or one
   essay. `/newtask` between every one.
4. **Plan in Plan mode, always.** Planning tokens are the cheapest tokens in
   the project.
5. **Route mechanical work down-market.** Docstrings, renames, test scaffolds,
   type stubs → the cheapest capable model. Do not spend frontier tokens on
   boilerplate.
6. **Test output must be short.** `pytest -q --tb=line -x`. A full traceback
   is ~3k tokens; a line summary is ~80.
7. **`make check` is the only verification command.** One invocation, one
   bounded output block.
8. **Never explore to find structure.** The tree is hand-written. Exploration
   is the single largest source of token waste.
9. **Focus Chain on, Auto Compact on, context cap ~200k** — not the 1M window;
   every turn re-sends context and long contexts burn the budget before
   producing anything.
10. **Close every phase with `/phase-close`** — update memory bank, log the
    ledger, `/newtask`. Commit after every task.

## Budget context
2,000,000 tokens ≈ 50 well-scoped tasks. The task count is the binding
constraint, not ambition. Tripwires live in `memory-bank/progress.md`; when
one is crossed, cut scope per the plan, do not push through.
