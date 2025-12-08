export interface Ingredient {
  item: string;
  quantity: string;
}

export interface Recipe {
  id: string;
  title: string;
  country: string;
  difficulty: "easy" | "medium" | "hard";
  meal_type: "breakfast" | "lunch" | "dinner" | "dessert";
  image: string;
  description: string;
  ingredients?: Ingredient[];
  instructions?: string[];
}

export interface SearchFilters {
  country?: string;
  difficulty?: string;
  meal_type?: string;
}

export interface SearchRequest {
  query: string;
  filters: SearchFilters;
}

export const COUNTRIES = [
  { code: "MA", name: "Morocco", flag: "🇲🇦" },
  { code: "IT", name: "Italy", flag: "🇮🇹" },
  { code: "PL", name: "Poland", flag: "🇵🇱" },
  { code: "SY", name: "Syria", flag: "🇸🇾" },
  { code: "KR", name: "South Korea", flag: "🇰🇷" },
  { code: "JP", name: "Japan", flag: "🇯🇵" },
  { code: "IN", name: "India", flag: "🇮🇳" },
  { code: "FR", name: "France", flag: "🇫🇷" },
  { code: "MX", name: "Mexico", flag: "🇲🇽" },
  { code: "GB", name: "England", flag: "🇬🇧" },
] as const;

export const DIFFICULTIES = [
  { label: "Easy", value: "easy", emoji: "🟢" },
  { label: "Medium", value: "medium", emoji: "🟡" },
  { label: "Hard", value: "hard", emoji: "🔴" },
] as const;

export const MEAL_TYPES = [
  { label: "Breakfast", value: "breakfast", emoji: "🍳" },
  { label: "Lunch", value: "lunch", emoji: "🍽️" },
  { label: "Dinner", value: "dinner", emoji: "🌙" },
  { label: "Dessert", value: "dessert", emoji: "🍰" },
] as const;
