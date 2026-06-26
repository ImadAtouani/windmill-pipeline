"""
Envoi des métriques du pipeline à l'OTEL Collector
À ajouter comme dernière étape du Flow
"""
import time
import json
import urllib.request
import urllib.error
from datetime import datetime
from pymongo import MongoClient

def main():
    OTEL_COLLECTOR_URL = "http://otel_collector:4318/v1/metrics"
    
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
        
        print(f"📊 Métriques: raw={raw}, normalized={norm}, rejected={rej}")
        
        # Envoyer les métriques (simplifié)
        metrics = [
            ("pipeline.raw.data.total", raw, {"type": "raw"}),
            ("pipeline.normalized.data.total", norm, {"type": "normalized"}),
            ("pipeline.rejected.data.total", rej, {"type": "rejected"}),
            ("pipeline.raw.pending.total", pending, {"status": "pending"}),
            ("pipeline.raw.processing.total", processing, {"status": "processing"}),
        ]
        
        for name, value, attrs in metrics:
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
                            "description": "",
                            "unit": "1",
                            "gauge": {
                                "dataPoints": [{
                                    "attributes": [
                                        {"key": k, "value": {"stringValue": str(v)}} 
                                        for k, v in attrs.items()
                                    ],
                                    "timeUnixNano": str(int(time.time() * 1e9)),
                                    "asDouble": float(value)
                                }]
                            }
                        }]
                    }]
                }]
            }
            
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                OTEL_COLLECTOR_URL,
                data=data,
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    print(f"✅ {name}={value}")
        
        for source in sources:
            source_type = source['_id'] or 'unknown'
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
                            "name": "pipeline.raw.by.source",
                            "description": "",
                            "unit": "1",
                            "gauge": {
                                "dataPoints": [{
                                    "attributes": [
                                        {"key": "source_type", "value": {"stringValue": source_type}}
                                    ],
                                    "timeUnixNano": str(int(time.time() * 1e9)),
                                    "asDouble": float(source["count"])
                                }]
                            }
                        }]
                    }]
                }]
            }
            
            data = json.dumps(payload).encode('utf-8')
            req = urllib.request.Request(
                OTEL_COLLECTOR_URL,
                data=data,
                headers={'Content-Type': 'application/json'},
                method='POST'
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                if response.status == 200:
                    print(f"✅ pipeline.raw.by.source{{source_type={source_type}}}={source['count']}")
        
        return {"status": "success", "step": "send_metrics"}
        
    except Exception as e:
        return {"status": "error", "message": str(e), "step": "send_metrics"}