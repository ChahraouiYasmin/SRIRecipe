from utils import load_all_recipes
from preprocess import build_text
from sentence_transformers import SentenceTransformer
import faiss
import pickle

# 1. Charger les recettes
recipes = load_all_recipes()
print(f"Loaded {len(recipes)} recipes.")

# 2. Préparer le texte pour chaque recette
texts = []
for r in recipes:
    text = build_text(r)
    texts.append(text.lower())  # lowercase suffit pour les embeddings

# 3. Charger un modèle de embeddings
model = SentenceTransformer('all-MiniLM-L6-v2')  # rapide et efficace
embeddings = model.encode(texts, convert_to_numpy=True)

# 4. Créer un index FAISS
dimension = embeddings.shape[1]
index = faiss.IndexFlatL2(dimension)  # distance L2
index.add(embeddings)
print(f"FAISS index created with {index.ntotal} vectors.")

# 5. Sauvegarder l'index et les recettes
faiss.write_index(index, "recipes_faiss.index")
with open("recipes.pkl", "wb") as f:
    pickle.dump(recipes, f)

print("Semantic index saved successfully!")