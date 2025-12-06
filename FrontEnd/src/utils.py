import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))  # SRIRecipe/FrontEnd/src

def load_json(path):
    with open(path, 'r', encoding='utf8') as f:
        return json.load(f)

def load_all_recipes(folder=None):
    if folder is None:
        folder = os.path.join(BASE_DIR, "data", "recipes")
    files = [f for f in os.listdir(folder) if f.endswith(".json")]
    recipes = []
    for f in files:
        path = os.path.join(folder, f)
        recipes.append(load_json(path))
    return recipes
