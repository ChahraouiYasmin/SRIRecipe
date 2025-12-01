import os
import json

def load_json(path):
    with open(path, 'r', encoding='utf8') as f:
        return json.load(f)

def load_all_recipes(folder="../Data/recipes"):
    files = [f for f in os.listdir(folder) if f.endswith(".json")]
    recipes = []
    for f in files:
        path = os.path.join(folder, f)
        recipes.append(load_json(path))
    return recipes
