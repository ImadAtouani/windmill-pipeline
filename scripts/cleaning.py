def main(mapped_data: dict):
    """
    Nettoyage - trim, encodage, formats
    """
    import json
    
    try:
        print("=" * 60)
        print("📥 Données reçues dans cleaning:")
        print(f"  - Type: {type(mapped_data)}")
        print(f"  - Clés: {list(mapped_data.keys()) if isinstance(mapped_data, dict) else 'Not a dict'}")
        print("=" * 60)
        
        if not isinstance(mapped_data, dict):
            return {
                "status": "error",
                "message": f"mapped_data is not a dict: {type(mapped_data)}",
                "step": "cleaning"
            }
        
        print(f"📊 Données avant nettoyage: {json.dumps(mapped_data, indent=2)}")
        print("=" * 60)
        
        cleaned = {}
        cleaning_stats = {
            "trimmed": 0,
            "encoded": 0,
            "unchanged": 0
        }
        
        for key, value in mapped_data.items():
            if isinstance(value, str):
                # Trim
                trimmed = value.strip()
                if trimmed != value:
                    cleaning_stats["trimmed"] += 1
                
                # Encodage UTF-8
                encoded = trimmed.encode('utf-8').decode('utf-8')
                if encoded != trimmed:
                    cleaning_stats["encoded"] += 1
                else:
                    cleaning_stats["unchanged"] += 1
                
                cleaned[key] = encoded
            else:
                cleaned[key] = value
                cleaning_stats["unchanged"] += 1
        
        print(f"📊 Statistiques de nettoyage: {json.dumps(cleaning_stats, indent=2)}")
        print(f"📊 Données après nettoyage: {json.dumps(cleaned, indent=2)}")
        print("=" * 60)
        
        return {
            "status": "success",
            "cleaned_data": cleaned,
            "cleaning_stats": cleaning_stats,
            "step": "cleaning"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "step": "cleaning"
        }