import { useState, useCallback, useEffect } from "react";
import { Header } from "@/components/Header";
import { SearchBar } from "@/components/SearchBar";
import { FilterBar } from "@/components/FilterBar";
import { RecipeGrid } from "@/components/RecipeGrid";
import { RecipeModal } from "@/components/RecipeModal";
import { Dashboard } from "@/components/Dashboard";
import { Pagination } from "@/components/Pagination";
import { Footer } from "@/components/Footer";
import { Recipe, SearchFilters } from "@/types/recipe";
import { searchRecipes } from "@/services/recipeApi";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { BarChart3, X } from "lucide-react";

const RECIPES_PER_PAGE = 12;

const Index = () => {
  const [query, setQuery] = useState("");
  const [filters, setFilters] = useState<SearchFilters>({});
  const [allRecipes, setAllRecipes] = useState<Recipe[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [selectedRecipe, setSelectedRecipe] = useState<Recipe | null>(null);
  const [hasSearched, setHasSearched] = useState(false);
  const [currentPage, setCurrentPage] = useState(1);
  const [showDashboard, setShowDashboard] = useState(false);

  // Initial load - show all recipes
  useEffect(() => {
    handleSearch();
  }, []);

  const handleSearch = useCallback(async () => {
    setIsLoading(true);
    setHasSearched(true);
    setCurrentPage(1); // Reset to first page on new search

    try {
      const results = await searchRecipes({ query, filters });
      setAllRecipes(results);
    } catch (error) {
      console.error("Search error:", error);
      setAllRecipes([]);
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

  // Calculate pagination
  const totalPages = Math.ceil(allRecipes.length / RECIPES_PER_PAGE);
  const startIndex = (currentPage - 1) * RECIPES_PER_PAGE;
  const endIndex = startIndex + RECIPES_PER_PAGE;
  const currentRecipes = allRecipes.slice(startIndex, endIndex);

  const handlePageChange = (page: number) => {
    setCurrentPage(page);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Decorative background */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-primary/5 rounded-full blur-3xl" />
        <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-secondary/5 rounded-full blur-3xl" />
      </div>

      <div className="relative container mx-auto px-4 py-12 sm:py-16 flex-grow">
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

        {/* Dashboard Toggle */}
        {hasSearched && !isLoading && allRecipes.length > 0 && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="flex items-center justify-between mb-6"
          >
            <p className="text-muted-foreground">
              Found <span className="font-semibold text-foreground">{allRecipes.length}</span> recipes
              {totalPages > 1 && (
                <span className="ml-2">
                  (Page {currentPage} of {totalPages})
                </span>
              )}
            </p>
            <Button
              variant={showDashboard ? "default" : "outline"}
              size="sm"
              onClick={() => setShowDashboard(!showDashboard)}
              className="gap-2"
            >
              {showDashboard ? (
                <>
                  <X className="h-4 w-4" />
                  Hide Stats
                </>
              ) : (
                <>
                  <BarChart3 className="h-4 w-4" />
                  Show Stats
                </>
              )}
            </Button>
          </motion.div>
        )}

        {/* Dashboard */}
        <Dashboard recipes={allRecipes} isVisible={showDashboard} />

        {/* Recipe Grid */}
        <RecipeGrid
          recipes={currentRecipes}
          isLoading={isLoading}
          onRecipeClick={setSelectedRecipe}
        />

        {/* Pagination */}
        {!isLoading && allRecipes.length > 0 && (
          <Pagination
            currentPage={currentPage}
            totalPages={totalPages}
            onPageChange={handlePageChange}
          />
        )}

        {/* Recipe Detail Modal */}
        <RecipeModal
          recipe={selectedRecipe}
          isOpen={!!selectedRecipe}
          onClose={() => setSelectedRecipe(null)}
        />
      </div>

      {/* Footer */}
      <Footer />
    </div>
  );
};

export default Index;