import { useState, useCallback, useEffect } from "react";
import { Header } from "@/components/Header";
import { SearchBar } from "@/components/SearchBar";
import { FilterBar } from "@/components/FilterBar";
import { RecipeGrid } from "@/components/RecipeGrid";
import { RecipeModal } from "@/components/RecipeModal";
import { Recipe, SearchFilters } from "@/types/recipe";
import { searchRecipes } from "@/services/recipeApi";
import { motion } from "framer-motion";

const Index = () => {
  const [query, setQuery] = useState("");
  const [filters, setFilters] = useState<SearchFilters>({});
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedRecipe, setSelectedRecipe] = useState<Recipe | null>(null);
  const [hasSearched, setHasSearched] = useState(false);

  // Initial load - show all recipes
  useEffect(() => {
    handleSearch();
  }, []);

  const handleSearch = useCallback(async () => {
    setIsLoading(true);
    setHasSearched(true);

    try {
      const results = await searchRecipes({ query, filters });
      setRecipes(results);
    } catch (error) {
      console.error("Search error:", error);
      setRecipes([]);
    } finally {
      setIsLoading(false);
    }
  }, [query, filters]);

  // Auto-search when filters change
  useEffect(() => {
    if (hasSearched) {
      handleSearch();
    }
  }, [filters]);

  return (
    <div className="min-h-screen bg-background">
      {/* Decorative background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-primary/5 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-secondary/5 rounded-full blur-3xl" />
      </div>

      <div className="relative container mx-auto px-4 py-12 sm:py-16">
        {/* Header */}
        <Header />

        {/* Search Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5, delay: 0.3 }}
          className="space-y-6 mb-12"
        >
          <SearchBar
            value={query}
            onChange={setQuery}
            onSearch={handleSearch}
            isLoading={isLoading}
          />
          <FilterBar filters={filters} onChange={setFilters} />
        </motion.div>

        {/* Results Count */}
        {hasSearched && !isLoading && recipes.length > 0 && (
          <motion.p
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="text-muted-foreground mb-6"
          >
            Found <span className="font-semibold text-foreground">{recipes.length}</span> recipes
          </motion.p>
        )}

        {/* Recipe Grid */}
        <RecipeGrid
          recipes={recipes}
          isLoading={isLoading}
          onRecipeClick={setSelectedRecipe}
        />

        {/* Recipe Detail Modal */}
        <RecipeModal
          recipe={selectedRecipe}
          isOpen={!!selectedRecipe}
          onClose={() => setSelectedRecipe(null)}
        />
      </div>
    </div>
  );
};

export default Index;
