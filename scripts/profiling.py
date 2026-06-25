from typing import Dict, Any

def main(raw_data: Dict[str, Any]):
    """
    Profilage - types, colonnes, valeurs nulles
    """
    import json
    
    data = raw_data.get("data", {})
    
    profile = {
        "column_count": len(data) if isinstance(data, dict) else 0,
        "data_types": {k: type(v).__name__ for k, v in data.items()},
        "null_values": {k: v is None for k, v in data.items()}
    }
    
    return {
        "status": "success",
        "profile": profile,
        "step": "profiling"
    }