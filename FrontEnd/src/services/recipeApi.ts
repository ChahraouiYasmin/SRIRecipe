import { Recipe, SearchRequest } from "@/types/recipe";

const API_URL = "http://localhost:5000/api";

export async function searchRecipes(data: SearchRequest): Promise<Recipe[]> {
  const body = {
    query: data.query || "",
    country: data.filters?.country || "",
    difficulty: data.filters?.difficulty || "",
    meal_type: data.filters?.meal_type || "",
  };

  const res = await fetch(`${API_URL}/recipes/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });

  const json = await res.json();

  if (!res.ok) {
    console.error("Backend error:", json);
    throw new Error(json.error || "Failed to search recipes");
  }

  return json.recipes ?? [];
}
/* -----------------------------------------------------------
   FILTER OPTIONS
------------------------------------------------------------ */
export async function getFilters() {
  const res = await fetch(`${API_URL}/recipes/filters`);
  if (!res.ok) throw new Error("Failed to load filters");
  return res.json();
}


export async function getRecipeById(id: string): Promise<Recipe> {
  const res = await fetch(`${API_URL}/recipes/${id}`);
  if (!res.ok) throw new Error("Recipe not found");

  const json = await res.json();
  return json.recipe;
}


export async function getRandomRecipes(count = 5): Promise<Recipe[]> {
  const res = await fetch(`${API_URL}/recipes/random?count=${count}`);
  if (!res.ok) throw new Error("Failed to fetch random recipes");

  const json = await res.json();
  return json.recipes ?? [];
}

export async function getAllRecipes(page = 1, pageSize = 20): Promise<Recipe[]> {
  const res = await fetch(`${API_URL}/recipes/all?page=${page}&page_size=${pageSize}`);
  if (!res.ok) throw new Error("Failed to fetch recipes");

  const json = await res.json();
  return json.recipes ?? [];
}

export async function findSimilarRecipes(recipeId: string, topK = 5): Promise<Recipe[]> {
  const res = await fetch(`${API_URL}/recipes/similar`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ recipe_id: recipeId, top_k: topK }),
  });

  if (!res.ok) throw new Error("Failed to fetch similar recipes");

  const json = await res.json();
  return json.recipes ?? [];
}
