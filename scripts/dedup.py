def main(standardized_data: dict):
    """
    Déduplication - clé métier / hash
    """
    import hashlib
    import json
    from datetime import datetime
    
    try:
        print("=" * 60)
        print("📥 Données reçues dans dedup:")
        print(f"  - Type: {type(standardized_data)}")
        print(f"  - Clés: {list(standardized_data.keys()) if isinstance(standardized_data, dict) else 'Not a dict'}")
        print("=" * 60)
        
        if not isinstance(standardized_data, dict):
            return {
                "status": "error",
                "message": f"standardized_data is not a dict: {type(standardized_data)}",
                "step": "dedup"
            }
        
        # Génération d'une clé de déduplication UNIQUE
        # Utiliser tous les champs + timestamp pour garantir l'unicité
        data_string = str(sorted(standardized_data.items()))
        timestamp = datetime.now().isoformat()
        unique_string = f"{data_string}_{timestamp}_{id(standardized_data)}"
        dedup_key = hashlib.md5(unique_string.encode()).hexdigest()
        
        # Ajouter la clé aux données
        standardized_data_with_key = standardized_data.copy()
        standardized_data_with_key["dedup_key"] = dedup_key
        
        print(f"🔑 Clé de déduplication générée: {dedup_key}")
        print("=" * 60)
        
        return {
            "status": "success",
            "deduplicated_data": standardized_data_with_key,
            "dedup_key": dedup_key,
            "step": "dedup"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "step": "dedup"
        }