import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.data_loader import DataLoader
from services.inverted_index import InvertedIndex
from services.facet_index import FacetIndex

def test_indexing():
    """Teste la construction des index inversés"""
    
    print("=== Testing Inverted and Facet Indexing ===\n")
    
    # 1. Charger les recettes
    loader = DataLoader()
    recipes = loader.load_all_recipes()
    
    if not recipes:
        print("❌ No recipes loaded!")
        return
    
    print(f"✅ {len(recipes)} recipes loaded\n")
    
    # 2. Construire l'index inversé
    print("🔨 Building inverted index...")
    inverted_index = InvertedIndex()
    for recipe in recipes[:5]:  # Test avec 5 recettes d'abord
        inverted_index.add_recipe(recipe['id'], recipe)
    
    inv_stats = inverted_index.get_stats()
    print(f"✅ Inverted index built:")
    print(f"   - Total terms: {inv_stats['total_terms']}")
    print(f"   - Total recipes: {inv_stats['total_recipes']}")
    print(f"   - Avg terms per recipe: {inv_stats['avg_terms_per_recipe']:.1f}")
    print(f"   - Top 5 terms: {[term for term, _ in inv_stats['top_10_terms'][:5]]}")
    
    # 3. Tester la recherche
    print("\n🔍 Testing search...")
    test_queries = ['chicken', 'beef rice', 'spicy']
    for query in test_queries:
        results = inverted_index.search(query, top_k=3)
        print(f"   Query: '{query}' -> {len(results)} results")
        if results:
            for i, (recipe_id, score) in enumerate(results[:2]):
                print(f"      {i+1}. Recipe {recipe_id} (score: {score:.3f})")
    
    # 4. Tester les suggestions
    print("\n💡 Testing suggestions...")
    prefixes = ['chi', 'bee', 'oni']
    for prefix in prefixes:
        suggestions = inverted_index.get_suggestions(prefix, limit=3)
        print(f"   Prefix: '{prefix}' -> {suggestions}")
    
    # 5. Construire l'index de facettes
    print("\n🔨 Building facet index...")
    facet_index = FacetIndex()
    for recipe in recipes[:5]:
        facet_index.add_recipe(recipe['id'], recipe)
    
    facet_stats = facet_index.get_stats()
    print(f"✅ Facet index built:")
    print(f"   - Countries: {facet_stats['total_countries']}")
    print(f"   - Categories: {facet_stats['total_categories']}")
    print(f"   - Ingredients: {facet_stats['total_ingredients']}")
    print(f"   - Top 5 ingredients: {[ing for ing, _ in facet_stats['top_10_ingredients'][:5]]}")
    
    # 6. Tester le filtrage
    print("\n🎯 Testing filtering...")
    filters = {'country': 'South Korea', 'difficulty': 'medium'}
    filtered_ids = facet_index.filter_recipes(filters)
    print(f"   Filters: {filters}")
    print(f"   -> {len(filtered_ids)} recipes match")
    
    # 7. Tester les suggestions d'ingrédients
    print("\n🍅 Testing ingredient suggestions...")
    ingredient_prefixes = ['chi', 'on', 'gar']
    for prefix in ingredient_prefixes:
        suggestions = facet_index.suggest_ingredients(prefix, limit=3)
        print(f"   Prefix: '{prefix}' -> {[s['ingredient'] for s in suggestions]}")
    
    print("\n✅ All tests completed successfully!")

if __name__ == "__main__":
    test_indexing()