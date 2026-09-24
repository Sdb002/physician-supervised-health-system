# Exercise Dataset Schema — `exercises.csv`

One row per exercise. Used by `src/lifestyle/` to build FITT-VP prescriptions and
estimate energy expenditure (`kcal = MET × weight_kg × hours`).

> Current rows are DEMO placeholders with MET values approximated from the
> Compendium of Physical Activities (Ainsworth et al., 2011). Replace or extend
> freely keeping these columns; cite per row in `source`.

## Columns

| Column | Type | Description |
|---|---|---|
| `exercise_id` | string | Unique ID, pattern `E###`. |
| `name_en` | string | English name. |
| `name_bn` | string | Bangla name. |
| `category` | string | `aerobic`, `strength`, or `flexibility`. |
| `met_value` | float | Metabolic equivalent of task (1.0–20.0). |
| `equipment` | string | Required equipment, `none` if bodyweight only. |
| `intensity_level` | string | `light` (< 3 MET), `moderate` (3–5.9 MET), `vigorous` (≥ 6 MET). Must be consistent with `met_value`. |
| `contra_tags` | string | `\|`-separated risk flags (may be empty). The contraindication gate excludes exercises whose tags intersect the patient's excluded tags. |
| `source` | string | Citation. `DEMO` marks placeholder data. |

## Contra-tag vocabulary

`high_impact`, `high_exertion`, `knee_stress`, `wrist_stress`, `abdominal_pressure`,
`supine_position`, `balance_required`.

Register any tag used by a condition rule in `data/reference/contraindications.yaml`.

## Validation rules

- `exercise_id` unique, matches `E\d+`.
- `met_value` numeric in (0, 20]; `intensity_level` consistent with the MET bands above.
- `category` from the list above; contra-tags from the vocabulary (warns on unknown).
