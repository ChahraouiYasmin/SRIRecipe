import { Recipe, COUNTRIES } from "@/types/recipe";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { ArrowLeft, ChefHat, Clock, Users } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

interface RecipeModalProps {
  recipe: Recipe | null;
  isOpen: boolean;
  onClose: () => void;
}

const difficultyColors = {
  easy: "bg-secondary text-secondary-foreground",
  medium: "bg-accent text-accent-foreground",
  hard: "bg-primary text-primary-foreground",
};

export function RecipeModal({ recipe, isOpen, onClose }: RecipeModalProps) {
  if (!recipe) return null;

  const country = COUNTRIES.find(
    (c) => c.name.toLowerCase() === recipe.country.toLowerCase()
  );

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto p-0 gap-0 bg-card border-none rounded-3xl">
        <div className="relative">
          {/* Hero Image */}
          <div className="relative h-64 sm:h-80 overflow-hidden rounded-t-3xl">
            <img
              src={recipe.image}
              alt={recipe.title}
              className="w-full h-full object-cover"
            />
            <div className="absolute inset-0 bg-gradient-to-t from-foreground/70 via-foreground/20 to-transparent" />

            {/* Back button */}
            <Button
              variant="ghost"
              size="icon"
              onClick={onClose}
              className="absolute top-4 left-4 bg-card/80 backdrop-blur-sm hover:bg-card rounded-full"
            >
              <ArrowLeft className="h-5 w-5" />
            </Button>

            {/* Title overlay */}
            <div className="absolute bottom-0 left-0 right-0 p-6">
              <div className="flex flex-wrap items-center gap-2 mb-3">
                <span className="bg-card/90 backdrop-blur-sm px-3 py-1 rounded-full text-sm font-medium flex items-center gap-1.5">
                  <span>{country?.flag}</span>
                  <span>{recipe.country}</span>
                </span>
                <span
                  className={`px-3 py-1 rounded-full text-xs font-semibold uppercase tracking-wide ${
                    difficultyColors[recipe.difficulty]
                  }`}
                >
                  {recipe.difficulty}
                </span>
                <span className="bg-card/90 backdrop-blur-sm px-3 py-1 rounded-full text-sm font-medium capitalize flex items-center gap-1.5">
                  <ChefHat className="h-3.5 w-3.5" />
                  {recipe.meal_type}
                </span>
              </div>
              <h2 className="font-display text-3xl sm:text-4xl font-bold text-card">
                {recipe.title}
              </h2>
            </div>
          </div>

          {/* Content */}
          <div className="p-6 sm:p-8 space-y-8">
            {/* Description */}
            <div>
              <p className="text-muted-foreground text-lg leading-relaxed">
                {recipe.description}
              </p>
            </div>

            {/* Ingredients */}
            {recipe.ingredients && recipe.ingredients.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 }}
              >
                <h3 className="font-display text-2xl font-semibold mb-4 flex items-center gap-2">
                  <span className="w-8 h-8 rounded-full bg-primary/10 flex items-center justify-center">
                    🥗
                  </span>
                  Ingredients
                </h3>
                <div className="bg-muted/50 rounded-2xl p-5">
                  <ul className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                    {recipe.ingredients.map((ingredient, index) => (
                      <motion.li
                        key={index}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: 0.2 + index * 0.05 }}
                        className="flex items-center justify-between bg-card rounded-xl px-4 py-3 shadow-sm"
                      >
                        <span className="font-medium text-foreground">
                          {ingredient.item}
                        </span>
                        <span className="text-muted-foreground text-sm bg-muted px-2 py-1 rounded-lg">
                          {ingredient.quantity}
                        </span>
                      </motion.li>
                    ))}
                  </ul>
                </div>
              </motion.div>
            )}

            {/* Steps */}
            {recipe.instructions && recipe.instructions.length > 0 && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.2 }}
              >
                <h3 className="font-display text-2xl font-semibold mb-4 flex items-center gap-2">
                  <span className="w-8 h-8 rounded-full bg-secondary/20 flex items-center justify-center">
                    📝
                  </span>
                  Instructions
                </h3>
                <ol className="space-y-4">
                  {recipe.instructions.map((step, index) => (
                    <motion.li
                      key={index}
                      initial={{ opacity: 0, x: -10 }}
                      animate={{ opacity: 1, x: 0 }}
                      transition={{ delay: 0.3 + index * 0.1 }}
                      className="flex gap-4"
                    >
                      <span className="flex-shrink-0 w-8 h-8 rounded-full bg-primary text-primary-foreground flex items-center justify-center font-bold text-sm">
                        {index + 1}
                      </span>
                      <p className="text-foreground leading-relaxed pt-1">
                        {step}
                      </p>
                    </motion.li>
                  ))}
                </ol>
              </motion.div>
            )}
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
