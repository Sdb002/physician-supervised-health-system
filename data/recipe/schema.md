# Recipe Dataset Schema

Two files. **Recipes carry no nutrient columns** — per-serving nutrition is always
computed at runtime by `src/diet/recipe.py` from the ingredient list joined against
`data/food/bd_food.csv`. This keeps a single source of truth for nutrients.

> Current rows are DEMO placeholders. Replace with your real recipes keeping these
> columns, then run `py scripts/validate_datasets.py` (it cross-checks that every
> `food_id` referenced here exists in `bd_food.csv`).

## `recipes.csv` — metadata only

| Column | Type | Description |
|---|---|---|
| `recipe_id` | string | Unique ID, pattern `R###`. |
| `name_en` | string | English name. |
| `name_bn` | string | Bangla name. |
| `servings` | int | Number of servings the ingredient list yields (> 0). |
| `meal_type` | string | `\|`-separated: `breakfast`, `lunch`, `dinner`, `snack`. |
| `tags` | string | `\|`-separated descriptive tags (may be empty). Ingredient-derived exclusion tags (e.g. `high_sodium`) are **inherited automatically** from ingredients at runtime — do not duplicate them here. |
| `source` | string | Citation / provenance. `DEMO` marks placeholder data. |

## `recipe_ingredients.csv` — join table

| Column | Type | Description |
|---|---|---|
| `recipe_id` | string | References `recipes.csv`. |
| `food_id` | string | References `data/food/bd_food.csv`. |
| `qty_g` | float | Grams of the food **as consumed** (same basis as the food table), for the whole recipe (all servings). |

## Validation rules

- `recipe_id` unique in `recipes.csv`; every ingredient row's `recipe_id` exists there.
- Every `food_id` exists in `bd_food.csv`.
- `servings` integer > 0; `qty_g` > 0.
- Every recipe has at least one ingredient row.
