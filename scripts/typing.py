from typing import Literal, Dict, Any

def main(
    cleaned_data: Dict[str, Any],
    date_format: str = "%Y-%m-%d"
):
    """
    Typage - date, nombre, booléen, enum
    """
    from datetime import datetime
    
    typed_data = {}
    
    for key, value in cleaned_data.items():
        if key == "date" and isinstance(value, str):
            try:
                typed_data[key] = datetime.strptime(value, date_format).isoformat()
            except:
                typed_data[key] = value
        elif key == "amount" and isinstance(value, (int, float)):
            typed_data[key] = float(value)
        else:
            typed_data[key] = value
    
    return {
        "status": "success",
        "typed_data": typed_data,
        "step": "typing"
    }