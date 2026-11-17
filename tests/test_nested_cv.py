"""The recommender comparison is a nested cross-validation.

scripts/train_recommenders.py tunes two of the models it compares. These
tests hold it to what "nested" means there:

- a search fits and scores only on the rows it is given;
- every outer fold's searches are given that fold's training archetypes and
  nothing else, and the fold's models are fitted with what those searches
  chose;
- which tuned model counts as "selected" in a fold is decided by the fold's
  searches, not by how the models then score on the archetypes held out.

So the archetypes a tuned model is judged on took no part in choosing its
hyperparameters, or in choosing it. Nothing is trained here: the tuned models
are stand-ins that record the rows they see.
"""

import importlib.util
import sys
from pathlib import Path

import numpy as np
import pytest
from sklearn.model_selection import GroupKFold

_SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "train_recommenders.py"
NAMES = ("row_number", "signal", "distraction")


@pytest.fixture(scope="module")
def train():
    # scripts/ is not a package: load the training script from its file
    spec = importlib.util.spec_from_file_location("train_recommenders_under_test", _SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
        yield module
    finally:
        sys.modules.pop(spec.name, None)


def _frame(train, archetypes=15, queries_each=2, items=6):
    """A small frame whose first feature is each row's own number, so a
    stand-in estimator can say exactly which rows it was shown."""
    rng = np.random.default_rng(0)
    rows = archetypes * queries_each * items
    signal, distraction = rng.normal(size=rows), rng.normal(size=rows)
    label = signal + 0.1 * rng.normal(size=rows)
    return train.Frame(
        X=np.column_stack([np.arange(rows, dtype=float), signal, distraction]),
        y=label + rng.normal(0.0, 0.05, size=rows),
        label=label,
        groups=np.repeat([f"archetype-{i:02d}" for i in range(archetypes)], queries_each * items),
        queries=np.repeat(np.arange(archetypes * queries_each), items),
        served=np.ones(rows, dtype=bool),
        weight=np.ones(rows),
        baseline=0.5 * signal + distraction,
        n_items=items,
        top_k=3,
    )


class _StandIn:
    """In place of an estimator: keeps the rows it was fitted on and asked to
    score, and ranks worse the larger its one hyperparameter is."""

    def __init__(self, log, name, params):
        self.log, self.name, self.params = log, name, params

    def fit(self, X, y):
        self.fitted = frozenset(X[:, 0].astype(int).tolist())
        return self

    def predict(self, X):
        self.log.append({"model": self.name, "params": dict(self.params), "fitted": self.fitted,
                         "scored": frozenset(X[:, 0].astype(int).tolist())})
        return X[:, 1] + self.params["blur"] * X[:, 2]


def _maker(log, name):
    return lambda params, feature_names: _StandIn(log, name, params)


def _archetypes(frame, rows) -> set:
    return {frame.groups[i] for i in rows}


def test_a_search_fits_and_scores_only_the_rows_it_is_given(train, monkeypatch):
    monkeypatch.setattr(train, "TUNING_ITER", 3)
    frame = _frame(train)
    given, held_out = next(GroupKFold(n_splits=5).split(frame.X, groups=frame.groups))
    log = []

    tuned = train.tune(_maker(log, "m"), {"blur": [0.0, 0.5, 2.0]}, frame, NAMES, rows=given)

    allowed = set(given.tolist())
    assert len(log) == 3 * train.TUNING_CV_FOLDS  # every candidate, on every fold of the search
    for step in log:
        assert step["fitted"] <= allowed and step["scored"] <= allowed
        # validated on archetypes the fit had not seen: the search is grouped too
        assert not _archetypes(frame, step["fitted"]) & _archetypes(frame, step["scored"])
    assert not set().union(*(step["fitted"] | step["scored"] for step in log)) & set(held_out.tolist())
    # each candidate was validated on every given row exactly once
    for blur in (0.0, 0.5, 2.0):
        validated = [step["scored"] for step in log if step["params"]["blur"] == blur]
        assert sorted(i for rows in validated for i in rows) == sorted(allowed)
    # and the candidate that ranks best is the one it settles on
    assert tuned.params == {"blur": 0.0} and 0.9 < tuned.score <= 1.0


def test_a_search_over_everything_uses_every_row(train, monkeypatch):
    monkeypatch.setattr(train, "TUNING_ITER", 3)
    frame = _frame(train)
    log = []
    train.tune(_maker(log, "m"), {"blur": [0.0, 0.5, 2.0]}, frame, NAMES)
    assert set().union(*(step["scored"] for step in log)) == set(range(len(frame.X)))


def test_every_outer_fold_is_tuned_on_its_own_training_archetypes(train, monkeypatch):
    frame = _frame(train)
    folds = list(GroupKFold(n_splits=train.N_FOLDS).split(frame.X, groups=frame.groups))
    log, searches = [], []
    models = {"random_forest": (_maker(log, "random_forest"), {}),
              "hist_gradient_boosting": (_maker(log, "hist_gradient_boosting"), {})}
    monkeypatch.setattr(train, "TUNED_MODELS", models)

    def tune(make_estimator, search_space, frame_, feature_names, rows=None):
        """Each search is given a result of its own, so that what a fold was
        tuned to can be told apart from every other fold's and from the
        shipped hyperparameters. The forest's searches score higher in the
        first two folds, the boosting's in the rest."""
        name = make_estimator(None, feature_names).name
        fold = len(searches) // len(models) + 1
        searches.append({"model": name, "rows": frozenset(rows.tolist())})
        forest_ahead = fold <= 2
        score = 0.9 if (name == "random_forest") == forest_ahead else 0.8
        blur = fold / 10 + (0.0 if name == "random_forest" else 0.05)
        return train.Tuned({"blur": blur}, score)

    monkeypatch.setattr(train, "tune", tune)
    shipped = {name: train.Tuned({"blur": 3.0}, 0.5) for name in models}

    evaluation = train.evaluate(frame, NAMES, shipped)

    # one search per tuned model per outer fold, each over that fold's
    # training rows: never a row of the archetypes the fold is judged on
    assert [search["rows"] for search in searches] == [
        frozenset(train_idx.tolist()) for train_idx, _ in folds for _ in models]
    for search, (_, test_idx) in zip(searches, [fold for fold in folds for _ in models]):
        assert not search["rows"] & set(test_idx.tolist())

    for number, (train_idx, test_idx) in enumerate(folds, 1):
        record = evaluation["folds"][number - 1]
        assert record["fold"] == number
        assert record["n_train_archetypes"] + record["n_test_archetypes"] == 15
        judged = [step for step in log if step["scored"] == frozenset(test_idx.tolist())]
        # every model judged on the fold was fitted on the fold's training rows
        assert all(step["fitted"] == frozenset(train_idx.tolist()) for step in judged)
        for name in models:
            chosen = record["models"][name]["params"]
            assert chosen == {"blur": pytest.approx(number / 10 + (0.0 if name == "random_forest" else 0.05))}
            used = [step["params"] for step in judged if step["model"] == name]
            # fitted with what this fold's search chose, and once more with the
            # shipped hyperparameters for the figure the script used to report
            assert used == [chosen, {"blur": 3.0}]
        assert record["preferred"] == ("random_forest" if number <= 2 else "hist_gradient_boosting")

    # the selected model is whichever tuned model each fold's search preferred
    # (here the one that then scores lower in the last three folds: the choice
    # does not look at the held-out scores)
    per_fold = [fold["models"][fold["preferred"]]["spearman"] for fold in evaluation["folds"]]
    assert evaluation["selected_model"]["spearman"]["mean"] == pytest.approx(np.mean(per_fold))
    assert evaluation["metrics"]["random_forest"]["spearman"]["mean"] == pytest.approx(
        np.mean([fold["models"]["random_forest"]["spearman"] for fold in evaluation["folds"]]))
    better = [max(model["spearman"] for model in fold["models"].values()) for fold in evaluation["folds"]]
    assert evaluation["selected_model"]["spearman"]["mean"] < np.mean(better)
    # the earlier, non-nested figure: the shipped hyperparameters on every fold
    assert evaluation["tuned_on_all_archetypes"]["random_forest"]["spearman"]["mean"] == pytest.approx(
        np.mean([fold["models"]["random_forest"]["spearman_tuned_on_all"] for fold in evaluation["folds"]]))
    assert set(evaluation["metrics"]) == set(train.MODEL_NAMES)


def test_hyperparameters_a_fold_shares_with_the_shipped_model_are_not_fitted_twice(train, monkeypatch):
    frame = _frame(train)
    log = []
    models = {"random_forest": (_maker(log, "random_forest"), {"blur": [0.0, 0.5, 2.0]}),
              "hist_gradient_boosting": (_maker(log, "hist_gradient_boosting"), {"blur": [1.0, 3.0, 5.0]})}
    monkeypatch.setattr(train, "TUNED_MODELS", models)
    monkeypatch.setattr(train, "TUNING_ITER", 3)

    shipped = train.tune_models(frame, NAMES)
    assert {name: tuned.params for name, tuned in shipped.items()} == {
        "random_forest": {"blur": 0.0}, "hist_gradient_boosting": {"blur": 1.0}}
    assert train.preferred(shipped) == "random_forest"

    log.clear()
    evaluation = train.evaluate(frame, NAMES, shipped)
    folds = list(GroupKFold(n_splits=train.N_FOLDS).split(frame.X, groups=frame.groups))
    for _, test_idx in folds:
        judged = [step for step in log if step["scored"] == frozenset(test_idx.tolist())]
        assert len(judged) == len(models)  # the same search result: one fit serves both figures
    for name in models:
        assert evaluation["tuned_on_all_archetypes"][name] == evaluation["metrics"][name]
    assert evaluation["selected_model"] == evaluation["metrics"]["random_forest"]
