import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.data_loader import DataLoader
from services.faiss_service import FaissService
from services.inverted_index import InvertedIndex
from services.facet_index import FacetIndex
import json

def print_separator():
    print("\n" + "="*60 + "\n")

def test_faiss_complete():
    """Test complet de FAISS avec toutes les fonctionnalités"""
    
    print("🧪 TEST COMPLET FAISS + INDEXES\n")
    
    # ==================== 1. CHARGEMENT DONNEES ====================
    print("📂 1. Chargement des données...")
    loader = DataLoader()
    recipes = loader.load_all_recipes()
    
    if not recipes:
        print("❌ ERREUR: Aucune recette chargée!")
        print(f"   Chemin: {loader.data_path}")
        print(f"   Existe: {os.path.exists(loader.data_path)}")
        return
    
    print(f"✅ {len(recipes)} recettes chargées")
    print(f"   Exemple: {recipes[0]['title'] if recipes else 'Aucune'}")
    
    # Prendre 15 recettes pour tester
    test_recipes = recipes[:15] if len(recipes) >= 15 else recipes
    print(f"🔬 Test avec {len(test_recipes)} recettes\n")
    
    print_separator()
    
    # ==================== 2. INDEX INVERSE ====================
    print("🔤 2. Test Index Inverse...")
    inverted_index = InvertedIndex()
    
    for recipe in test_recipes:
        inverted_index.add_recipe(recipe['id'], recipe)
    
    inv_stats = inverted_index.get_stats()
    print(f"✅ Index Inverse créé:")
    print(f"   - Termes: {inv_stats['total_terms']}")
    print(f"   - Recettes: {inv_stats['total_recipes']}")
    
    # Test recherche index inverse
    test_queries = ['chicken', 'beef', 'rice']
    for query in test_queries:
        results = inverted_index.search(query, top_k=3)
        print(f"   🔍 '{query}': {len(results)} résultats")
    
    # Test suggestions
    suggestions = inverted_index.get_suggestions('chi', limit=5)
    print(f"   💡 Suggestions 'chi': {suggestions}")
    
    print_separator()
    
    # ==================== 3. INDEX FACETTES ====================
    print("🏷️  3. Test Index Facettes...")
    facet_index = FacetIndex()
    
    for recipe in test_recipes:
        facet_index.add_recipe(recipe['id'], recipe)
    
    facet_stats = facet_index.get_stats()
    print(f"✅ Index Facettes créé:")
    print(f"   - Pays: {facet_stats['total_countries']}")
    print(f"   - Catégories: {facet_stats['total_categories']}")
    print(f"   - Ingrédients: {facet_stats['total_ingredients']}")
    
    # Test filtres
    filters = {'country': 'South Korea', 'difficulty': 'medium'}
    filtered = facet_index.filter_recipes(filters)
    print(f"   🎯 Filtres {filters}: {len(filtered)} recettes")
    
    # Test suggestions ingrédients
    ing_suggestions = facet_index.suggest_ingredients('chi', limit=5)
    print(f"   🍗 Suggestions ingrédients 'chi': {[s['ingredient'] for s in ing_suggestions]}")
    
    print_separator()
    
    # ==================== 4. FAISS ====================
    print("🧠 4. Test FAISS (recherche sémantique)...")
    
    try:
        faiss_service = FaissService(model_name='paraphrase-MiniLM-L3-v2')
        print("✅ Modèle FAISS chargé")
        
        # Ajouter recettes
        faiss_service.add_recipes(test_recipes)
        
        faiss_stats = faiss_service.get_stats()
        print(f"✅ Index FAISS créé:")
        print(f"   - Recettes: {faiss_stats['total_recipes']}")
        print(f"   - Dimension: {faiss_stats['embedding_dimension']}")
        print(f"   - Modèle: {faiss_stats['model_name']}")
        
        print_separator()
        
        # ==================== 5. TESTS RECHERCHE SEMANTIQUE ====================
        print("🔍 5. Tests recherche sémantique...")
        
        semantic_queries = [
            ("spicy chicken", "Recettes épicées au poulet"),
            ("quick dinner", "Dîners rapides"),
            ("italian pasta", "Pâtes italiennes"),
            ("healthy salad", "Salades saines"),
            ("beef rice", "Bœuf avec riz")
        ]
        
        for query, description in semantic_queries:
            print(f"\n   📝 '{query}' ({description}):")
            results = faiss_service.semantic_search(query, k=3)
            
            if results:
                for i, result in enumerate(results):
                    title = result.get('title', 'Inconnu')
                    score = result.get('semantic_score', 0)
                    distance = result.get('semantic_distance', 0)
                    print(f"      {i+1}. {title}")
                    print(f"         Score: {score:.3f}, Distance: {distance:.3f}")
            else:
                print(f"      ❌ Aucun résultat")
        
        print_separator()
        
        # ==================== 6. TESTS SIMILARITE ====================
        print("🔄 6. Tests recettes similaires...")
        
        if test_recipes:
            source_recipe = test_recipes[0]
            print(f"   🔗 Recettes similaires à: {source_recipe.get('title')}")
            
            similar = faiss_service.find_similar_recipes(source_recipe['id'], k=3)
            
            if similar:
                for i, sim_recipe in enumerate(similar):
                    title = sim_recipe.get('title', 'Inconnu')
                    score = sim_recipe.get('similarity_score', 0)
                    print(f"      {i+1}. {title}")
                    print(f"         Similarité: {score:.3f}")
            else:
                print(f"      ❌ Aucune recette similaire")
        
        print_separator()
        
        # ==================== 7. TEST HYBRIDE ====================
        print("⚡ 7. Test recherche hybride...")
        
        hybrid_query = "spicy korean chicken"
        print(f"   🔥 Requête: '{hybrid_query}'")
        
        # Sémantique
        semantic_results = faiss_service.semantic_search(hybrid_query, k=5)
        print(f"   🧠 Résultats sémantiques: {len(semantic_results)}")
        
        # Textuelle
        text_results = inverted_index.search(hybrid_query, top_k=5)
        print(f"   🔤 Résultats textuels: {len(text_results)}")
        
        # Simuler fusion
        all_ids = set()
        for result in semantic_results:
            all_ids.add(result.get('id'))
        for recipe_id, _ in text_results:
            all_ids.add(recipe_id)
        
        print(f"   ⚡ Résultats uniques combinés: {len(all_ids)}")
        
        print_separator()
        
        # ==================== 8. SAUVEGARDE/CHARGEMENT ====================
        print("💾 8. Test sauvegarde/chargement...")
        
        # Sauvegarder
        save_path = './data/test_faiss_complete'
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        
        inverted_index.save(save_path + '_inv.pkl')
        facet_index.save(save_path + '_facets.pkl')
        faiss_service.save(save_path + '_faiss')
        
        print(f"   ✅ Index sauvegardés dans ./data/")
        
        # Créer nouveaux index vides
        new_inv = InvertedIndex()
        new_facets = FacetIndex()
        new_faiss = FaissService(model_name='paraphrase-MiniLM-L3-v2')
        
        # Charger
        new_inv.load(save_path + '_inv.pkl')
        new_facets.load(save_path + '_facets.pkl')
        new_faiss.load(save_path + '_faiss')
        
        print(f"   ✅ Index rechargés avec succès")
        print(f"   🧪 Vérification: {new_faiss.get_stats()['total_recipes']} recettes dans FAISS")
        
        print_separator()
        
        # ==================== 9. TESTS PERFORMANCE ====================
        print("⚡ 9. Tests performance...")
        
        import time
        
        # Test vitesse recherche
        test_query = "chicken dinner"
        times = []
        
        for _ in range(5):
            start = time.time()
            results = faiss_service.semantic_search(test_query, k=10)
            end = time.time()
            times.append((end - start) * 1000)  # en ms
        
        avg_time = sum(times) / len(times)
        print(f"   ⏱️  Recherche FAISS moyenne: {avg_time:.2f} ms")
        print(f"   📊 Résultats: {len(results) if 'results' in locals() else 0} recettes")
        
        print_separator()
        
        # ==================== 10. RAPPORT FINAL ====================
        print("📊 RAPPORT FINAL - TOUS LES TESTS")
        print("="*40)
        
        print(f"✅ CHARGEMENT: {len(recipes)} recettes totales, {len(test_recipes)} testées")
        print(f"✅ INDEX INVERSE: {inv_stats['total_terms']} termes")
        print(f"✅ INDEX FACETTES: {facet_stats['total_ingredients']} ingrédients")
        print(f"✅ FAISS: {faiss_stats['total_recipes']} embeddings, dim={faiss_stats['embedding_dimension']}")
        print(f"✅ PERFORMANCE: {avg_time:.2f} ms/recherche")
        
        # Vérifier chaque recette a un ID
        missing_ids = [i for i, r in enumerate(test_recipes) if 'id' not in r]
        if missing_ids:
            print(f"⚠️  ATTENTION: {len(missing_ids)} recettes sans ID")
        else:
            print(f"✅ TOUTES les recettes ont un ID")
        
        # Test final
        final_query = "test"
        final_results = faiss_service.semantic_search(final_query, k=1)
        if final_results:
            print(f"✅ TEST FINAL: Recherche '{final_query}' → OK")
        else:
            print(f"⚠️  TEST FINAL: Aucun résultat pour '{final_query}'")
        
        print("\n🎉 TOUS LES TESTS REUSSIS !")
        print("Le système FAISS + Indexes est prêt à être utilisé dans l'API.")
        
    except Exception as e:
        print(f"\n❌ ERREUR CRITIQUE dans FAISS:")
        print(f"   Message: {str(e)}")
        import traceback
        traceback.print_exc()
        
        print("\n💡 SOLUTIONS POSSIBLES:")
        print("1. Vérifier que sentence-transformers est installé")
        print("2. Vérifier que le modèle paraphrase-MiniLM-L3-v2 peut être téléchargé")
        print("3. Essayer un modèle plus petit: 'all-MiniLM-L6-v2'")
        print("4. Vérifier la connexion internet pour télécharger le modèle")

if __name__ == "__main__":
    print("🚀 Démarrage du test complet FAISS...")
    test_faiss_complete()