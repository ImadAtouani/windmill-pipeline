def main(typed_data: dict):
    """
    Standardisation - noms, unités, devises, pays
    """
    import json
    
    try:
        print("=" * 60)
        print("📥 Données reçues dans standardization:")
        print(f"  - Type: {type(typed_data)}")
        print(f"  - Clés: {list(typed_data.keys()) if isinstance(typed_data, dict) else 'Not a dict'}")
        print("=" * 60)
        
        if not isinstance(typed_data, dict):
            return {
                "status": "error",
                "message": f"typed_data is not a dict: {type(typed_data)}",
                "step": "standardization"
            }
        
        print(f"📊 Données avant standardisation: {json.dumps(typed_data, indent=2)}")
        print("=" * 60)
        
        standardized = typed_data.copy()
        std_stats = {
            "countries_normalized": 0,
            "currencies_converted": 0,
            "units_normalized": 0
        }
        
        # Standardisation des pays
        country_mapping = {
            "FR": "France",
            "DE": "Germany",
            "US": "United States",
            "UK": "United Kingdom",
            "CA": "Canada",
            "ES": "Spain",
            "IT": "Italy",
            "JP": "Japan",
            "BR": "Brazil",
            "AU": "Australia"
        }
        
        if "country" in standardized:
            if standardized["country"] in country_mapping:
                standardized["country_name"] = country_mapping[standardized["country"]]
                std_stats["countries_normalized"] += 1
                print(f"  ✅ country: '{standardized['country']}' → '{standardized['country_name']}'")
            elif "country_code" in standardized and standardized["country_code"] in country_mapping:
                standardized["country_name"] = country_mapping[standardized["country_code"]]
                std_stats["countries_normalized"] += 1
                print(f"  ✅ country_code: '{standardized['country_code']}' → '{standardized['country_name']}'")
        
        # Standardisation des devises (conversion EUR → USD)
        if "amount" in standardized:
            standardized["amount_usd"] = standardized["amount"] * 1.08
            std_stats["currencies_converted"] += 1
            print(f"  ✅ amount: {standardized['amount']} EUR → {standardized['amount_usd']} USD")
        
        print("=" * 60)
        print(f"📊 Statistiques de standardisation: {json.dumps(std_stats, indent=2)}")
        print(f"📊 Données après standardisation: {json.dumps(standardized, indent=2)}")
        print("=" * 60)
        
        return {
            "status": "success",
            "standardized_data": standardized,
            "standardization_stats": std_stats,
            "step": "standardization"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "step": "standardization"
        }