# app.py
from flask_cors import CORS
import os
from flask import Flask, request, jsonify, send_from_directory
from sentence_transformers import SentenceTransformer
import faiss
import pickle
from filter import filter_recipes
import numpy as np
from typing import List, Dict, Any, Optional

app = Flask(__name__)
CORS(app)

# Directory containing images
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
IMAGES_DIR = os.path.join(BASE_DIR, "data", "images")


@app.route("/images/<path:filename>")
def serve_image(filename):
    # Look for the file in a case-insensitive way
    for f in os.listdir(IMAGES_DIR):
        if f.lower() == filename.lower():
            return send_from_directory(IMAGES_DIR, f)
    # fallback
    return send_from_directory(IMAGES_DIR, "placeholder.png")

# Global variables for loaded data
recipes = None
index = None
model = None
recipe_embeddings = None  # Cache for all recipe embeddings


def load_models():
    """Load the recipes, FAISS index, and embedding model"""
    global recipes, index, model, recipe_embeddings

    print("Loading recipes and models...")

    # Load recipes
    with open("recipes.pkl", "rb") as f:
        recipes = pickle.load(f)

    # Load FAISS index
    index = faiss.read_index("recipes_faiss.index")

    # Load sentence transformer model
    model = SentenceTransformer('all-MiniLM-L6-v2')

    print(f"Loaded {len(recipes)} recipes successfully!")


# Load models when the app starts
load_models()


def build_recipe_response(recipe_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convert recipe objects to response-friendly format and expose image URLs"""
    response = []
    for recipe in recipe_list:
        # HANDLE IMAGES: recipe['image'] may be list or string or absent.
        raw_images = recipe.get("image")  # could be list or string or None
        image_urls = []

        if isinstance(raw_images, list):
            for p in raw_images:
                # extract basename (filename)
                filename = os.path.basename(p)
                # construct URL: http://host:port/images/{filename}
                image_urls.append(request.host_url.rstrip("/") + "/images/" + filename)
        elif isinstance(raw_images, str) and raw_images.strip():
            filename = os.path.basename(raw_images)
            image_urls.append(request.host_url.rstrip("/") + "/images/" + filename)

        # fallback placeholder if empty
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
            # expose the first image as `image` for backwards compatibility
            "image": image_urls[0] if image_urls else None,
            # expose all images as `images`
            "images": image_urls,
        }
        response.append(recipe_data)
    return response



@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "recipes_loaded": len(recipes) if recipes else 0,
        "index_loaded": index.ntotal if index else 0
    })


@app.route('/api/recipes/search', methods=['POST'])
def search_recipes():
    """Search recipes with semantic search and filters"""
    try:
        data = request.json

        # Extract filters
        country_filter = data.get('country', '').strip() or None
        difficulty_filter = data.get('difficulty', '').strip() or None
        meal_type_filter = data.get('meal_type', '').strip() or None
        query = data.get('query', '').strip()

        # Apply filters
        filtered_recipes = filter_recipes(
            recipes,
            country=country_filter,
            difficulty=difficulty_filter,
            meal_type=meal_type_filter
        )

        # --- CASE 1: No filters, no query → show all recipes (limit 50) ---
        if not query and not any([country_filter, difficulty_filter, meal_type_filter]):
            results = build_recipe_response(recipes[:50])

        # --- CASE 2: Filters applied, no query → show all filtered recipes ---
        elif not query and any([country_filter, difficulty_filter, meal_type_filter]):
            results = build_recipe_response(filtered_recipes)

        # --- CASE 3: Search query provided → semantic search ---
        else:
            if not filtered_recipes:
                return jsonify({
                    "message": "No recipes match the filters",
                    "count": 0,
                    "recipes": []
                })

            # Encode filtered recipes
            filtered_texts = [r['title'] + " " + r['description'] for r in filtered_recipes]
            filtered_embeddings = model.encode(filtered_texts, convert_to_numpy=True)

            # Build temporary FAISS index
            dimension = filtered_embeddings.shape[1]
            temp_index = faiss.IndexFlatL2(dimension)
            temp_index.add(filtered_embeddings)

            # Perform semantic search
            k = min(5, len(filtered_recipes))  # max 5 results
            query_vec = model.encode([query], convert_to_numpy=True)
            distances, indices = temp_index.search(query_vec, k)

            results = []
            for i, idx in enumerate(indices[0]):
                recipe = filtered_recipes[idx]
                recipe_data = build_recipe_response([recipe])[0]
                recipe_data["similarity_score"] = float(1 / (1 + distances[0][i]))
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
    """Get available filter values (countries, difficulties, meal types)"""
    try:
        countries = set()
        difficulties = set()
        meal_types = set()
        categories = set()

        for recipe in recipes:
            if recipe.get("country"):
                countries.add(recipe["country"])
            if recipe.get("difficulty"):
                difficulties.add(recipe["difficulty"])
            if recipe.get("meal_type"):
                meal_types.add(recipe["meal_type"])
            if recipe.get("category"):
                categories.add(recipe["category"])

        return jsonify({
            "countries": sorted(list(countries)),
            "difficulties": sorted(list(difficulties)),
            "meal_types": sorted(list(meal_types)),
            "categories": sorted(list(categories))
        })

    except Exception as e:
        return jsonify({
            "error": str(e),
            "message": "An error occurred while fetching filters"
        }), 500


@app.route('/api/recipes/<recipe_id>', methods=['GET'])
def get_recipe_by_id(recipe_id):
    """Get a specific recipe by ID"""
    try:
        # Try to find by id field first
        recipe = next((r for r in recipes if r.get('id') == recipe_id), None)

        # If not found, try to find by title (as fallback)
        if not recipe:
            recipe = next((r for r in recipes if r.get('title', '').lower() == recipe_id.lower()), None)

        if recipe:
            return jsonify({
                "message": "Recipe found",
                "recipe": build_recipe_response([recipe])[0]
            })
        else:
            return jsonify({
                "message": "Recipe not found",
                "recipe": None
            }), 404

    except Exception as e:
        return jsonify({
            "error": str(e),
            "message": "An error occurred while fetching the recipe"
        }), 500


@app.route('/api/recipes/similar', methods=['POST'])
def find_similar_recipes():
    """Find recipes similar to a given recipe or text"""
    try:
        data = request.json
        recipe_id = data.get('recipe_id')
        text = data.get('text')
        top_k = data.get('top_k', 5)

        if not recipe_id and not text:
            return jsonify({
                "error": "Either recipe_id or text must be provided"
            }), 400

        query_vec = None

        if recipe_id:
            # Find the recipe
            recipe = next((r for r in recipes if r.get('id') == recipe_id), None)
            if not recipe:
                return jsonify({
                    "message": "Recipe not found",
                    "recipe": None
                }), 404

            # Create embedding from recipe text
            recipe_text = recipe['title'] + " " + recipe['description']
            query_vec = model.encode([recipe_text], convert_to_numpy=True)
        else:
            # Create embedding from provided text
            query_vec = model.encode([text], convert_to_numpy=True)

        # Search in the main index
        k = min(top_k, len(recipes))
        distances, indices = index.search(query_vec, k + 1)  # +1 to account for the query recipe itself

        # Prepare results
        results = []
        for i, idx in enumerate(indices[0]):
            if idx < len(recipes):
                recipe = recipes[idx]

                # Skip if this is the query recipe itself
                if recipe_id and recipe.get('id') == recipe_id:
                    continue

                recipe_data = build_recipe_response([recipe])[0]
                recipe_data["similarity_score"] = float(1 / (1 + distances[0][i]))
                results.append(recipe_data)

                if len(results) >= top_k:
                    break

        return jsonify({
            "message": "Similar recipes found",
            "count": len(results),
            "recipes": results
        })

    except Exception as e:
        return jsonify({
            "error": str(e),
            "message": "An error occurred while finding similar recipes"
        }), 500


@app.route('/api/recipes/random', methods=['GET'])
def get_random_recipes():
    """Get random recipes"""
    try:
        count = request.args.get('count', 5, type=int)
        count = min(count, 20)  # Limit to 20

        import random
        random_recipes = random.sample(recipes, min(count, len(recipes)))

        return jsonify({
            "message": f"Random {len(random_recipes)} recipes",
            "count": len(random_recipes),
            "recipes": build_recipe_response(random_recipes)
        })

    except Exception as e:
        return jsonify({
            "error": str(e),
            "message": "An error occurred while fetching random recipes"
        }), 500


@app.route('/api/recipes/all', methods=['GET'])
def get_all_recipes():
    """Get all recipes (paginated)"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)

        # Validate pagination parameters
        page = max(1, page)
        page_size = min(max(1, page_size), 100)  # Limit to 100 per page

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

    except Exception as e:
        return jsonify({
            "error": str(e),
            "message": "An error occurred while fetching recipes"
        }), 500


if __name__ == '__main__':
    print("Starting Recipe Search API...")
    print(f"Total recipes loaded: {len(recipes)}")
    app.run(debug=True, host='0.0.0.0', port=5000)