"""
Envoi des métriques du pipeline à l'OTEL Collector
"""
import time
import json
import requests
from datetime import datetime

OTEL_COLLECTOR_URL = "http://otel_collector:4318/v1/metrics"

def send_metric(name, value, unit="1", description="", attributes=None):
    """Envoie une métrique à l'OTEL Collector"""
    if attributes is None:
        attributes = {}
    
    payload = {
        "resourceMetrics": [{
            "resource": {
                "attributes": [
                    {"key": "service.name", "value": {"stringValue": "windmill-pipeline"}},
                    {"key": "service.version", "value": {"stringValue": "1.0.0"}}
                ]
            },
            "scopeMetrics": [{
                "scope": {"name": "pipeline.metrics", "version": "1.0.0"},
                "metrics": [{
                    "name": name,
                    "description": description,
                    "unit": unit,
                    "gauge": {
                        "dataPoints": [{
                            "attributes": [
                                {"key": k, "value": {"stringValue": str(v)}} 
                                for k, v in attributes.items()
                            ],
                            "timeUnixNano": str(int(time.time() * 1e9)),
                            "asDouble": float(value)
                        }]
                    }
                }]
            }]
        }]
    }
    
    try:
        response = requests.post(OTEL_COLLECTOR_URL, headers={"Content-Type": "application/json"}, json=payload, timeout=2)
        return response.status_code == 200
    except Exception as e:
        print(f"⚠️ Erreur envoi métrique: {e}")
        return False

def update_pipeline_metrics():
    """Met à jour les métriques du pipeline"""
    try:
        from pymongo import MongoClient
        client = MongoClient("mongodb://admin:changeme@mongodb:27017/", serverSelectionTimeoutMS=5000)
        db = client["data_pipeline"]
        
        raw = db.raw_data.count_documents({})
        norm = db.normalized_data.count_documents({})
        rej = db.rejected_data.count_documents({})
        pending = db.raw_data.count_documents({"status": "pending"})
        processing = db.raw_data.count_documents({"status": "processing"})
        
        sources = list(db.raw_data.aggregate([
            {"$group": {"_id": "$source_type", "count": {"$sum": 1}}}
        ]))
        
        # Envoyer les métriques
        send_metric("pipeline.raw.data.total", raw, "1", "Total raw data", {"type": "raw"})
        send_metric("pipeline.normalized.data.total", norm, "1", "Total normalized data", {"type": "normalized"})
        send_metric("pipeline.rejected.data.total", rej, "1", "Total rejected data", {"type": "rejected"})
        send_metric("pipeline.raw.pending.total", pending, "1", "Pending data", {"status": "pending"})
        send_metric("pipeline.raw.processing.total", processing, "1", "Processing data", {"status": "processing"})
        
        for source in sources:
            source_type = source['_id'] or 'unknown'
            send_metric("pipeline.raw.by.source", source["count"], "1", "Data by source", {"source_type": source_type})
        
        print(f"✅ Métriques envoyées: raw={raw}, normalized={norm}, rejected={rej}")
        return True
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return False

if __name__ == "__main__":
    update_pipeline_metrics()