def filter_recipes(recipes, country=None, difficulty=None, meal_type=None):
    filtered = []
    for r in recipes:
        if country and r.get("country").lower() != country.lower():
            continue
        if difficulty and r.get("difficulty").lower() != difficulty.lower():
            continue
        if meal_type and r.get("meal_type").lower() != meal_type.lower():
            continue
        filtered.append(r)
    return filtered