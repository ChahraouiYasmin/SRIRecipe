import json
import pickle
from collections import defaultdict
from typing import Dict, List, Any, Set, Tuple
import os
from pathlib import Path
from utils.logger import logger
import nltk
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

# Télécharger ressources NLTK
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('wordnet')

class InvertedIndex:
    """Index inversé pour recherche textuelle rapide"""
    
    def __init__(self):
        self.index = defaultdict(set)  # {terme: {recipe_ids}}
        self.recipe_terms = {}         # {recipe_id: [termes]}
        self.total_recipes = 0
        
        # NLTK pour prétraitement
        self.stop_words = set(stopwords.words('english'))
        self.lemmatizer = WordNetLemmatizer()
        
        # Stop words personnalisés pour recettes
        self.recipe_stop_words = {
            'recipe', 'make', 'prepare', 'cook', 'serve',
            'ingredient', 'step', 'minute', 'hour', 'cup',
            'tablespoon', 'teaspoon', 'gram', 'ounce', 'optional'
        }
        
        # Dictionnaire de synonymes culinaires basiques
        self.culinary_synonyms = {
            'beef': ['beef', 'steak', 'meat'],
            'chicken': ['chicken', 'poultry'],
            'pork': ['pork', 'bacon', 'ham'],
            'onion': ['onion', 'shallot'],
            'garlic': ['garlic', 'clove'],
            'tomato': ['tomato', 'tomatoes'],
            'cheese': ['cheese', 'cheeses'],
            'butter': ['butter', 'butters'],
            'oil': ['oil', 'oils', 'olive oil'],
            'salt': ['salt', 'salty'],
            'pepper': ['pepper', 'black pepper'],
            'sugar': ['sugar', 'sweet'],
            'egg': ['egg', 'eggs'],
            'rice': ['rice', 'rices'],
            'pasta': ['pasta', 'noodle', 'spaghetti']
        }
    
    def preprocess_text(self, text: str) -> List[str]:
        """Tokenize, nettoie et lemmatise un texte"""
        if not text:
            return []
        
        # Tokenization
        tokens = word_tokenize(text.lower())
        
        # Nettoyage et lemmatisation
        processed = []
        for token in tokens:
            # Supprimer ponctuation
            token = ''.join(char for char in token if char.isalnum())
            if not token or len(token) < 2:
                continue
            
            # Supprimer stop words
            if token in self.stop_words or token in self.recipe_stop_words:
                continue
            
            # Lemmatisation
            lemma = self.lemmatizer.lemmatize(token)
            processed.append(lemma)
        
        return processed
    
    def add_recipe(self, recipe_id: str, recipe_data: Dict[str, Any]):
        """Ajoute une recette à l'index inversé"""
        self.total_recipes += 1
        recipe_terms = set()
        
        # 1. Indexer le titre (poids fort)
        title = recipe_data.get('title', '')
        title_terms = self.preprocess_text(title)
        for term in title_terms:
            self.index[term].add(recipe_id)
            recipe_terms.add(term)
        
        # 2. Indexer la description (poids moyen)
        description = recipe_data.get('description', '')
        desc_terms = self.preprocess_text(description)
        for term in desc_terms:
            self.index[term].add(recipe_id)
            recipe_terms.add(term)
        
        # 3. Indexer les ingrédients (poids fort)
        ingredients_text = ' '.join([
            f"{ing.get('item', '')} {ing.get('quantity', '')}" 
            for ing in recipe_data.get('ingredients', [])
        ])
        ing_terms = self.preprocess_text(ingredients_text)
        for term in ing_terms:
            self.index[term].add(recipe_id)
            recipe_terms.add(term)
        
        # 4. Indexer les tags (poids fort)
        tags_text = ' '.join(recipe_data.get('tags', []))
        tag_terms = self.preprocess_text(tags_text)
        for term in tag_terms:
            self.index[term].add(recipe_id)
            recipe_terms.add(term)
        
        # 5. Indexer les instructions (poids faible)
        instructions_text = ' '.join(recipe_data.get('instructions', []))
        instr_terms = self.preprocess_text(instructions_text)
        for term in instr_terms:
            self.index[term].add(recipe_id)
            recipe_terms.add(term)
        
        # Stocker les termes de cette recette
        self.recipe_terms[recipe_id] = list(recipe_terms)
    
    def search(self, query: str, top_k: int = 20) -> List[Tuple[str, float]]:
        """Recherche simple dans l'index inversé"""
        query_terms = self.preprocess_text(query)
        
        if not query_terms:
            return []
        
        # Calcul des scores (simple fréquence)
        scores = defaultdict(float)
        for term in query_terms:
            if term in self.index:
                # Inverse Document Frequency simplifié
                idf = 1.0 / (len(self.index[term]) + 1)
                for recipe_id in self.index[term]:
                    scores[recipe_id] += idf
        
        # Trier par score
        sorted_results = sorted(scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_results[:top_k]
    
    def get_suggestions(self, prefix: str, limit: int = 10) -> List[str]:
        """Retourne des suggestions pour l'auto-complétion"""
        suggestions = []
        prefix = prefix.lower()
        
        for term in self.index.keys():
            if term.startswith(prefix):
                # Score basé sur la fréquence du terme
                frequency = len(self.index[term])
                suggestions.append((term, frequency))
        
        # Trier par fréquence
        suggestions.sort(key=lambda x: x[1], reverse=True)
        return [term for term, _ in suggestions[:limit]]
    
    def expand_query(self, query: str) -> List[str]:
        """Étend la requête avec des synonymes culinaires"""
        query_terms = self.preprocess_text(query)
        expanded_terms = set(query_terms)
        
        for term in query_terms:
            if term in self.culinary_synonyms:
                expanded_terms.update(self.culinary_synonyms[term])
        
        return list(expanded_terms)
    
    def save(self, filepath: str):
        """Sauvegarde l'index sur disque"""
        try:
            data = {
                'index': {k: list(v) for k, v in self.index.items()},
                'recipe_terms': self.recipe_terms,
                'total_recipes': self.total_recipes
            }
            
            with open(filepath, 'wb') as f:
                pickle.dump(data, f)
            
            logger.info(f"✅ Inverted index saved to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error saving index: {str(e)}")
            return False
    
    def load(self, filepath: str):
        """Charge l'index depuis le disque"""
        try:
            with open(filepath, 'rb') as f:
                data = pickle.load(f)
            
            self.index = defaultdict(set)
            for k, v in data['index'].items():
                self.index[k] = set(v)
            
            self.recipe_terms = data['recipe_terms']
            self.total_recipes = data['total_recipes']
            
            logger.info(f"✅ Inverted index loaded from {filepath}")
            logger.info(f"   - Terms: {len(self.index)}")
            logger.info(f"   - Recipes: {self.total_recipes}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error loading index: {str(e)}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne des statistiques sur l'index"""
        return {
            'total_terms': len(self.index),
            'total_recipes': self.total_recipes,
            'avg_terms_per_recipe': sum(len(terms) for terms in self.recipe_terms.values()) / max(1, self.total_recipes),
            'top_10_terms': sorted(
                [(term, len(recipes)) for term, recipes in self.index.items()],
                key=lambda x: x[1],
                reverse=True
            )[:10]
        }