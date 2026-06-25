def main(standardized_data: dict):
    """
    Déduplication - clé métier / hash
    """
    import hashlib
    
    # Génération d'une clé de déduplication
    dedup_key = hashlib.md5(
        str(sorted(standardized_data.items())).encode()
    ).hexdigest()
    
    return {
        "status": "success",
        "deduplicated_data": standardized_data,
        "dedup_key": dedup_key,
        "step": "deduplication"
    }