"""Tags that dietary restrictions and the condition rules for pregnancy and
high cholesterol exclude on.

Derived from each food's group and English name rather than curated by hand,
so they hold for whatever food table is loaded; a recipe carries the tags of
every ingredient, in any amount, because a restriction or an allergy is about
presence, not share of the dish - and a dish finished with a spoon of ghee is
a dish cooked in ghee. The rules that use them are in
data/reference/dietary_restrictions.yaml and contraindications.yaml, and the
gate that applies them is src/clinical/contraindication.py.

    contains_meat       the meat group (poultry, offal and frog legs included)
    contains_beef       beef, calf and veal
    contains_pork       pork, ham and bacon
    contains_fish       the fish group other than shellfish, and fish oils
    contains_shellfish  prawn, shrimp, crab, lobster and molluscs
    contains_egg        the egg group, and mayonnaise
    contains_dairy      the dairy group, butter, cow ghee, milk-powder drinks
    contains_nuts       tree nuts and peanuts, and their oils
    contains_gluten     wheat, barley and rye, and what is made from them
    liver               liver of any animal, and fish-liver oil
    high_mercury        shark, swordfish, marlin, tilefish, king mackerel,
                        bigeye tuna, orange roughy
    alcohol             toddy and other alcoholic drinks
    solid_fat           the cooking fats that are solid at room temperature:
                        butter, ghee (cow's or vegetable), vanaspati,
                        margarine, coconut oil and palm oil - animal fats,
                        tropical oils and partially hydrogenated fats. The
                        food table records no saturated or trans fat, so
                        these are recognised by what they are.
"""

import re

_BEEF = re.compile(r"\b(beef|calf|veal)\b", re.I)
_PORK = re.compile(r"\b(pork|ham|bacon)\b", re.I)
_SHELLFISH = re.compile(
    r"(prawn|shrimp|crab|lobster|crayfish|squid|cuttlefish|octopus|clam|mussel|oyster|snail)", re.I)
_FISH_OIL = re.compile(r"\bfish oil\b", re.I)
_LIVER = re.compile(r"\bliver\b", re.I)
_HIGH_MERCURY = re.compile(
    r"\b(sharks?|swordfish|marlin|tilefish|king mackerel|bigeye|orange roughy)\b", re.I)
_EGG = re.compile(r"\bmayonnaise\b", re.I)
_DAIRY = re.compile(r"^(butter|ghee, cow)\b|milk powder", re.I)
_NUTS = re.compile(
    r"(almond|cashew|chilgoza|pine nut|ground ?nut|peanut|pistachio|walnut|hazelnut)", re.I)
_GLUTEN = re.compile(r"\b(wheat|barley|rye|semolina|vermicelli|bread|biscuit|ruti)\b", re.I)
_ALCOHOL = re.compile(r"\b(toddy|beer|wine|whisky|rum|vodka|alcohol)\b", re.I)
_SOLID_FAT = re.compile(
    r"\b(butter|ghee|vanaspati|margarine|coconut oil|palm (kernel )?oil|lard|tallow)\b", re.I)

RESTRICTION_TAGS = frozenset({
    "contains_meat", "contains_beef", "contains_pork", "contains_fish",
    "contains_shellfish", "contains_egg", "contains_dairy", "contains_nuts",
    "contains_gluten", "liver", "high_mercury", "alcohol", "solid_fat",
})


def food_restriction_tags(name_en: str, food_group: str) -> tuple[str, ...]:
    """The restriction tags of one food-table row, in a stable order."""
    tags = []
    if food_group == "meat":
        tags.append("contains_meat")
        if _BEEF.search(name_en):
            tags.append("contains_beef")
        if _PORK.search(name_en):
            tags.append("contains_pork")
    if food_group == "fish":
        tags.append("contains_shellfish" if _SHELLFISH.search(name_en) else "contains_fish")
    elif _FISH_OIL.search(name_en):
        tags.append("contains_fish")
    if food_group == "egg" or _EGG.search(name_en):
        tags.append("contains_egg")
    if food_group == "dairy" or _DAIRY.search(name_en):
        tags.append("contains_dairy")
    if _NUTS.search(name_en):
        tags.append("contains_nuts")
    if food_group == "grain" and _GLUTEN.search(name_en):
        tags.append("contains_gluten")
    if _LIVER.search(name_en):
        tags.append("liver")
    if food_group == "fish" and _HIGH_MERCURY.search(name_en):
        tags.append("high_mercury")
    if _ALCOHOL.search(name_en):
        tags.append("alcohol")
    # the oil group only: butter beans and peanut butter are not cooking fats
    if food_group == "oil" and _SOLID_FAT.search(name_en):
        tags.append("solid_fat")
    return tuple(tags)
