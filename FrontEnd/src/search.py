from sentence_transformers import SentenceTransformer
import pickle
from filter import filter_recipes  # ta fonction de filtrage
import numpy as np

# Charger les recettes
with open("recipes.pkl", "rb") as f:
    recipes = pickle.load(f)

# Charger le modèle d'embeddings
model = SentenceTransformer('all-MiniLM-L6-v2')

print("Semantic Recipe Search with Filters (type 'exit' to quit)\n")

while True:
    # Inputs de filtrage
    country_filter = input("Filter by country (or leave blank): ").strip()
    difficulty_filter = input("Filter by difficulty (easy, medium, hard, or leave blank): ").strip()
    meal_type_filter = input("Filter by meal type (dessert, breakfast, lunch, dinner, or leave blank): ").strip()

    # Appliquer les filtres
    filtered_recipes = filter_recipes(
        recipes,
        country=country_filter if country_filter else None,
        difficulty=difficulty_filter if difficulty_filter else None,
        meal_type=meal_type_filter if meal_type_filter else None
    )

    if not filtered_recipes:
        print("No recipes match the filters.\n" + "-"*40 + "\n")
        continue

    # Input query
    query = input("Enter your query (or leave blank to just use filters): ").strip()
    if query.lower() == "exit":
        print("Goodbye!")
        break

    if query:  # Recherche sémantique
        # Construire le texte pour embeddings
        filtered_texts = [r['title'] + " " + r['description'] for r in filtered_recipes]
        filtered_embeddings = model.encode(filtered_texts, convert_to_numpy=True)
        query_vec = model.encode([query], convert_to_numpy=True)

        # Normalisation pour cosine similarity
        filtered_embeddings = filtered_embeddings / np.linalg.norm(filtered_embeddings, axis=1, keepdims=True)
        query_vec = query_vec / np.linalg.norm(query_vec, axis=1, keepdims=True)

        # Calcul de la similarité cosinus
        cos_sim = np.dot(filtered_embeddings, query_vec.T).squeeze()  # (num_recipes, )

        # Trier par score décroissant
        sorted_idx = np.argsort(-cos_sim)

        # Seuil pour considérer une recette pertinente
        THRESHOLD = 0.4

        results_count = 0
        print("\nTop relevant recipes:")

        for idx in sorted_idx:
            score = cos_sim[idx]
            if score < THRESHOLD:
                continue
            r = filtered_recipes[idx]
            results_count += 1
            print(f"{results_count}. {r['title']} ({r['country']}, {r['difficulty']}, {r['meal_type']}) - score: {score:.2f}")

        if results_count == 0:
            print("❌ No relevant recipes found.")

    else:  # Pas de query, juste filtres
        print(f"\nRecipes matching filters ({len(filtered_recipes)} found):")
        for i, r in enumerate(filtered_recipes):
            print(f"{i+1}. {r['title']} ({r['country']}, {r['difficulty']}, {r['meal_type']})")

    print("\n" + "-"*40 + "\n")
