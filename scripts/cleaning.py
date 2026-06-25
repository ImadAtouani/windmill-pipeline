def main(mapped_data: dict):
    """
    Nettoyage - trim, encodage, formats
    """
    cleaned = {}
    
    for key, value in mapped_data.items():
        if isinstance(value, str):
            cleaned[key] = value.strip().encode('utf-8').decode('utf-8')
        else:
            cleaned[key] = value
    
    return {
        "status": "success",
        "cleaned_data": cleaned,
        "step": "cleaning"
    }