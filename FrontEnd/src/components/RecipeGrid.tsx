import { Recipe } from "@/types/recipe";
import { RecipeCard } from "./RecipeCard";
import { motion } from "framer-motion";
import { UtensilsCrossed } from "lucide-react";

interface RecipeGridProps {
  recipes: Recipe[];
  isLoading: boolean;
  onRecipeClick: (recipe: Recipe) => void;
}

function LoadingSkeleton() {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
      {[...Array(8)].map((_, i) => (
        <div
          key={i}
          className="bg-card rounded-2xl overflow-hidden shadow-card animate-pulse"
        >
          <div className="aspect-[4/3] bg-muted" />
          <div className="p-5 space-y-3">
            <div className="h-3 w-20 bg-muted rounded" />
            <div className="h-6 w-3/4 bg-muted rounded" />
            <div className="h-4 w-full bg-muted rounded" />
            <div className="h-4 w-2/3 bg-muted rounded" />
          </div>
        </div>
      ))}
    </div>
  );
}

function EmptyState() {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      className="flex flex-col items-center justify-center py-20 text-center"
    >
      <div className="w-24 h-24 rounded-full bg-muted flex items-center justify-center mb-6">
        <UtensilsCrossed className="w-12 h-12 text-muted-foreground" />
      </div>
      <h3 className="font-display text-2xl font-semibold text-foreground mb-2">
        No recipes found
      </h3>
      <p className="text-muted-foreground max-w-md">
        Try adjusting your search query or filters to discover delicious recipes from around the world.
      </p>
    </motion.div>
  );
}

export function RecipeGrid({ recipes, isLoading, onRecipeClick }: RecipeGridProps) {
  if (isLoading) {
    return <LoadingSkeleton />;
  }

  if (recipes.length === 0) {
    return <EmptyState />;
  }

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6"
    >
      {recipes.map((recipe, index) => (
        <RecipeCard
          key={recipe.id}
          recipe={recipe}
          onClick={() => onRecipeClick(recipe)}
          index={index}
        />
      ))}
    </motion.div>
  );
}
