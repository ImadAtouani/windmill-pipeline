def main(parsed_data: dict):
    """
    Mapping - champs source → modèle cible
    """
    import json
    
    try:
        print("=" * 60)
        print("📥 Données reçues dans mapping:")
        print(f"  - parsed_data keys: {list(parsed_data.keys()) if isinstance(parsed_data, dict) else 'Not a dict'}")
        print("=" * 60)
        
        # Récupérer les records
        if isinstance(parsed_data, dict) and "records" in parsed_data:
            records = parsed_data["records"]
            print(f"✅ Utilisation de parsed_data['records']")
        else:
            records = parsed_data
            print(f"✅ Utilisation de parsed_data directement")
        
        if not isinstance(records, dict):
            return {
                "status": "error",
                "message": f"records is not a dict: {type(records)}",
                "step": "mapping"
            }
        
        # Mapping des champs
        mapping_rules = {
            "id": "user_id",
            "name": "full_name",
            "amount": "amount",
            "date": "transaction_date",
            "country": "country_code",
            "email": "email_address"
        }
        
        mapped_data = {}
        for source, target in mapping_rules.items():
            if source in records:
                mapped_data[target] = records[source]
            else:
                print(f"⚠️ Champ source manquant: {source}")
        
        print(f"📊 Données mappées: {json.dumps(mapped_data, indent=2)}")
        print("=" * 60)
        
        return {
            "status": "success",
            "mapped_data": mapped_data,
            "step": "mapping"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "step": "mapping"
        }