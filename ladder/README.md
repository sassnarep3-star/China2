# Cost ladder — CNY → USD, $10,000 to $400,000

Generated, source-linked cost model for moving RMB out of mainland China into USD as a US citizen.

- **Site:** `ladder/index.html` (published at `/China2/ladder/`)
- **Model:** `ladder/model.py` — all data and arithmetic live here
- **Render:** `ladder/build.py` — writes the ten pages, the root navigation hub and the downloads
- **Verify:** `ladder/verify.py` — structure, citation coverage, ladder integrity, local links
- **Data:** `ladder/data/*.json`, `ladder/data/costs.csv` (600 rows)

## Reproduce

```sh
python3 ladder/model.py     # recompute 40 tiers x 15 routes
python3 ladder/build.py     # regenerate the static pages
python3 ladder/verify.py    # 0 failures expected
```

No install step, no runtime dependency, no browser-side network calls.

## Rules this directory follows

1. **Every published figure carries a source id and a locator.** See `sources.html`.
2. **Nothing unpublished is presented as a fact.** Missing commercial values are either blank and
   flagged, or listed in `assumptions.html` as a model assumption with an explicit range.
3. **Estimates are labelled.** "All-in cost" = verified bank fees where a tariff exists + a modelled
   FX-spread band. Rows where the fixed fee is unpublished are marked *partial*.
4. **Prior sessions' files are never edited.** The only shared files touched are the root
   `index.html` (navigation hub, generated) and a link line in `README.md`, both additively.

## Known limits

The FX spread is a commercial price and is not published by any regulator. Every estimate in this
directory therefore contains a band, not a quote. A bank's executable quote supersedes it. See
`flagged.html` for the full list of unverified items.
