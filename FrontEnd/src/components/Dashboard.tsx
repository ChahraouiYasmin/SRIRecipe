import { motion } from "framer-motion";
import { UtensilsCrossed, Globe, ChefHat, TrendingUp } from "lucide-react";
import { Recipe } from "@/types/recipe";

interface DashboardProps {
  recipes: Recipe[];
  isVisible: boolean;
}

export function Dashboard({ recipes, isVisible }: DashboardProps) {
  if (!isVisible) return null;

  const stats = {
    total: recipes.length,
    countries: new Set(recipes.map((r) => r.country)).size,
    difficulties: {
      easy: recipes.filter((r) => r.difficulty === "easy").length,
      medium: recipes.filter((r) => r.difficulty === "medium").length,
      hard: recipes.filter((r) => r.difficulty === "hard").length,
    },
  };

  const topCountries = Object.entries(
    recipes.reduce((acc, recipe) => {
      acc[recipe.country] = (acc[recipe.country] || 0) + 1;
      return acc;
    }, {} as Record<string, number>)
  )
    .sort((a, b) => b[1] - a[1])
    .slice(0, 5);

  const statCards = [
    {
      icon: UtensilsCrossed,
      label: "Total Recipes",
      value: stats.total,
      color: "bg-primary/10 text-primary",
      iconColor: "text-primary",
    },
    {
      icon: Globe,
      label: "Countries",
      value: stats.countries,
      color: "bg-secondary/10 text-secondary-foreground",
      iconColor: "text-secondary-foreground",
    },
    {
      icon: ChefHat,
      label: "Easy Recipes",
      value: stats.difficulties.easy,
      color: "bg-green-500/10 text-green-600",
      iconColor: "text-green-600",
    },
    {
      icon: TrendingUp,
      label: "Most Popular",
      value: topCountries[0]?.[0] || "N/A",
      color: "bg-accent/10 text-accent-foreground",
      iconColor: "text-accent-foreground",
      isText: true,
    },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="mb-12"
    >
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {statCards.map((stat, index) => (
          <motion.div
            key={index}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: index * 0.1 }}
            className="bg-card rounded-2xl p-6 shadow-card hover:shadow-card-hover transition-all duration-300"
          >
            <div className={`w-12 h-12 rounded-xl ${stat.color} flex items-center justify-center mb-4`}>
              <stat.icon className={`w-6 h-6 ${stat.iconColor}`} />
            </div>
            <p className="text-sm text-muted-foreground mb-1">{stat.label}</p>
            <p className="text-2xl font-bold text-foreground">
              {stat.isText ? stat.value : stat.value.toLocaleString()}
            </p>
          </motion.div>
        ))}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.4 }}
          className="bg-card rounded-2xl p-6 shadow-card"
        >
          <h3 className="font-semibold text-lg mb-4 flex items-center gap-2">
            <span>📊</span>
            Difficulty Distribution
          </h3>
          <div className="space-y-3">
            {Object.entries(stats.difficulties).map(([level, count]) => {
              const percentage = stats.total > 0 ? (count / stats.total) * 100 : 0;
              const colors = {
                easy: "bg-green-500",
                medium: "bg-yellow-500",
                hard: "bg-red-500",
              };
              return (
                <div key={level}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="capitalize text-muted-foreground">{level}</span>
                    <span className="font-medium">{count}</span>
                  </div>
                  <div className="h-2 bg-muted rounded-full overflow-hidden">
                    <div
                      className={`h-full ${colors[level as keyof typeof colors]} transition-all duration-500`}
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </motion.div>

        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.5 }}
          className="bg-card rounded-2xl p-6 shadow-card"
        >
          <h3 className="font-semibold text-lg mb-4 flex items-center gap-2">
            <span>🌍</span>
            Top Countries
          </h3>
          <div className="space-y-3">
            {topCountries.map(([country, count], index) => {
              const percentage = stats.total > 0 ? (count / stats.total) * 100 : 0;
              return (
                <div key={country}>
                  <div className="flex justify-between text-sm mb-1">
                    <span className="text-muted-foreground">
                      {index + 1}. {country}
                    </span>
                    <span className="font-medium">{count}</span>
                  </div>
                  <div className="h-2 bg-muted rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary transition-all duration-500"
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </motion.div>
      </div>
    </motion.div>
  );
}