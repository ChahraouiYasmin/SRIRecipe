import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { COUNTRIES, DIFFICULTIES, MEAL_TYPES, SearchFilters } from "@/types/recipe";
import { X } from "lucide-react";
import { Button } from "@/components/ui/button";

interface FilterBarProps {
  filters: SearchFilters;
  onChange: (filters: SearchFilters) => void;
}

export function FilterBar({ filters, onChange }: FilterBarProps) {
  const hasFilters = filters.country || filters.difficulty || filters.meal_type;

  const clearFilters = () => {
    onChange({ country: undefined, difficulty: undefined, meal_type: undefined });
  };

  return (
    <div className="flex flex-wrap items-center justify-center gap-3 w-full max-w-3xl mx-auto">
      <Select
        value={filters.country || "all"}
        onValueChange={(value) =>
          onChange({ ...filters, country: value === "all" ? undefined : value })
        }
      >
        <SelectTrigger className="w-[180px] h-11 rounded-full border-2 bg-card shadow-card hover:shadow-card-hover transition-all duration-300">
          <SelectValue placeholder="Country" />
        </SelectTrigger>
        <SelectContent className="bg-card border-2 border-border rounded-xl shadow-elevated">
          <SelectItem value="all" className="rounded-lg">All Countries</SelectItem>
          {COUNTRIES.map((country) => (
            <SelectItem key={country.code} value={country.name} className="rounded-lg">
              <span className="flex items-center gap-2">
                <span className="text-lg">{country.flag}</span>
                <span>{country.name}</span>
              </span>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <Select
  value={filters.difficulty || "all"}
  onValueChange={(value) =>
    onChange({ ...filters, difficulty: value === "all" ? undefined : value })
  }
>
  <SelectTrigger className="w-[160px] h-11 rounded-full border-2 bg-card shadow-card hover:shadow-card-hover transition-all duration-300">
    <SelectValue placeholder="Difficulty" />
  </SelectTrigger>
  <SelectContent className="bg-card border-2 border-border rounded-xl shadow-elevated">
    <SelectItem value="all" className="rounded-lg">All Levels</SelectItem>
    {DIFFICULTIES.map((diff) => (
      <SelectItem key={diff.value} value={diff.value} className="rounded-lg">
        <span className="flex items-center gap-2">
          <span>{diff.emoji}</span>
          <span>{diff.label}</span>
        </span>
      </SelectItem>
    ))}
  </SelectContent>
</Select>


      <Select
  value={filters.meal_type || "all"}
  onValueChange={(value) =>
    onChange({ ...filters, meal_type: value === "all" ? undefined : value })
  }
>
  <SelectTrigger className="w-[160px] h-11 rounded-full border-2 bg-card shadow-card hover:shadow-card-hover transition-all duration-300">
    <SelectValue placeholder="Meal Type" />
  </SelectTrigger>
  <SelectContent className="bg-card border-2 border-border rounded-xl shadow-elevated">
    <SelectItem value="all" className="rounded-lg">All Meals</SelectItem>
    {MEAL_TYPES.map((meal) => (
      <SelectItem key={meal.value} value={meal.value} className="rounded-lg">
        <span className="flex items-center gap-2">
          <span>{meal.emoji}</span>
          <span>{meal.label}</span>
        </span>
      </SelectItem>
    ))}
  </SelectContent>
</Select>


      {hasFilters && (
        <Button
          variant="ghost"
          size="sm"
          onClick={clearFilters}
          className="h-11 px-4 rounded-full text-muted-foreground hover:text-foreground"
        >
          <X className="h-4 w-4 mr-1" />
          Clear
        </Button>
      )}
    </div>
  );
}
