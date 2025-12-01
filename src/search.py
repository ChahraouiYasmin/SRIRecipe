from sentence_transformers import SentenceTransformer
import faiss
import pickle
from filter import filter_recipes  # import your filter function

# Load recipes
with open("recipes.pkl", "rb") as f:
    recipes = pickle.load(f)

# Load semantic embeddings index
index = faiss.read_index("recipes_faiss.index")
model = SentenceTransformer('all-MiniLM-L6-v2')

print("Semantic Recipe Search with Filters (type 'exit' to quit)\n")

while True:
    # Filtering inputs
    country_filter = input("Filter by country (or leave blank): ").strip()
    difficulty_filter = input("Filter by difficulty (easy, medium, hard, or leave blank): ").strip()
    meal_type_filter = input("Filter by meal type (dessert, breakfast, lunch, dinner, or leave blank): ").strip()

    # Apply filtering
    filtered_recipes = filter_recipes(
        recipes,
        country=country_filter if country_filter else None,
        difficulty=difficulty_filter if difficulty_filter else None,
        meal_type=meal_type_filter if meal_type_filter else None
    )

    if not filtered_recipes:
        print("No recipes match the filters.\n" + "-"*40 + "\n")
        continue

    # Ask for semantic query
    query = input("Enter your query (or leave blank to just use filters): ").strip()
    if query.lower() == "exit":
        print("Goodbye!")
        break

    if query:  # If the user entered a query, do semantic search
        filtered_texts = [r['title'] + " " + r['description'] for r in filtered_recipes]
        filtered_embeddings = model.encode(filtered_texts, convert_to_numpy=True)

        # Build temporary FAISS index for filtered recipes
        dimension = filtered_embeddings.shape[1]
        temp_index = faiss.IndexFlatL2(dimension)
        temp_index.add(filtered_embeddings)

        # Search top 5
        k = min(5, len(filtered_recipes))
        query_vec = model.encode([query], convert_to_numpy=True)
        distances, indices = temp_index.search(query_vec, k)

        print("\nTop recipes:")
        for i, idx in enumerate(indices[0]):
            r = filtered_recipes[idx]
            print(f"{i+1}. {r['title']} ({r['country']}, {r['difficulty']}, {r['meal_type']})")
    else:  # No query, just show filtered recipes
        print(f"\nRecipes matching filters ({len(filtered_recipes)} found):")
        for i, r in enumerate(filtered_recipes):
            print(f"{i+1}. {r['title']} ({r['country']}, {r['difficulty']}, {r['meal_type']})")

    print("\n" + "-"*40 + "\n")