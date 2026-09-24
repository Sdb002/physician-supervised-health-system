# Offline training corpus

Public datasets used **once, offline** — e.g. to derive or cross-check nutrient
values, or to evaluate OCR extraction accuracy. Nothing in this directory is
read at runtime; the app only ever reads `data/food/`, `data/recipe/`,
`data/lifestyle/`, and `data/reference/`.

Drop downloaded public datasets into `public_datasets/` (they are not committed).
