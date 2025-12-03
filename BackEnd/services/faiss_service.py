import numpy as np
import faiss
from typing import List, Dict, Any, Optional, Tuple
import pickle
import os
from utils.logger import logger
from sentence_transformers import SentenceTransformer

class FaissService:
    """Service FAISS pour recherche sémantique ultra-rapide"""
    
    def __init__(self, model_name: str = 'paraphrase-MiniLM-L3-v2'):
        """
        Initialise le service FAISS
        
        Args:
            model_name: Modèle SentenceTransformer léger
        """
        self.model_name = model_name
        self.model = None
        self.index = None
        self.embeddings = None
        self.recipes = []
        self.recipe_ids = []
        self.id_to_index = {}
        self.index_to_id = {}
        
        # Charger le modèle
        self._load_model()
        
        # Initialiser index FAISS
        self.dimension = 384  # Dimension du modèle MiniLM
        self._init_faiss_index()
        
        logger.info(f"FaissService initialisé avec modèle {model_name}")
    
    def _load_model(self):
        """Charge le modèle SentenceTransformer"""
        try:
            logger.info(f"Chargement du modèle: {self.model_name}")
            self.model = SentenceTransformer(self.model_name)
            
            # Tester
            test_embedding = self.model.encode(["test"])
            self.dimension = test_embedding.shape[1]
            
            logger.info(f"✅ Modèle chargé, dimension: {self.dimension}")
            
        except Exception as e:
            logger.error(f"❌ Erreur chargement modèle: {str(e)}")
            raise
    
    def _init_faiss_index(self):
        """Initialise l'index FAISS"""
        # Index plat L2 (distance euclidienne) - simple et efficace
        self.index = faiss.IndexFlatL2(self.dimension)
        logger.info(f"✅ Index FAISS initialisé (dim={self.dimension})")
    
    def prepare_recipe_text(self, recipe: Dict[str, Any]) -> str:
        """Prépare le texte d'une recette pour l'embedding"""
        text_parts = []
        
        # Titre (poids fort)
        title = recipe.get('title', '')
        if title:
            text_parts.extend([title] * 2)  # Double poids
        
        # Description
        description = recipe.get('description', '')
        if description:
            text_parts.append(description)
        
        # Ingrédients principaux
        ingredients = recipe.get('ingredients', [])
        if ingredients:
            ingredient_names = [ing.get('item', '') for ing in ingredients[:8]]
            text_parts.append(', '.join(ingredient_names))
        
        # Tags
        tags = recipe.get('tags', [])
        if tags:
            text_parts.append(', '.join(tags))
        
        # Catégorie et pays
        category = recipe.get('category', '')
        country = recipe.get('country', '')
        if category:
            text_parts.append(category)
        if country:
            text_parts.append(country)
        
        return '. '.join(text_parts)
    
    def add_recipes(self, recipes: List[Dict[str, Any]]):
        """Ajoute des recettes et génère leurs embeddings"""
        if not recipes:
            logger.warning("Aucune recette à ajouter")
            return
        
        logger.info(f"Ajout de {len(recipes)} recettes à FAISS...")
        
        self.recipes = recipes
        self.recipe_ids = [recipe.get('id', f'recipe_{i}') for i, recipe in enumerate(recipes)]
        
        # Créer mapping
        for idx, recipe_id in enumerate(self.recipe_ids):
            self.id_to_index[recipe_id] = idx
            self.index_to_id[idx] = recipe_id
        
        # Préparer les textes
        texts = [self.prepare_recipe_text(recipe) for recipe in recipes]
        
        # Générer les embeddings par batch
        logger.info("Génération des embeddings...")
        embeddings = []
        batch_size = 16
        
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i + batch_size]
            batch_embeddings = self.model.encode(batch_texts, show_progress_bar=False)
            embeddings.append(batch_embeddings)
            
            if (i // batch_size) % 5 == 0:
                logger.info(f"  Traitées: {min(i + batch_size, len(texts))}/{len(texts)}")
        
        # Concaténer
        self.embeddings = np.vstack(embeddings).astype('float32')
        
        # Ajouter à l'index FAISS
        self.index.add(self.embeddings)
        
        logger.info(f"✅ {len(recipes)} recettes indexées dans FAISS")
        logger.info(f"   - Embeddings shape: {self.embeddings.shape}")
        logger.info(f"   - Index size: {self.index.ntotal}")
    
    def semantic_search(self, query: str, k: int = 10) -> List[Dict[str, Any]]:
        """
        Recherche sémantique avec FAISS
        
        Args:
            query: Requête textuelle
            k: Nombre de résultats
        
        Returns:
            Liste de résultats avec scores
        """
        if self.index is None or self.index.ntotal == 0:
            logger.warning("Index FAISS vide")
            return []
        
        # Générer embedding de la requête
        query_embedding = self.model.encode([query]).astype('float32')
        
        # Recherche FAISS
        distances, indices = self.index.search(query_embedding, min(k, self.index.ntotal))
        
        # Formater résultats
        results = []
        for i, (distance, idx) in enumerate(zip(distances[0], indices[0])):
            if idx < 0 or idx >= len(self.recipes):  # Index invalide
                continue
            
            recipe_id = self.index_to_id.get(idx)
            if not recipe_id:
                continue
            
            # Convertir distance en similarité (0-1)
            # distance L2 → similarité (plus petite distance = plus similaire)
            similarity = 1.0 / (1.0 + distance)  # Transformation simple
            
            recipe = self.recipes[idx].copy()
            recipe['semantic_score'] = float(similarity)
            recipe['semantic_distance'] = float(distance)
            recipe['semantic_rank'] = i + 1
            
            results.append(recipe)
            
            if len(results) >= k:
                break
        
        logger.debug(f"Recherche sémantique: '{query}' -> {len(results)} résultats")
        return results
    
    def find_similar_recipes(self, recipe_id: str, k: int = 5) -> List[Dict[str, Any]]:
        """Trouve des recettes similaires à une recette donnée"""
        if recipe_id not in self.id_to_index:
            logger.warning(f"Recette {recipe_id} non trouvée")
            return []
        
        idx = self.id_to_index[recipe_id]
        
        # Récupérer l'embedding de la recette
        recipe_embedding = self.embeddings[idx:idx+1].astype('float32')
        
        # Recherche (exclure la recette elle-même)
        k_search = k + 1  # Chercher un de plus pour exclure soi-même
        distances, indices = self.index.search(recipe_embedding, min(k_search, self.index.ntotal))
        
        # Formater résultats (exclure la première qui est la recette elle-même)
        results = []
        for i, (distance, idx_result) in enumerate(zip(distances[0], indices[0])):
            if i == 0:  # Sauter la première (recette elle-même)
                continue
            
            if idx_result < 0 or idx_result >= len(self.recipes):
                continue
            
            result_id = self.index_to_id.get(idx_result)
            if not result_id or result_id == recipe_id:
                continue
            
            similarity = 1.0 / (1.0 + distance)
            
            recipe = self.recipes[idx_result].copy()
            recipe['similarity_score'] = float(similarity)
            recipe['similarity_distance'] = float(distance)
            
            results.append(recipe)
            
            if len(results) >= k:
                break
        
        return results
    
    def hybrid_search(self, query: str, filters: Optional[Dict] = None, 
                     k: int = 20) -> List[Dict[str, Any]]:
        """
        Recherche hybride : FAISS sémantique + BM25 textuel
        
        Note: BM25 sera implémenté séparément
        """
        # Pour l'instant, juste recherche sémantique
        return self.semantic_search(query, k)
    
    def save(self, filepath: str):
        """Sauvegarde l'index FAISS"""
        try:
            # Sauvegarder FAISS index
            faiss.write_index(self.index, filepath + '.faiss')
            
            # Sauvegarder les métadonnées
            metadata = {
                'recipes': self.recipes,
                'recipe_ids': self.recipe_ids,
                'embeddings': self.embeddings,
                'id_to_index': self.id_to_index,
                'index_to_id': self.index_to_id,
                'model_name': self.model_name,
                'dimension': self.dimension
            }
            
            with open(filepath + '.meta', 'wb') as f:
                pickle.dump(metadata, f)
            
            logger.info(f"✅ Index FAISS sauvegardé: {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur sauvegarde FAISS: {str(e)}")
            return False
    
    def load(self, filepath: str):
        """Charge l'index FAISS"""
        try:
            # Charger FAISS index
            self.index = faiss.read_index(filepath + '.faiss')
            
            # Charger métadonnées
            with open(filepath + '.meta', 'rb') as f:
                metadata = pickle.load(f)
            
            self.recipes = metadata['recipes']
            self.recipe_ids = metadata['recipe_ids']
            self.embeddings = metadata['embeddings']
            self.id_to_index = metadata['id_to_index']
            self.index_to_id = metadata['index_to_id']
            self.model_name = metadata['model_name']
            self.dimension = metadata['dimension']
            
            # Recharger le modèle
            self.model = SentenceTransformer(self.model_name)
            
            logger.info(f"✅ Index FAISS chargé: {filepath}")
            logger.info(f"   - Recettes: {len(self.recipes)}")
            logger.info(f"   - Dimension: {self.dimension}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erreur chargement FAISS: {str(e)}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne des statistiques"""
        return {
            'total_recipes': len(self.recipes) if self.recipes else 0,
            'faiss_index_size': self.index.ntotal if self.index else 0,
            'embedding_dimension': self.dimension,
            'model_name': self.model_name
        }