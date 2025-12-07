# app.py
from flask_cors import CORS
import os
from flask import Flask, request, jsonify, send_from_directory
from sentence_transformers import SentenceTransformer
import pickle
from filter import filter_recipes
import numpy as np
from typing import List, Dict, Any

app = Flask(__name__)
CORS(app)

# Directory containing images
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(BASE_DIR, "data", "images")


@app.route("/images/<path:filename>")
def serve_image(filename):
    """Serve images in a case-insensitive way"""
    for f in os.listdir(IMAGES_DIR):
        if f.lower() == filename.lower():
            return send_from_directory(IMAGES_DIR, f)
    # fallback placeholder
    return send_from_directory(IMAGES_DIR, "placeholder.png")


# Global variables
recipes = None
model = None


def load_models():
    """Load recipes and sentence transformer model"""
    global recipes, model
    print("Loading recipes and model...")
    with open("recipes.pkl", "rb") as f:
        recipes = pickle.load(f)

    model = SentenceTransformer('all-MiniLM-L6-v2')
    print(f"Loaded {len(recipes)} recipes successfully!")


# Load on startup
load_models()


def build_recipe_response(recipe_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convert recipes to API-friendly format, include image URLs"""
    response = []
    for recipe in recipe_list:
        raw_images = recipe.get("image")
        image_urls = []

        if isinstance(raw_images, list):
            for p in raw_images:
                filename = os.path.basename(p)
                image_urls.append(request.host_url.rstrip("/") + "/images/" + filename)
        elif isinstance(raw_images, str) and raw_images.strip():
            filename = os.path.basename(raw_images)
            image_urls.append(request.host_url.rstrip("/") + "/images/" + filename)

        if not image_urls:
            image_urls = [request.host_url.rstrip("/") + "/images/placeholder.png"]

        recipe_data = {
            "id": recipe.get("id", ""),
            "title": recipe.get("title", ""),
            "description": recipe.get("description", ""),
            "country": recipe.get("country", ""),
            "difficulty": recipe.get("difficulty", ""),
            "meal_type": recipe.get("meal_type", ""),
            "servings": recipe.get("servings", ""),
            "cooking_time": recipe.get("cooking_time", ""),
            "preparation_time": recipe.get("preparation_time", ""),
            "ingredients": recipe.get("ingredients", []),
            "instructions": recipe.get("instructions", []),
            "tags": recipe.get("tags", []),
            "category": recipe.get("category", ""),
            "cooking_method": recipe.get("cooking_method", ""),
            "image": image_urls[0] if image_urls else None,
            "images": image_urls,
        }
        response.append(recipe_data)
    return response


@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        "status": "healthy",
        "recipes_loaded": len(recipes) if recipes else 0
    })


@app.route('/api/recipes/search', methods=['POST'])
def search_recipes():
    """Search recipes using filters and semantic similarity"""
    try:
        data = request.json or {}
        country_filter = data.get('country', '').strip() or None
        difficulty_filter = data.get('difficulty', '').strip() or None
        meal_type_filter = data.get('meal_type', '').strip() or None
        query = data.get('query', '').strip()

        filtered_recipes = filter_recipes(
            recipes,
            country=country_filter,
            difficulty=difficulty_filter,
            meal_type=meal_type_filter
        )

        # Case: no query
        if not query:
            results = build_recipe_response(filtered_recipes if any([country_filter, difficulty_filter, meal_type_filter]) else recipes[:50])
            return jsonify({
                "message": "Search completed successfully",
                "count": len(results),
                "filters": {
                    "country": country_filter,
                    "difficulty": difficulty_filter,
                    "meal_type": meal_type_filter
                },
                "query": query,
                "recipes": results
            })

        # Case: semantic search
        if not filtered_recipes:
            return jsonify({
                "message": "No recipes match the filters",
                "count": 0,
                "recipes": []
            })

        filtered_texts = [r['title'] + " " + r['description'] for r in filtered_recipes]
        filtered_embeddings = model.encode(filtered_texts, convert_to_numpy=True)
        query_vec = model.encode([query], convert_to_numpy=True)

        # Normalize for cosine similarity
        filtered_embeddings /= np.linalg.norm(filtered_embeddings, axis=1, keepdims=True)
        query_vec /= np.linalg.norm(query_vec, axis=1, keepdims=True)

        scores = np.dot(filtered_embeddings, query_vec.T).squeeze()
        sorted_idx = np.argsort(-scores)
        THRESHOLD = 0.4

        results = []
        for idx in sorted_idx:
            score = scores[idx]
            if score < THRESHOLD:
                continue
            r = filtered_recipes[idx]
            recipe_data = build_recipe_response([r])[0]
            recipe_data["similarity_score"] = round(float(score), 2)
            results.append(recipe_data)

        return jsonify({
            "message": "Search completed successfully",
            "count": len(results),
            "filters": {
                "country": country_filter,
                "difficulty": difficulty_filter,
                "meal_type": meal_type_filter
            },
            "query": query,
            "recipes": results
        })

    except Exception as e:
        return jsonify({
            "error": str(e),
            "message": "An error occurred during search"
        }), 500


@app.route('/api/recipes/filters', methods=['GET'])
def get_available_filters():
    countries = set()
    difficulties = set()
    meal_types = set()
    categories = set()
    for r in recipes:
        if r.get("country"): countries.add(r["country"])
        if r.get("difficulty"): difficulties.add(r["difficulty"])
        if r.get("meal_type"): meal_types.add(r["meal_type"])
        if r.get("category"): categories.add(r["category"])
    return jsonify({
        "countries": sorted(countries),
        "difficulties": sorted(difficulties),
        "meal_types": sorted(meal_types),
        "categories": sorted(categories)
    })


@app.route('/api/recipes/<recipe_id>', methods=['GET'])
def get_recipe_by_id(recipe_id):
    recipe = next((r for r in recipes if r.get('id') == recipe_id), None)
    if not recipe:
        recipe = next((r for r in recipes if r.get('title', '').lower() == recipe_id.lower()), None)
    if recipe:
        return jsonify({"message": "Recipe found", "recipe": build_recipe_response([recipe])[0]})
    return jsonify({"message": "Recipe not found", "recipe": None}), 404


@app.route('/api/recipes/similar', methods=['POST'])
def find_similar_recipes():
    try:
        data = request.json or {}
        recipe_id = data.get('recipe_id')
        text = data.get('text')
        top_k = data.get('top_k', 5)

        if not recipe_id and not text:
            return jsonify({"error": "Either recipe_id or text must be provided"}), 400

        if recipe_id:
            recipe = next((r for r in recipes if r.get('id') == recipe_id), None)
            if not recipe:
                return jsonify({"message": "Recipe not found", "recipe": None}), 404
            query_vec = model.encode([recipe['title'] + " " + recipe['description']], convert_to_numpy=True)
        else:
            query_vec = model.encode([text], convert_to_numpy=True)

        # Semantic search over all recipes
        all_texts = [r['title'] + " " + r['description'] for r in recipes]
        all_embeddings = model.encode(all_texts, convert_to_numpy=True)
        all_embeddings /= np.linalg.norm(all_embeddings, axis=1, keepdims=True)
        query_vec /= np.linalg.norm(query_vec, axis=1, keepdims=True)

        scores = np.dot(all_embeddings, query_vec.T).squeeze()
        sorted_idx = np.argsort(-scores)

        results = []
        for idx in sorted_idx:
            if recipe_id and recipes[idx]['id'] == recipe_id:
                continue
            results.append(build_recipe_response([recipes[idx]])[0])
            if len(results) >= top_k:
                break

        return jsonify({"message": "Similar recipes found", "count": len(results), "recipes": results})

    except Exception as e:
        return jsonify({"error": str(e), "message": "An error occurred while finding similar recipes"}), 500


@app.route('/api/recipes/random', methods=['GET'])
def get_random_recipes():
    import random
    count = min(request.args.get('count', 5, type=int), 20)
    random_recipes = random.sample(recipes, min(count, len(recipes)))
    return jsonify({"message": f"Random {len(random_recipes)} recipes",
                    "count": len(random_recipes),
                    "recipes": build_recipe_response(random_recipes)})


@app.route('/api/recipes/all', methods=['GET'])
def get_all_recipes():
    page = max(request.args.get('page', 1, type=int), 1)
    page_size = min(max(request.args.get('page_size', 20, type=int), 1), 100)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_recipes = recipes[start_idx:end_idx]
    return jsonify({
        "message": f"Recipes page {page}",
        "page": page,
        "page_size": page_size,
        "total_recipes": len(recipes),
        "total_pages": (len(recipes) + page_size - 1) // page_size,
        "recipes": build_recipe_response(paginated_recipes)
    })


if __name__ == '__main__':
    print("Starting Recipe Search API...")
    print(f"Total recipes loaded: {len(recipes)}")
    app.run(debug=True, host='0.0.0.0', port=5000)
