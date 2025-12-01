from sentence_transformers import SentenceTransformer
import faiss
import pickle

# Charger index et recettes
index = faiss.read_index("recipes_faiss.index")
with open("recipes.pkl", "rb") as f:
    recipes = pickle.load(f)

# Charger modèle
model = SentenceTransformer('all-MiniLM-L6-v2')

print("Semantic Recipe Search (type 'exit' to quit)\n")

while True:
    # Requête utilisateur
    query = input("Enter your query: ")
    if query.lower() == "exit":
        print("Goodbye!")
        break

    # Calculer vecteur
    query_vec = model.encode([query], convert_to_numpy=True)

    # Recherche top 5
    k = 5
    distances, indices = index.search(query_vec, k)

    print("\nTop recipes:")
    for i, idx in enumerate(indices[0]):
        print(f"{i+1}. {recipes[idx]['title']}")
    print("\n" + "-"*40 + "\n")