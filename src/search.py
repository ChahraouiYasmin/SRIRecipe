from sentence_transformers import SentenceTransformer
import faiss
import pickle

# Charger index et recettes
index = faiss.read_index("recipes_faiss.index")
with open("recipes.pkl", "rb") as f:
    recipes = pickle.load(f)

# Charger modèle
model = SentenceTransformer('all-MiniLM-L6-v2')

# Requête
query = "fast recipe"
query_vec = model.encode([query], convert_to_numpy=True)

# Recherche top 5
k = 5
distances, indices = index.search(query_vec, k)

print("Top recipes:")
for i in indices[0]:
    print(recipes[i]['title'])