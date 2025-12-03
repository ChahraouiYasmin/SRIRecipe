from flask import Flask, jsonify, request
from flask_cors import CORS
from dotenv import load_dotenv
import os

from services.data_loader import DataLoader
from services.faiss_service import FaissService
from services.inverted_index import InvertedIndex
from services.facet_index import FacetIndex
from utils.logger import logger

# Charger les variables d'environnement
load_dotenv()

def create_app():
    """Factory pour créer l'application Flask"""
    
    app = Flask(__name__)
    
    # Configuration
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret')
    app.config['DEBUG'] = os.getenv('DEBUG', 'False').lower() == 'true'
    app.config['DATA_PATH'] = os.getenv('DATA_PATH', './data/recipes')
    app.config['INDEX_PATH'] = os.getenv('INDEX_PATH', './data/indexes')
    
    # Activer CORS
    CORS(app)
    
    # Initialiser le DataLoader
    data_loader = DataLoader(app.config['DATA_PATH'])
    
    # Charger les données
    recipes = data_loader.load_all_recipes()
    
    if not recipes:
        logger.error("❌ Aucune recette chargée!")
        # Créer quand même l'app mais avec données vides
        app.recipes = []
        app.faiss_service = None
        app.inverted_index = None
        app.facet_index = None
        app.data_loader = data_loader
        app.stats = {'total_recipes': 0}
    else:
        # Initialiser les index
        logger.info("🔨 Building indexes...")
        
        # 1. Index inversé
        inverted_index = InvertedIndex()
        # 2. Index facettes
        facet_index = FacetIndex()
        # 3. FAISS sémantique
        faiss_service = FaissService(model_name='paraphrase-MiniLM-L3-v2')
        
        # Construire les index
        logger.info("Building inverted index and facets...")
        for recipe in recipes:
            inverted_index.add_recipe(recipe['id'], recipe)
            facet_index.add_recipe(recipe['id'], recipe)
        
        # Ajouter recettes à FAISS
        logger.info("Adding recipes to FAISS...")
        faiss_service.add_recipes(recipes)
        
        # Afficher statistiques
        inv_stats = inverted_index.get_stats()
        facet_stats = facet_index.get_stats()
        faiss_stats = faiss_service.get_stats()
        
        logger.info(f"✅ Indexing completed:")
        logger.info(f"   - Inverted Index: {inv_stats['total_terms']} terms, {inv_stats['total_recipes']} recipes")
        logger.info(f"   - Facet Index: {facet_stats['total_ingredients']} ingredients, {facet_stats['total_countries']} countries")
        logger.info(f"   - FAISS Index: {faiss_stats['total_recipes']} recipes, dim={faiss_stats['embedding_dimension']}")
        
        # Sauvegarder les index (optionnel)
        index_path = app.config['INDEX_PATH']
        os.makedirs(index_path, exist_ok=True)
        
        inverted_index.save(os.path.join(index_path, 'inverted_index.pkl'))
        facet_index.save(os.path.join(index_path, 'facet_index.pkl'))
        faiss_service.save(os.path.join(index_path, 'faiss_index'))
        
        # Stocker dans le contexte de l'app
        app.recipes = recipes
        app.faiss_service = faiss_service
        app.inverted_index = inverted_index
        app.facet_index = facet_index
        app.data_loader = data_loader
        app.stats = data_loader.get_stats(recipes)
        
        logger.info(f"✅ Application démarrée avec {len(recipes)} recettes")
    
    # ==================== ROUTES API ====================
    
    @app.route('/')
    def home():
        """Route de bienvenue"""
        endpoints = {
            'recipes': '/api/recipes',
            'stats': '/api/stats',
            'health': '/api/health',
            'index_stats': '/api/index/stats',
            'facets': '/api/facets',
            'search_semantic': '/api/search/semantic?q=query',
            'search_text': '/api/search/text?q=query',
            'similar': '/api/recipes/<id>/similar',
            'suggest': '/api/suggest?prefix=text'
        }
        
        return jsonify({
            'message': 'Recipe Search API',
            'version': '1.0.0',
            'endpoints': endpoints
        })
    
    @app.route('/api/health')
    def health_check():
        """Vérification de la santé de l'API"""
        return jsonify({
            'status': 'healthy',
            'recipe_count': len(app.recipes),
            'faiss_available': app.faiss_service is not None,
            'indexes_available': app.inverted_index is not None and app.facet_index is not None
        })
    
    @app.route('/api/stats')
    def get_stats():
        """Retourne les statistiques des recettes"""
        return jsonify(app.stats)
    
    @app.route('/api/index/stats')
    def get_index_stats():
        """Retourne les statistiques des index"""
        if not app.inverted_index or not app.facet_index:
            return jsonify({'error': 'Indexes not available'}), 503
        
        return jsonify({
            'inverted_index': app.inverted_index.get_stats(),
            'facet_index': app.facet_index.get_stats(),
            'faiss': app.faiss_service.get_stats() if app.faiss_service else None,
            'total_recipes': len(app.recipes)
        })
    
    @app.route('/api/recipes')
    def get_recipes():
        """Retourne toutes les recettes"""
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        
        start = (page - 1) * per_page
        end = start + per_page
        
        return jsonify({
            'page': page,
            'per_page': per_page,
            'total': len(app.recipes),
            'recipes': app.recipes[start:end]
        })
    
    @app.route('/api/recipes/<recipe_id>')
    def get_recipe(recipe_id):
        """Retourne une recette spécifique par ID"""
        for recipe in app.recipes:
            if recipe.get('id') == recipe_id:
                return jsonify(recipe)
        
        return jsonify({'error': 'Recipe not found'}), 404
    
    @app.route('/api/facets')
    def get_facets():
        """Retourne toutes les valeurs de facettes disponibles"""
        if not app.facet_index:
            return jsonify({'error': 'Facet index not available'}), 503
        
        return jsonify(app.facet_index.get_facet_values())
    
    # ==================== RECHERCHE ====================
    
    @app.route('/api/search/semantic')
    def semantic_search():
        """Recherche sémantique avec FAISS"""
        if not app.faiss_service:
            return jsonify({'error': 'FAISS semantic search not available'}), 503
        
        query = request.args.get('q', '')
        k = request.args.get('k', 10, type=int)
        
        if not query:
            return jsonify({'error': 'Query parameter "q" is required'}), 400
        
        # Appliquer les filtres si présents
        filters = {}
        for param in ['country', 'category', 'difficulty', 'meal_type', 'cooking_method', 'max_time']:
            value = request.args.get(param)
            if value:
                filters[param] = value
        
        # Recherche sémantique
        results = app.faiss_service.semantic_search(query, k=k)
        
        # Appliquer filtres facettes si disponibles
        if app.facet_index and filters:
            filtered_results = []
            for recipe in results:
                recipe_id = recipe.get('id')
                if recipe_id and app.facet_index.filter_recipes(filters, specific_ids={recipe_id}):
                    filtered_results.append(recipe)
            results = filtered_results
        
        return jsonify({
            'query': query,
            'search_type': 'semantic',
            'filters': filters,
            'count': len(results),
            'results': results
        })
    
    @app.route('/api/search/text')
    def text_search():
        """Recherche textuelle avec index inversé"""
        if not app.inverted_index:
            return jsonify({'error': 'Text search not available'}), 503
        
        query = request.args.get('q', '')
        top_k = request.args.get('top_k', 20, type=int)
        
        if not query:
            return jsonify({'error': 'Query parameter "q" is required'}), 400
        
        # Recherche index inversé
        search_results = app.inverted_index.search(query, top_k=top_k)
        
        # Récupérer les recettes complètes
        results = []
        for recipe_id, score in search_results:
            recipe = next((r for r in app.recipes if r['id'] == recipe_id), None)
            if recipe:
                recipe_copy = recipe.copy()
                recipe_copy['text_score'] = score
                results.append(recipe_copy)
        
        return jsonify({
            'query': query,
            'search_type': 'text',
            'count': len(results),
            'results': results
        })
    
    @app.route('/api/search/hybrid')
    def hybrid_search():
        """Recherche hybride : sémantique + textuelle"""
        query = request.args.get('q', '')
        if not query:
            return jsonify({'error': 'Query parameter "q" is required'}), 400
        
        # Récupérer les filtres
        filters = {}
        for param in ['country', 'category', 'difficulty', 'meal_type', 'cooking_method', 'max_time']:
            value = request.args.get(param)
            if value:
                filters[param] = value
        
        # 1. Recherche sémantique (si disponible)
        semantic_results = []
        if app.faiss_service:
            semantic_results = app.faiss_service.semantic_search(query, k=30)
            # Ajouter un bonus pour résultats sémantiques
            for recipe in semantic_results:
                recipe['hybrid_score'] = recipe.get('semantic_score', 0) * 0.7
        
        # 2. Recherche textuelle (si disponible)
        text_results = []
        if app.inverted_index:
            text_search = app.inverted_index.search(query, top_k=30)
            for recipe_id, score in text_search:
                recipe = next((r for r in app.recipes if r['id'] == recipe_id), None)
                if recipe:
                    recipe_copy = recipe.copy()
                    recipe_copy['hybrid_score'] = score * 0.3
                    text_results.append(recipe_copy)
        
        # 3. Fusionner et dédupliquer
        all_results = {}
        
        # Ajouter résultats sémantiques
        for recipe in semantic_results:
            recipe_id = recipe.get('id')
            if recipe_id:
                all_results[recipe_id] = recipe
        
        # Fusionner avec résultats textuels
        for recipe in text_results:
            recipe_id = recipe.get('id')
            if recipe_id in all_results:
                # Si déjà présent, augmenter le score
                all_results[recipe_id]['hybrid_score'] += recipe['hybrid_score']
                all_results[recipe_id]['text_score'] = recipe.get('text_score', 0)
            else:
                all_results[recipe_id] = recipe
        
        # Convertir en liste et trier par score hybride
        results = list(all_results.values())
        results.sort(key=lambda x: x.get('hybrid_score', 0), reverse=True)
        
        # 4. Appliquer les filtres facettes
        if app.facet_index and filters:
            filtered_results = []
            for recipe in results:
                recipe_id = recipe.get('id')
                if recipe_id and app.facet_index.filter_recipes(filters, specific_ids={recipe_id}):
                    filtered_results.append(recipe)
            results = filtered_results
        
        return jsonify({
            'query': query,
            'search_type': 'hybrid',
            'filters': filters,
            'count': len(results),
            'results': results[:20]  # Limiter à 20 résultats
        })
    
    @app.route('/api/recipes/<recipe_id>/similar')
    def get_similar_recipes(recipe_id):
        """Recettes similaires avec FAISS"""
        if not app.faiss_service:
            return jsonify({'error': 'Similar recipes not available'}), 503
        
        k = request.args.get('k', 5, type=int)
        
        similar = app.faiss_service.find_similar_recipes(recipe_id, k=k)
        
        return jsonify({
            'source_recipe_id': recipe_id,
            'count': len(similar),
            'similar_recipes': similar
        })
    
    @app.route('/api/suggest')
    def get_suggestions():
        """Suggestions d'auto-complétion"""
        if not app.inverted_index:
            return jsonify({'error': 'Suggestions not available'}), 503
        
        prefix = request.args.get('prefix', '')
        limit = request.args.get('limit', 10, type=int)
        
        if not prefix or len(prefix) < 2:
            return jsonify({'suggestions': []})
        
        suggestions = app.inverted_index.get_suggestions(prefix, limit=limit)
        
        return jsonify({
            'prefix': prefix,
            'suggestions': suggestions
        })
    
    @app.route('/api/suggest/ingredients')
    def suggest_ingredients():
        """Suggestions d'ingrédients"""
        if not app.facet_index:
            return jsonify({'error': 'Ingredient suggestions not available'}), 503
        
        prefix = request.args.get('prefix', '')
        limit = request.args.get('limit', 10, type=int)
        
        if not prefix or len(prefix) < 2:
            return jsonify({'suggestions': []})
        
        suggestions = app.facet_index.suggest_ingredients(prefix, limit=limit)
        
        return jsonify({
            'prefix': prefix,
            'suggestions': suggestions
        })
    
    return app

if __name__ == '__main__':
    app = create_app()
    
    # Démarrer le serveur
    port = int(os.getenv('PORT', 5000))
    logger.info(f"🚀 Démarrage du serveur sur http://localhost:{port}")
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=app.config['DEBUG'],
        use_reloader=False 
    )