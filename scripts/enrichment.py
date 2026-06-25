def main(validated_data: dict):
    """
    Enrichissement - métadonnées, source, horodatage
    """
    from datetime import datetime
    
    enriched = validated_data.copy()
    enriched.update({
        "enriched_at": datetime.now().isoformat(),
        "pipeline_version": "1.0.0",
        "source_system": "windmill_pipeline"
    })
    
    return {
        "status": "success",
        "enriched_data": enriched,
        "step": "enrichment"
    }