"""
Envoi des métriques du pipeline à l'OTEL Collector
Ce script est dans un dossier séparé pour éviter les conflits avec typing.py
"""
import time
import json
import urllib.request
import urllib.error
from datetime import datetime
from pymongo import MongoClient

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
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            OTEL_COLLECTOR_URL,
            data=data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status == 200:
                print(f"✅ Métrique envoyée: {name}={value}")
                return True
            else:
                print(f"⚠️ Erreur envoi {name}: {response.status}")
                return False
    except Exception as e:
        print(f"⚠️ Erreur envoi métrique {name}: {e}")
        return False

def get_pipeline_metrics():
    """Récupère les métriques du pipeline depuis MongoDB"""
    try:
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
        
        return {
            "raw": raw,
            "normalized": norm,
            "rejected": rej,
            "pending": pending,
            "processing": processing,
            "sources": sources
        }
    except Exception as e:
        print(f"❌ Erreur MongoDB: {e}")
        return None

def update_pipeline_metrics():
    """Met à jour les métriques du pipeline"""
    metrics = get_pipeline_metrics()
    if not metrics:
        return False
    
    print(f"📊 Métriques: raw={metrics['raw']}, normalized={metrics['normalized']}, rejected={metrics['rejected']}")
    
    # Envoyer les métriques
    send_metric("pipeline.raw.data.total", metrics["raw"], "1", "Total raw data", {"type": "raw"})
    send_metric("pipeline.normalized.data.total", metrics["normalized"], "1", "Total normalized data", {"type": "normalized"})
    send_metric("pipeline.rejected.data.total", metrics["rejected"], "1", "Total rejected data", {"type": "rejected"})
    send_metric("pipeline.raw.pending.total", metrics["pending"], "1", "Pending data", {"status": "pending"})
    send_metric("pipeline.raw.processing.total", metrics["processing"], "1", "Processing data", {"status": "processing"})
    
    for source in metrics["sources"]:
        source_type = source['_id'] or 'unknown'
        send_metric("pipeline.raw.by.source", source["count"], "1", "Data by source", {"source_type": source_type})
    
    return True

if __name__ == "__main__":
    update_pipeline_metrics()