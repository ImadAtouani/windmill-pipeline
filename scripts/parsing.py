from typing import Literal, Dict, Any

def main(
    raw_data: Dict[str, Any],
    format: Literal["csv", "excel", "json", "html", "parquet"] = "json"
):
    """
    Parsing - CSV, Excel, JSON, HTML, Parquet
    """
    import json
    
    # Simulation de parsing
    parsed_data = {
        "format": format,
        "records": raw_data.get("data", {}),
        "record_count": 1
    }
    
    return {
        "status": "success",
        "parsed_data": parsed_data,
        "step": "parsing"
    }