def build_text(doc):
    """Concatène tous les champs utiles pour les embeddings"""
    return " ".join([
        doc.get("title", ""),
        doc.get("description", ""),
        " ".join([i.get("item","") for i in doc.get("ingredients", [])]),
        " ".join(doc.get("instructions", [])),
        " ".join(doc.get("tags", [])),
        doc.get("category", ""),
        doc.get("country", ""),
        doc.get("difficulty", ""),
        str(doc.get("servings", "")),
        doc.get("cooking_method", ""),
        doc.get("meal_type", "")
    ])
