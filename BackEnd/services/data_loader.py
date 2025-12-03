import json
import os
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime
from utils.logger import logger

class DataLoader:
    """Charge et valide les données JSON des recettes"""
    
    def __init__(self, data_path: str = None):
        # Utiliser le chemin depuis la racine du projet
        if data_path and os.path.isabs(data_path):
            self.data_path = data_path
        else:
            # Construire le chemin depuis la racine du projet
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.data_path = os.path.join(base_dir, data_path) if data_path else os.path.join(base_dir, 'data', 'recipes')
        
        logger.info(f"DataLoader initialized with path: {self.data_path}")
    
    def load_all_recipes(self) -> List[Dict[str, Any]]:
        """Charge toutes les recettes depuis les fichiers JSON"""
        recipes = []
        
        # Vérifier si le dossier existe
        if not os.path.exists(self.data_path):
            logger.error(f"Directory {self.data_path} does not exist!")
            return recipes
        
        # Lister tous les fichiers .json
        json_files = [f for f in os.listdir(self.data_path) if f.endswith('.json')]
        
        if not json_files:
            logger.warning(f"No .json files found in {self.data_path}")
            return recipes
        
        logger.info(f"Loading {len(json_files)} recipe files...")
        
        for json_file in json_files:
            file_path = os.path.join(self.data_path, json_file)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    recipe_data = json.load(f)
                    
                    # Valider la structure de base
                    if self._validate_recipe(recipe_data):
                        # Ajouter un ID unique basé sur le nom du fichier
                        recipe_data['id'] = Path(json_file).stem
                        recipe_data['source_file'] = json_file
                        recipes.append(recipe_data)
                        logger.debug(f"✓ {json_file} loaded successfully")
                    else:
                        logger.warning(f"✗ {json_file} - Invalid structure")
                        
            except json.JSONDecodeError as e:
                logger.error(f"JSON error in {json_file}: {str(e)}")
            except Exception as e:
                logger.error(f"Error loading {json_file}: {str(e)}")
        
        logger.info(f"Loading complete: {len(recipes)} valid recipes loaded")
        return recipes
    
    def _validate_recipe(self, recipe: Dict[str, Any]) -> bool:
        """Valide la structure minimale d'une recette"""
        required_fields = ['title', 'ingredients', 'instructions']
        
        for field in required_fields:
            if field not in recipe:
                return False
        
        # Vérifier que les ingrédients et instructions sont des listes
        if not isinstance(recipe.get('ingredients'), list):
            return False
        if not isinstance(recipe.get('instructions'), list):
            return False
        
        return True
    
    def get_stats(self, recipes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Retourne des statistiques sur les recettes"""
        if not recipes:
            return {}
        
        stats = {
            'total_recipes': len(recipes),
            'countries': {},
            'categories': {},
            'difficulties': {},
            'meal_types': {}
        }
        
        for recipe in recipes:
            # Statistiques par pays
            country = recipe.get('country', 'Unknown')
            stats['countries'][country] = stats['countries'].get(country, 0) + 1
            
            # Statistiques par catégorie
            category = recipe.get('category', 'Unknown')
            stats['categories'][category] = stats['categories'].get(category, 0) + 1
            
            # Statistiques par difficulté
            difficulty = recipe.get('difficulty', 'Unknown')
            stats['difficulties'][difficulty] = stats['difficulties'].get(difficulty, 0) + 1
            
            # Statistiques par type de repas
            meal_type = recipe.get('meal_type', 'Unknown')
            stats['meal_types'][meal_type] = stats['meal_types'].get(meal_type, 0) + 1
        
        return stats
    
    def save_processed_recipes(self, processed_recipes: List[Dict[str, Any]], output_dir: str = None):
        """Sauvegarde les recettes traitées dans un fichier JSON"""
        
        # Si aucun dossier de sortie n'est spécifié, utiliser data/processed
        if output_dir is None:
            base_dir = os.path.dirname(self.data_path)
            output_dir = os.path.join(base_dir, 'processed')
        
        # Créer le dossier s'il n'existe pas
        os.makedirs(output_dir, exist_ok=True)
        
        output_file = os.path.join(output_dir, 'recipes_processed.json')
        
        try:
            # Préparer les données pour la sauvegarde
            save_data = {
                'metadata': {
                    'total_recipes': len(processed_recipes),
                    'processed_at': datetime.now().isoformat(),
                    'source': 'NLP processed recipes'
                },
                'recipes': processed_recipes
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
            
            file_size = os.path.getsize(output_file) / 1024  # Taille en KB
            
            logger.info(f"✅ Processed recipes saved: {output_file}")
            logger.info(f"📊 File size: {file_size:.2f} KB")
            logger.info(f"📁 Location: {output_dir}")
            
            return output_file
            
        except Exception as e:
            logger.error(f"❌ Error saving processed recipes: {str(e)}")
            return None
    
    def save_recipes_to_file(self, recipes: List[Dict[str, Any]], output_file: str = 'all_recipes.json'):
        """Sauvegarde toutes les recettes dans un seul fichier JSON"""
        output_path = os.path.join(self.data_path, '..', output_file)
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(recipes, f, indent=2, ensure_ascii=False)
            logger.info(f"Recipes saved in {output_path}")
            return True
        except Exception as e:
            logger.error(f"Error saving: {str(e)}")
            return False