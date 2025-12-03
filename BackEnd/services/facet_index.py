from typing import Dict, List, Set, Any
from collections import defaultdict
from utils.logger import logger
import pickle
import os

class FacetIndex:
    """Index pour le filtrage rapide par facettes"""
    
    def __init__(self):
        # Index inversés pour chaque type de facette
        self.country_index = defaultdict(set)      # {pays: {recipe_ids}}
        self.category_index = defaultdict(set)     # {catégorie: {recipe_ids}}
        self.difficulty_index = defaultdict(set)   # {difficulté: {recipe_ids}}
        self.meal_type_index = defaultdict(set)    # {meal_type: {recipe_ids}}
        self.cooking_method_index = defaultdict(set) # {méthode: {recipe_ids}}
        self.ingredient_index = defaultdict(set)   # {ingrédient: {recipe_ids}}
        
        # Valeurs uniques pour chaque facette
        self.all_countries = set()
        self.all_categories = set()
        self.all_difficulties = set()
        self.all_meal_types = set()
        self.all_cooking_methods = set()
        self.all_ingredients = set()
        
        # Index des durées
        self.duration_index = {
            'quick': set(),     # < 30 min
            'medium': set(),    # 30-60 min
            'long': set()       # > 60 min
        }
    
    def add_recipe(self, recipe_id: str, recipe_data: Dict[str, Any]):
        """Ajoute une recette à tous les index de facettes"""
        
        # Index par pays
        country = recipe_data.get('country', 'Unknown')
        self.country_index[country].add(recipe_id)
        self.all_countries.add(country)
        
        # Index par catégorie
        category = recipe_data.get('category', 'Unknown')
        self.category_index[category].add(recipe_id)
        self.all_categories.add(category)
        
        # Index par difficulté
        difficulty = recipe_data.get('difficulty', 'Unknown')
        self.difficulty_index[difficulty].add(recipe_id)
        self.all_difficulties.add(difficulty)
        
        # Index par type de repas
        meal_type = recipe_data.get('meal_type', 'Unknown')
        self.meal_type_index[meal_type].add(recipe_id)
        self.all_meal_types.add(meal_type)
        
        # Index par méthode de cuisson
        cooking_method = recipe_data.get('cooking_method', 'Unknown')
        self.cooking_method_index[cooking_method].add(recipe_id)
        self.all_cooking_methods.add(cooking_method)
        
        # Index par ingrédients
        for ingredient in recipe_data.get('ingredients', []):
            item = ingredient.get('item', '').strip().lower()
            if item and len(item) > 2:  # Ignorer les items trop courts
                self.ingredient_index[item].add(recipe_id)
                self.all_ingredients.add(item)
        
        # Index par durée
        total_time = recipe_data.get('duration', {}).get('total', 0)
        if total_time < 30:
            self.duration_index['quick'].add(recipe_id)
        elif total_time <= 60:
            self.duration_index['medium'].add(recipe_id)
        else:
            self.duration_index['long'].add(recipe_id)
    
    def filter_recipes(self, filters: Dict[str, Any]) -> Set[str]:
        """
        Filtre les recettes selon plusieurs critères
        
        Args:
            filters: Dictionnaire avec clés: country, category, difficulty, 
                    meal_type, cooking_method, max_time, ingredients, exclude_ingredients
        
        Returns:
            Set des IDs de recettes correspondant à TOUS les filtres
        """
        # Commence avec toutes les recettes (si disponibles)
        if not any([self.country_index, self.category_index]):
            return set()
        
        # Utilise le premier index non vide comme base
        base_set = None
        for index in [self.country_index, self.category_index, self.difficulty_index]:
            if index:
                first_key = next(iter(index))
                base_set = index[first_key].copy()
                for recipe_ids in index.values():
                    base_set.update(recipe_ids)
                break
        
        if base_set is None:
            return set()
        
        # Applique chaque filtre successivement
        filtered_ids = base_set.copy()
        
        # Filtre par pays
        if 'country' in filters and filters['country']:
            country_ids = self.country_index.get(filters['country'], set())
            filtered_ids = filtered_ids.intersection(country_ids)
        
        # Filtre par catégorie
        if 'category' in filters and filters['category']:
            category_ids = self.category_index.get(filters['category'], set())
            filtered_ids = filtered_ids.intersection(category_ids)
        
        # Filtre par difficulté
        if 'difficulty' in filters and filters['difficulty']:
            difficulty_ids = self.difficulty_index.get(filters['difficulty'], set())
            filtered_ids = filtered_ids.intersection(difficulty_ids)
        
        # Filtre par type de repas
        if 'meal_type' in filters and filters['meal_type']:
            meal_type_ids = self.meal_type_index.get(filters['meal_type'], set())
            filtered_ids = filtered_ids.intersection(meal_type_ids)
        
        # Filtre par méthode de cuisson
        if 'cooking_method' in filters and filters['cooking_method']:
            method_ids = self.cooking_method_index.get(filters['cooking_method'], set())
            filtered_ids = filtered_ids.intersection(method_ids)
        
        # Filtre par temps maximum
        if 'max_time' in filters and filters['max_time']:
            time_category = self._get_time_category(filters['max_time'])
            time_ids = set()
            for cat, ids in self.duration_index.items():
                if cat == 'quick' or (cat == 'medium' and filters['max_time'] >= 30):
                    time_ids.update(ids)
            filtered_ids = filtered_ids.intersection(time_ids)
        
        # Filtre par ingrédients requis (doit contenir TOUS)
        if 'ingredients' in filters and filters['ingredients']:
            for ingredient in filters['ingredients']:
                ing_lower = ingredient.strip().lower()
                ingredient_ids = self.ingredient_index.get(ing_lower, set())
                filtered_ids = filtered_ids.intersection(ingredient_ids)
        
        # Filtre par ingrédients exclus (ne doit contenir AUCUN)
        if 'exclude_ingredients' in filters and filters['exclude_ingredients']:
            for ingredient in filters['exclude_ingredients']:
                ing_lower = ingredient.strip().lower()
                exclude_ids = self.ingredient_index.get(ing_lower, set())
                filtered_ids = filtered_ids.difference(exclude_ids)
        
        return filtered_ids
    
    def _get_time_category(self, minutes: int) -> str:
        """Catégorise la durée"""
        if minutes < 30:
            return 'quick'
        elif minutes <= 60:
            return 'medium'
        else:
            return 'long'
    
    def get_facet_values(self) -> Dict[str, List[str]]:
        """Retourne toutes les valeurs possibles pour chaque facette"""
        return {
            'countries': sorted(list(self.all_countries)),
            'categories': sorted(list(self.all_categories)),
            'difficulties': sorted(list(self.all_difficulties)),
            'meal_types': sorted(list(self.all_meal_types)),
            'cooking_methods': sorted(list(self.all_cooking_methods)),
            'duration_categories': ['quick', 'medium', 'long']
        }
    
    def suggest_ingredients(self, prefix: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Suggestions d'ingrédients pour l'auto-complétion"""
        suggestions = []
        prefix = prefix.lower()
        
        for ingredient in self.all_ingredients:
            if ingredient.startswith(prefix):
                frequency = len(self.ingredient_index[ingredient])
                suggestions.append({
                    'ingredient': ingredient,
                    'frequency': frequency
                })
        
        # Trier par fréquence décroissante
        suggestions.sort(key=lambda x: x['frequency'], reverse=True)
        return suggestions[:limit]
    
    def get_recipe_facets(self, recipe_id: str) -> Dict[str, Any]:
        """Retourne toutes les facettes d'une recette spécifique"""
        return {
            'country': self._get_key_for_recipe(recipe_id, self.country_index),
            'category': self._get_key_for_recipe(recipe_id, self.category_index),
            'difficulty': self._get_key_for_recipe(recipe_id, self.difficulty_index),
            'meal_type': self._get_key_for_recipe(recipe_id, self.meal_type_index),
            'cooking_method': self._get_key_for_recipe(recipe_id, self.cooking_method_index),
            'ingredients': self._get_ingredients_for_recipe(recipe_id)
        }
    
    def _get_key_for_recipe(self, recipe_id: str, index: Dict[str, Set[str]]) -> str:
        """Trouve la clé pour une recette dans un index"""
        for key, recipe_ids in index.items():
            if recipe_id in recipe_ids:
                return key
        return 'Unknown'
    
    def _get_ingredients_for_recipe(self, recipe_id: str) -> List[str]:
        """Retourne les ingrédients d'une recette"""
        ingredients = []
        for ing, recipe_ids in self.ingredient_index.items():
            if recipe_id in recipe_ids:
                ingredients.append(ing)
        return sorted(ingredients)
    
    def save(self, filepath: str):
        """Sauvegarde les index sur disque"""
        try:
            data = {
                'country_index': {k: list(v) for k, v in self.country_index.items()},
                'category_index': {k: list(v) for k, v in self.category_index.items()},
                'difficulty_index': {k: list(v) for k, v in self.difficulty_index.items()},
                'meal_type_index': {k: list(v) for k, v in self.meal_type_index.items()},
                'cooking_method_index': {k: list(v) for k, v in self.cooking_method_index.items()},
                'ingredient_index': {k: list(v) for k, v in self.ingredient_index.items()},
                'duration_index': {k: list(v) for k, v in self.duration_index.items()}
            }
            
            with open(filepath, 'wb') as f:
                pickle.dump(data, f)
            
            logger.info(f"✅ Facet index saved to {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error saving facet index: {str(e)}")
            return False
    
    def load(self, filepath: str):
        """Charge les index depuis le disque"""
        try:
            with open(filepath, 'rb') as f:
                data = pickle.load(f)
            
            # Convertir les listes en sets
            for attr_name in ['country_index', 'category_index', 'difficulty_index', 
                            'meal_type_index', 'cooking_method_index', 'ingredient_index']:
                index_dict = getattr(self, attr_name)
                index_dict.clear()
                for k, v in data.get(attr_name, {}).items():
                    index_dict[k] = set(v)
                    # Mettre à jour les valeurs uniques
                    getattr(self, f'all_{attr_name.replace("_index", "").replace("cooking_method", "cooking_methods")}').add(k)
            
            # Charger l'index de durée
            self.duration_index = {k: set(v) for k, v in data.get('duration_index', {}).items()}
            
            logger.info(f"✅ Facet index loaded from {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error loading facet index: {str(e)}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Retourne des statistiques sur les facettes"""
        return {
            'total_countries': len(self.all_countries),
            'total_categories': len(self.all_categories),
            'total_difficulties': len(self.all_difficulties),
            'total_meal_types': len(self.all_meal_types),
            'total_cooking_methods': len(self.all_cooking_methods),
            'total_ingredients': len(self.all_ingredients),
            'top_10_ingredients': sorted(
                [(ing, len(ids)) for ing, ids in self.ingredient_index.items()],
                key=lambda x: x[1],
                reverse=True
            )[:10]
        }