# Contributing

## The one rule that matters

**A new pattern or indicator needs evidence, not an argument.** Open the PR with a
`tools/validate.py` run showing it beats baseline:

```console
$ python3 tools/validate.py SMH --pattern your_pattern --horizon 10

SMH  2021-09-07 -> 2026-09-04  (1255 sessions)  10-day forward return

  your_pattern           n=38    mean  +2.90%  median  +2.10%  win  63.2%
  baseline (any day)     n=1245  mean  +1.19%  median  +1.14%  win  56.5%

  edge +1.71pp over baseline  ->  signal holds
```

Fewer than 15 occurrences is not enough. Test on more than one ticker if you can, and
say so if you could not — "one ticker, 35 events, provisional" is a fine caveat and a
bad thing to leave out. Textbook provenance is not evidence: the O'Neil follow-through
day is in this repo *as an inverted signal* on SOXX because that is what the data said.

Negative results are welcome as PRs too. A pattern proven not to work, with the numbers,
is worth more than one asserted to work.

## What is wanted

- **More validated patterns** in `tools/validate.py`, per the rule above.
- **Data providers** in `tools/data.py` — especially anything that returns Korean ETF
  holdings, which neither current provider covers.
- **Bug reports with a reproducing command.**

## What is not wanted

- Buy/sell recommendations, price targets, or anything that reads as advice. The
  four-state verdict vocabulary (`worth reviewing / conditional / on hold / low
  priority`) is deliberate, and `.claude/skills/etf-compliance-rules/` enforces it.
- New runtime dependencies. `tools/` is standard library only, and staying that way is
  most of why it is easy to run.
- Indicators that cannot be computed from an available source. If the data is not
  obtainable, the harness records a coverage gap — it does not estimate.

Open PRs against `main`, which is the English branch. `ko` is the Korean working branch
and the upstream source; it is translated onto `main` periodically, so a change landing
on `main` may be re-stated there rather than merged.

## Working on it

```bash
python3 tools/validate.py --self-check     # must print "ok"
python3 tools/score.py --self-check        # must print "ok"
python3 tools/score.py SOXX --horizon swing
```

There is no test framework. Non-trivial logic carries a `--self-check` that fails
loudly if it breaks; add to it rather than introducing a suite.

Style: match what is there. Comments explain *why*, not *what* — most of the comments
in `tools/` record the mistake that motivated the line.

## Before you open the PR

- No API keys, tokens, account numbers, or personal holdings in the diff. `.env` and
  `private/` are gitignored; check anything new you added. See [SECURITY.md](SECURITY.md).
- Real output pasted in the PR body, not a description of what it would print.
- If you changed a weight, a band or a threshold, say what evidence moved it.

By contributing you agree your work is licensed under the [MIT License](LICENSE).
