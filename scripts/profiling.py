def main(raw_data: dict):
    """
    Profilage - Analyse des types, colonnes, valeurs nulles
    """
    import json
    
    try:
        print("=" * 60)
        print("📥 Données reçues dans profiling:")
        print(f"  - Type: {type(raw_data)}")
        print(f"  - Clés: {list(raw_data.keys()) if isinstance(raw_data, dict) else 'Not a dict'}")
        print("=" * 60)
        
        if not isinstance(raw_data, dict):
            return {
                "status": "error",
                "message": f"raw_data is not a dict: {type(raw_data)}",
                "step": "profiling"
            }
        
        data = raw_data
        
        print(f"📊 Données à profiler: {json.dumps(data, indent=2)}")
        print("=" * 60)
        
        column_count = len(data)
        data_types = {k: type(v).__name__ for k, v in data.items()}
        null_values = {k: v is None for k, v in data.items()}
        
        return {
            "status": "success",
            "profile": {
                "column_count": column_count,
                "data_types": data_types,
                "null_values": null_values,
                "columns": list(data.keys())
            },
            "step": "profiling"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "step": "profiling"
        }