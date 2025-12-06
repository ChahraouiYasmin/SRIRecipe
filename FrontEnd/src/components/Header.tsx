import { UtensilsCrossed } from "lucide-react";
import { motion } from "framer-motion";

export function Header() {
  return (
    <header className="text-center mb-10">
      <motion.div
        initial={{ opacity: 0, y: -20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="flex items-center justify-center gap-3 mb-4"
      >
        <div className="w-12 h-12 rounded-2xl bg-primary flex items-center justify-center shadow-lg">
          <UtensilsCrossed className="w-6 h-6 text-primary-foreground" />
        </div>
      </motion.div>

      <motion.h1
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.1 }}
        className="font-display text-4xl sm:text-5xl lg:text-6xl font-bold text-foreground mb-4"
      >
        Recipe Semantic Search
      </motion.h1>

      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ duration: 0.5, delay: 0.2 }}
        className="text-muted-foreground text-lg max-w-2xl mx-auto"
      >
        Discover delicious recipes from around the world using natural language search
      </motion.p>
    </header>
  );
}
