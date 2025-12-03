import re
import spacy
from typing import Dict, List, Any
from utils.logger import logger
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize

# Télécharger les ressources NLTK (une seule fois)
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')
    nltk.download('wordnet')
    nltk.download('omw-eng')

class TextProcessor:
    """Processeur de texte pour le traitement NLP des recettes en anglais"""
    
    def __init__(self):
        # Charger le modèle SpaCy anglais
        try:
            self.nlp = spacy.load('en_core_web_sm')
            logger.info("English SpaCy model loaded successfully")
        except:
            logger.warning("SpaCy not available, using NLTK only")
            self.nlp = None
        
        # Initialiser NLTK
        self.english_stopwords = set(stopwords.words('english'))
        self.lemmatizer = WordNetLemmatizer()
        
        # Stop words personnalisés pour les recettes culinaires
        self.recipe_stopwords = {
            'recipe', 'make', 'prepare', 'cook', 'serve',
            'ingredient', 'ingredients', 'step', 'steps',
            'minute', 'minutes', 'hour', 'hours',
            'tablespoon', 'tablespoons', 'tbsp', 'teaspoon', 'teaspoons', 'tsp',
            'cup', 'cups', 'ounce', 'ounces', 'oz', 'pound', 'pounds', 'lb',
            'gram', 'grams', 'g', 'kilogram', 'kilograms', 'kg',
            'milliliter', 'milliliters', 'ml', 'liter', 'liters', 'l',
            'small', 'medium', 'large', 'some', 'about', 'approximately',
            'optional', 'fresh', 'dried', 'chopped', 'sliced', 'diced', 'minced'
        }
        
        # Expressions régulières pour le nettoyage
        self.quantity_pattern = re.compile(r'\b\d+\s*(g|kg|ml|l|cl|tbsp|tsp|cup|cups|oz|lb|pound|pounds)\b', re.IGNORECASE)
        self.number_pattern = re.compile(r'\b\d+\b')
        
        # Liste des techniques de cuisine communes
        self.cooking_techniques = {
            'chop', 'slice', 'dice', 'mince', 'grate', 'peel', 'whisk',
            'stir', 'mix', 'blend', 'beat', 'knead', 'fold', 'whip',
            'boil', 'simmer', 'steam', 'poach', 'fry', 'sauté', 'pan-fry',
            'deep-fry', 'stir-fry', 'roast', 'bake', 'grill', 'broil',
            'barbecue', 'sear', 'braise', 'stew', 'marinate', 'season',
            'garnish', 'plate', 'serve'
        }
    
    def clean_text(self, text: str) -> str:
        """Nettoie le texte"""
        if not text or not isinstance(text, str):
            return ""
        
        # Convertir en minuscules
        text = text.lower()
        
        # Supprimer la ponctuation spéciale mais garder les apostrophes et tirets
        text = re.sub(r'[^\w\s\'-]', ' ', text)
        
        # Supprimer les nombres isolés (mais pas dans "2 cups")
        text = self.number_pattern.sub(' ', text)
        
        # Normaliser les espaces
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text
    
    def tokenize(self, text: str) -> List[str]:
        """Tokenize le texte"""
        if self.nlp:
            # Utiliser SpaCy si disponible
            doc = self.nlp(text)
            tokens = [token.text for token in doc if not token.is_punct and not token.is_space]
        else:
            # Fallback sur NLTK
            tokens = word_tokenize(text)
        
        return tokens
    
    def remove_stopwords(self, tokens: List[str]) -> List[str]:
        """Supprime les stop words"""
        all_stopwords = self.english_stopwords.union(self.recipe_stopwords)
        return [token for token in tokens if token not in all_stopwords and len(token) > 2]
    
    def lemmatize(self, tokens: List[str]) -> List[str]:
        """Lemmatise les tokens"""
        lemmas = []
        
        if self.nlp:
            # Utiliser SpaCy pour la lemmatisation (plus précise)
            for token in tokens:
                doc = self.nlp(token)
                if len(doc) > 0:
                    lemma = doc[0].lemma_
                    # SpaCy retourne parfois '-PRON-' pour les pronoms
                    if lemma != '-PRON-':
                        lemmas.append(lemma)
        else:
            # Utiliser le lemmatizer NLTK
            for token in tokens:
                lemma = self.lemmatizer.lemmatize(token)
                lemmas.append(lemma)
        
        return lemmas
    
    def extract_cooking_techniques(self, text: str) -> List[str]:
        """Extrait les techniques de cuisine mentionnées"""
        tokens = self.tokenize(text)
        techniques_found = []
        
        for token in tokens:
            if token in self.cooking_techniques:
                techniques_found.append(token)
        
        return list(set(techniques_found))
    
    def extract_keywords(self, text: str) -> List[str]:
        """Extrait les mots-clés d'un texte"""
        cleaned = self.clean_text(text)
        tokens = self.tokenize(cleaned)
        filtered = self.remove_stopwords(tokens)
        lemmas = self.lemmatize(filtered)
        
        # Retirer les doublons tout en préservant l'ordre
        unique_lemmas = []
        seen = set()
        for lemma in lemmas:
            if lemma not in seen:
                seen.add(lemma)
                unique_lemmas.append(lemma)
        
        return unique_lemmas
    
    def process_ingredient(self, ingredient_item: str) -> Dict[str, Any]:
        """Traite un ingrédient pour en extraire les composants"""
        if not ingredient_item:
            return {}
        
        # Nettoyer l'ingrédient
        cleaned = self.clean_text(ingredient_item)
        
        # Extraire les mots-clés
        keywords = self.extract_keywords(cleaned)
        
        # Identifier si c'est un ingrédient de base
        base_ingredients = {
            # Viandes
            'beef', 'chicken', 'pork', 'lamb', 'fish', 'salmon', 'tuna',
            'shrimp', 'prawn', 'crab', 'lobster', 'egg', 'eggs',
            # Légumes
            'onion', 'garlic', 'tomato', 'potato', 'carrot', 'broccoli',
            'spinach', 'lettuce', 'cabbage', 'pepper', 'mushroom',
            # Fruits
            'apple', 'orange', 'lemon', 'lime', 'banana', 'strawberry',
            # Produits laitiers
            'milk', 'cheese', 'butter', 'yogurt', 'cream',
            # Céréales
            'rice', 'pasta', 'noodle', 'bread', 'flour',
            # Épices et herbes
            'salt', 'pepper', 'sugar', 'oil', 'vinegar', 'soy sauce'
        }
        
        base_ingredient = None
        for kw in keywords:
            if kw in base_ingredients:
                base_ingredient = kw
                break
        
        return {
            'original': ingredient_item,
            'cleaned': cleaned,
            'keywords': keywords,
            'base_ingredient': base_ingredient,
            'is_main': base_ingredient is not None
        }
    
    def process_recipe(self, recipe: Dict[str, Any]) -> Dict[str, Any]:
        """Traite une recette complète"""
        
        logger.debug(f"Processing recipe: {recipe.get('title', 'Unknown')}")
        
        # Préparer le document traité
        processed = {
            'id': recipe.get('id'),
            'source_file': recipe.get('source_file'),
            'original': recipe,  # Garder les données originales
            'searchable': {},     # Champs pour la recherche
            'processed': {},      # Données traitées
            'metadata': {},       # Métadonnées extraites
            'facets': {}          # Facettes pour le filtrage
        }
        
        # 1. Traiter le titre
        if 'title' in recipe:
            title = recipe['title']
            processed['searchable']['title'] = title
            processed['processed']['title_keywords'] = self.extract_keywords(title)
        
        # 2. Traiter la description
        if 'description' in recipe:
            description = recipe['description']
            processed['searchable']['description'] = description
            processed['processed']['description_keywords'] = self.extract_keywords(description)
        
        # 3. Traiter les ingrédients
        if 'ingredients' in recipe:
            ingredients_text = ' '.join([
                f"{ing.get('item', '')} {ing.get('quantity', '')}" 
                for ing in recipe['ingredients']
            ])
            processed['searchable']['ingredients_text'] = ingredients_text
            processed['processed']['ingredients_keywords'] = self.extract_keywords(ingredients_text)
            
            # Traiter chaque ingrédient individuellement
            processed_ingredients = []
            for ing in recipe['ingredients']:
                processed_ing = self.process_ingredient(ing.get('item', ''))
                processed_ing['quantity'] = ing.get('quantity', '')
                processed_ingredients.append(processed_ing)
            
            processed['processed']['ingredients'] = processed_ingredients
            
            # Extraire les ingrédients de base
            base_ingredients = [pi['base_ingredient'] for pi in processed_ingredients 
                               if pi.get('base_ingredient')]
            processed['metadata']['base_ingredients'] = list(set(base_ingredients))
            processed['metadata']['ingredient_count'] = len(recipe['ingredients'])
        
        # 4. Traiter les instructions
        if 'instructions' in recipe:
            instructions_text = ' '.join(recipe['instructions'])
            processed['searchable']['instructions_text'] = instructions_text
            processed['processed']['instructions_keywords'] = self.extract_keywords(instructions_text)
            
            # Extraire les techniques de cuisine
            techniques = self.extract_cooking_techniques(instructions_text)
            processed['metadata']['cooking_techniques'] = techniques
            
            # Compter les étapes
            processed['metadata']['step_count'] = len(recipe['instructions'])
        
        # 5. Traiter les tags
        if 'tags' in recipe:
            tags_text = ' '.join(recipe['tags'])
            processed['searchable']['tags_text'] = tags_text
            processed['processed']['tags_keywords'] = self.extract_keywords(tags_text)
            processed['metadata']['tags'] = recipe['tags']
        
        # 6. Extraire toutes les facettes
        processed['facets'] = {
            'category': recipe.get('category'),
            'difficulty': recipe.get('difficulty'),
            'meal_type': recipe.get('meal_type'),
            'country': recipe.get('country'),
            'cooking_method': recipe.get('cooking_method'),
            'duration_total': recipe.get('duration', {}).get('total', 0),
            'duration_prep': recipe.get('duration', {}).get('prep', 0),
            'duration_cook': recipe.get('duration', {}).get('cook', 0),
            'servings': recipe.get('servings', 1),
            'dish_type': recipe.get('dish_type')
        }
        
        # 7. Créer un champ de recherche complet
        all_searchable_parts = []
        if 'title' in recipe:
            all_searchable_parts.append(recipe['title'])
        if 'description' in recipe:
            all_searchable_parts.append(recipe['description'])
        if 'ingredients' in recipe:
            all_searchable_parts.append(ingredients_text)
        if 'instructions' in recipe:
            all_searchable_parts.append(instructions_text)
        if 'tags' in recipe:
            all_searchable_parts.append(tags_text)
        
        all_searchable_text = ' '.join(all_searchable_parts)
        processed['searchable']['full_text'] = all_searchable_text
        processed['processed']['full_text_keywords'] = self.extract_keywords(all_searchable_text)
        
        # 8. Ajouter un timestamp de traitement
        from datetime import datetime
        processed['metadata']['processed_at'] = datetime.now().isoformat()
        
        logger.debug(f"✓ Recipe processed: {recipe.get('title')}")
        return processed
    
    def batch_process_recipes(self, recipes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Traite plusieurs recettes en batch"""
        logger.info(f"Starting batch processing of {len(recipes)} recipes")
        
        processed_recipes = []
        success_count = 0
        error_count = 0
        
        for i, recipe in enumerate(recipes):
            try:
                processed = self.process_recipe(recipe)
                processed_recipes.append(processed)
                success_count += 1
                
                if (i + 1) % 10 == 0:
                    logger.info(f"Processed: {i + 1}/{len(recipes)} recipes")
                    
            except Exception as e:
                logger.error(f"Error processing recipe {recipe.get('title', 'Unknown')}: {str(e)}")
                error_count += 1
        
        logger.info(f"Processing complete: {success_count} successful, {error_count} failed")
        return processed_recipes