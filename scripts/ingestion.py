def main(source_type: str, source_path: str):
    """
    Ingestion - connecteurs sources
    """
    import json
    from datetime import datetime
    
    # Simuler l'ingestion
    raw_payload = {
        "source_type": source_type,
        "source_path": source_path,
        "ingested_at": datetime.now().isoformat(),
        "data": {"sample": "data"}
    }
    
    return {
        "status": "success",
        "raw_payload": raw_payload,
        "step": "ingestion"
    }