import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.data_loader import DataLoader
from services.text_processor import TextProcessor
import json

def test_english_processing():
    """Teste le traitement NLP sur des recettes en anglais"""
    
    print("=== English NLP Processing Test ===\n")
    
    # 1. Charger les recettes
    loader = DataLoader()
    recipes = loader.load_all_recipes()
    
    if not recipes:
        print("❌ No recipes loaded!")
        return
    
    print(f"✅ {len(recipes)} recipes loaded")
    
    # 2. Initialiser le processeur
    processor = TextProcessor()
    
    # 3. Traiter la première recette
    if len(recipes) > 0:
        test_recipe = recipes[0]
        print(f"\n🔍 Testing on: {test_recipe.get('title')}")
        print(f"🌍 Country: {test_recipe.get('country')}")
        
        processed = processor.process_recipe(test_recipe)
        
        # 4. Afficher les résultats
        print(f"\n📝 Original title: {test_recipe.get('title')}")
        print(f"🔑 Title keywords: {processed['processed'].get('title_keywords', [])}")
        
        print(f"\n📊 Ingredients analysis:")
        ingredients = processed['processed'].get('ingredients', [])
        print(f"   Found {len(ingredients)} ingredients")
        if ingredients:
            print(f"   First 3 ingredients processed:")
            for i, ing in enumerate(ingredients[:3]):
                print(f"     {i+1}. {ing.get('original')}")
                print(f"        Keywords: {ing.get('keywords', [])[:5]}")
                print(f"        Base ingredient: {ing.get('base_ingredient')}")
        
        print(f"\n🔪 Cooking techniques found:")
        techniques = processed['metadata'].get('cooking_techniques', [])
        print(f"   {techniques if techniques else 'None detected'}")
        
        print(f"\n🎯 Facets for filtering:")
        for key, value in processed['facets'].items():
            if value:
                print(f"   • {key}: {value}")
        
        print(f"\n📈 Full text keywords ({len(processed['processed'].get('full_text_keywords', []))} total):")
        full_kw = processed['processed'].get('full_text_keywords', [])
        print(f"   Sample: {full_kw[:15]}")
    
    # 5. Traiter toutes les recettes et sauvegarder
    print(f"\n🔄 Processing all recipes...")
    all_processed = processor.batch_process_recipes(recipes)
    
    print(f"\n💾 Saving processed recipes...")
    saved_file = loader.save_processed_recipes(all_processed)
    
    if saved_file:
        print(f"✅ File saved: {saved_file}")
        
        # Lire et afficher quelques statistiques
        try:
            with open(saved_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            print(f"\n📊 Processing statistics:")
            print(f"   Total recipes processed: {len(data)}")
            
            # Compter les recettes par difficulté
            difficulties = {}
            countries = {}
            for recipe in data:
                diff = recipe['facets'].get('difficulty', 'unknown')
                difficulties[diff] = difficulties.get(diff, 0) + 1
                
                country = recipe['facets'].get('country', 'unknown')
                countries[country] = countries.get(country, 0) + 1
            
            print(f"\n   By difficulty:")
            for diff, count in difficulties.items():
                print(f"     {diff}: {count}")
            
            print(f"\n   By country (top 5):")
            sorted_countries = sorted(countries.items(), key=lambda x: x[1], reverse=True)
            for country, count in sorted_countries[:5]:
                print(f"     {country}: {count}")
                
        except Exception as e:
            print(f"❌ Error reading saved file: {str(e)}")
    
    print("\n✅ Test completed successfully!")

if __name__ == "__main__":
    test_english_processing()