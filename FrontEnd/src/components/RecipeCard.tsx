import { Recipe, COUNTRIES } from "@/types/recipe";
import { motion } from "framer-motion";
import { Clock, ChefHat } from "lucide-react";

interface RecipeCardProps {
  recipe: Recipe;
  onClick: () => void;
  index: number;
}

const difficultyColors = {
  easy: "bg-secondary text-secondary-foreground",
  medium: "bg-accent text-accent-foreground",
  hard: "bg-primary text-primary-foreground",
};

export function RecipeCard({ recipe, onClick, index }: RecipeCardProps) {
  const country = COUNTRIES.find(
    (c) => c.name.toLowerCase() === recipe.country.toLowerCase()
  );

  return (
    <motion.article
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: index * 0.1 }}
      whileHover={{ y: -8 }}
      onClick={onClick}
      className="group cursor-pointer bg-card rounded-2xl overflow-hidden shadow-card hover:shadow-card-hover transition-all duration-300"
    >
      <div className="relative aspect-[4/3] overflow-hidden">
        <img
          src={recipe.image}
          alt={recipe.title}
          className="w-full h-full object-cover transition-transform duration-500 group-hover:scale-110"
        />
        <div className="absolute inset-0 bg-gradient-to-t from-foreground/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

        {/* Country flag badge */}
        <div className="absolute top-3 left-3 bg-card/90 backdrop-blur-sm px-3 py-1.5 rounded-full shadow-md">
          <span className="flex items-center gap-1.5 text-sm font-medium">
            <span className="text-base">{country?.flag}</span>
            <span>{recipe.country}</span>
          </span>
        </div>

        {/* Difficulty badge */}
        <div
          className={`absolute top-3 right-3 px-3 py-1.5 rounded-full text-xs font-semibold uppercase tracking-wide ${
            difficultyColors[recipe.difficulty]
          }`}
        >
          {recipe.difficulty}
        </div>
      </div>

      <div className="p-5">
        <div className="flex items-center gap-2 text-xs text-muted-foreground mb-2">
          <span className="flex items-center gap-1">
            <ChefHat className="h-3.5 w-3.5" />
            <span className="capitalize">{recipe.meal_type}</span>
          </span>
        </div>

        <h3 className="font-display text-xl font-semibold text-foreground mb-2 group-hover:text-primary transition-colors duration-300">
          {recipe.title}
        </h3>

        <p className="text-sm text-muted-foreground line-clamp-2 leading-relaxed">
          {recipe.description}
        </p>
      </div>
    </motion.article>
  );
}
