from typing import Literal, Dict, Any

def main(raw_data: Dict[str, Any], format: Literal["csv", "excel", "json", "html", "parquet"] = "json"):
    """
    Parsing - CSV, Excel, JSON, HTML, Parquet
    """
    import json
    
    try:
        print("=" * 60)
        print("📥 Données reçues dans parsing:")
        print(f"  - format: {format}")
        print(f"  - raw_data keys: {list(raw_data.keys()) if isinstance(raw_data, dict) else 'Not a dict'}")
        print("=" * 60)
        
        if not isinstance(raw_data, dict):
            return {
                "status": "error",
                "message": f"raw_data is not a dict: {type(raw_data)}",
                "step": "parsing"
            }
        
        # Les données sont directement dans raw_data
        records = raw_data
        
        print(f"📊 Données parsées: {json.dumps(records, indent=2)}")
        print("=" * 60)
        
        parsed_data = {
            "format": format,
            "records": records,
            "record_count": len(records) if isinstance(records, dict) else 0
        }
        
        return {
            "status": "success",
            "parsed_data": parsed_data,
            "step": "parsing"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "step": "parsing"
        }