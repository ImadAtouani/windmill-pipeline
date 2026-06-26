def main(validated_data: dict):
    """
    Enrichissement - métadonnées, source, horodatage
    """
    import json
    from datetime import datetime
    
    try:
        print("=" * 60)
        print("📥 Données reçues dans enrichment:")
        print(f"  - Type: {type(validated_data)}")
        print(f"  - Clés: {list(validated_data.keys()) if isinstance(validated_data, dict) else 'Not a dict'}")
        print("=" * 60)
        
        if not isinstance(validated_data, dict):
            return {
                "status": "error",
                "message": f"validated_data is not a dict: {type(validated_data)}",
                "step": "enrichment"
            }
        
        # Enrichissement des données
        enriched = validated_data.copy()
        enriched.update({
            "enriched_at": datetime.now().isoformat(),
            "pipeline_version": "1.0.0",
            "source_system": "windmill_pipeline",
            "processing_timestamp": datetime.now().timestamp()
        })
        
        print(f"📊 Données enrichies avec:")
        print(f"  - enriched_at: {enriched['enriched_at']}")
        print(f"  - pipeline_version: {enriched['pipeline_version']}")
        print(f"  - source_system: {enriched['source_system']}")
        print("=" * 60)
        
        return {
            "status": "success",
            "enriched_data": enriched,
            "step": "enrichment"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
            "step": "enrichment"
        }