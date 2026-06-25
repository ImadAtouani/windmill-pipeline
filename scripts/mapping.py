def main(parsed_data: dict):
    """
    Mapping - champs source → modèle cible
    """
    # Exemple de mapping
    mapping_rules = {
        "source_field": "target_field",
        "name": "full_name",
        "id": "user_id"
    }
    
    mapped = {}
    for source, target in mapping_rules.items():
        if source in parsed_data.get("records", {}):
            mapped[target] = parsed_data["records"][source]
    
    return {
        "status": "success",
        "mapped_data": mapped,
        "step": "mapping"
    }