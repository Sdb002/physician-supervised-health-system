"""The food and dish names a patient record can exclude.

Open to anyone: the sign-up form needs the list before there is an account,
and it holds nothing but the names in the food table and the recipe list.
"""

from fastapi import APIRouter

from src.api.services import excludable_foods

router = APIRouter(prefix="/foods", tags=["foods"])


@router.get("/catalogue")
def catalogue() -> list[dict]:
    """Every dish, then every everyday food once, for the patient forms'
    "does not eat" picker."""
    return excludable_foods()
