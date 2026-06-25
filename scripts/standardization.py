def main(typed_data: dict):
    """
    Standardisation - noms, unités, devises, pays
    """
    standardized = typed_data.copy()
    
    # Normalisation des unités
    if "amount" in standardized:
        standardized["amount_usd"] = standardized["amount"] * 1.08
    
    # Standardisation des pays
    country_mapping = {"FR": "France", "DE": "Germany", "US": "United States"}
    if "country" in standardized:
        standardized["country_name"] = country_mapping.get(
            standardized["country"], 
            standardized["country"]
        )
    
    return {
        "status": "success",
        "standardized_data": standardized,
        "step": "standardization"
    }