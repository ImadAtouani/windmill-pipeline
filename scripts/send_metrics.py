"""
Envoi des métriques du pipeline à l'OTEL Collector
Métriques : Comptage, Latence, Erreurs, CPU, Mémoire
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


def main():
    """Met à jour toutes les métriques du pipeline"""
    
    try:
        client = MongoClient("mongodb://admin:changeme@mongodb:27017/", serverSelectionTimeoutMS=5000)
        db = client["data_pipeline"]
        
        # ============================================
        # 1. MÉTRIQUES DE COMPTAGE
        # ============================================
        raw = db.raw_data.count_documents({})
        norm = db.normalized_data.count_documents({})
        rej = db.rejected_data.count_documents({})
        pending = db.raw_data.count_documents({"status": "pending"})
        processing = db.raw_data.count_documents({"status": "processing"})
        
        sources = list(db.raw_data.aggregate([
            {"$group": {"_id": "$source_type", "count": {"$sum": 1}}}
        ]))
        
        print(f"📊 Métriques de comptage: raw={raw}, normalized={norm}, rejected={rej}")
        
        send_metric("pipeline.raw.data.total", raw, "1", "Total raw data", {"type": "raw"})
        send_metric("pipeline.normalized.data.total", norm, "1", "Total normalized data", {"type": "normalized"})
        send_metric("pipeline.rejected.data.total", rej, "1", "Total rejected data", {"type": "rejected"})
        send_metric("pipeline.raw.pending.total", pending, "1", "Pending data", {"status": "pending"})
        send_metric("pipeline.raw.processing.total", processing, "1", "Processing data", {"status": "processing"})
        
        for source in sources:
            source_type = source['_id'] or 'unknown'
            send_metric("pipeline.raw.by.source", source["count"], "1", "Data by source", {"source_type": source_type})
        
        # ============================================
        # 2. MÉTRIQUES DE LATENCE PAR TÂCHE
        # ============================================
        print("\n⏱️ Métriques de latence:")
        scripts = ["ingestion", "profiling", "parsing", "mapping", "cleaning", 
                   "typing", "standardization", "dedup", "validation", "enrichment", "mongodb_writer"]
        
        for script in scripts:
            last = db.script_metrics.find_one(
                {"script": script},
                sort=[("timestamp", -1)]
            )
            if last:
                duration = last.get("duration_ms", 0)
                status = last.get("status", "unknown")
                send_metric(
                    "pipeline.latency.last",
                    duration,
                    "ms",
                    f"Last execution duration for {script}",
                    {"script": script, "status": status}
                )
            
            # Durée moyenne
            avg_docs = list(db.script_metrics.find(
                {"script": script}
            ).sort("timestamp", -1).limit(10))
            
            if avg_docs:
                avg_duration = sum(d.get("duration_ms", 0) for d in avg_docs) / len(avg_docs)
                send_metric(
                    "pipeline.latency.avg",
                    round(avg_duration, 2),
                    "ms",
                    f"Average execution duration for {script}",
                    {"script": script}
                )
        
        # ============================================
        # 3. MÉTRIQUES D'ERREURS PAR TÂCHE
        # ============================================
        print("\n❌ Métriques d'erreurs:")
        
        for script in scripts:
            errors = db.script_metrics.count_documents({
                "script": script,
                "status": "error"
            })
            successes = db.script_metrics.count_documents({
                "script": script,
                "status": "success"
            })
            
            send_metric(
                "pipeline.errors.total",
                errors,
                "1",
                f"Total errors for {script}",
                {"script": script}
            )
            send_metric(
                "pipeline.success.total",
                successes,
                "1",
                f"Total successes for {script}",
                {"script": script}
            )
            
            total = errors + successes
            if total > 0:
                error_rate = (errors / total) * 100
                send_metric(
                    "pipeline.error.rate",
                    round(error_rate, 2),
                    "%",
                    f"Error rate for {script}",
                    {"script": script}
                )
        
        # ============================================
        # 4. MÉTRIQUES CPU PAR TÂCHE
        # ============================================
        print("\n💻 Métriques CPU par tâche:")
        
        for script in scripts:
            last_cpu = db.script_metrics.find_one(
                {"script": script},
                sort=[("timestamp", -1)]
            )
            if last_cpu and "cpu_percent" in last_cpu:
                send_metric(
                    "pipeline.cpu.percent",
                    last_cpu["cpu_percent"],
                    "%",
                    f"CPU usage for {script}",
                    {"script": script}
                )
            
            # CPU moyenne
            avg_cpu_docs = list(db.script_metrics.find(
                {"script": script, "cpu_percent": {"$exists": True}}
            ).sort("timestamp", -1).limit(10))
            
            if avg_cpu_docs:
                avg_cpu = sum(d.get("cpu_percent", 0) for d in avg_cpu_docs) / len(avg_cpu_docs)
                send_metric(
                    "pipeline.cpu.avg",
                    round(avg_cpu, 2),
                    "%",
                    f"Average CPU usage for {script}",
                    {"script": script}
                )
        
        # ============================================
        # 5. MÉTRIQUES MÉMOIRE PAR TÂCHE
        # ============================================
        print("\n💾 Métriques Mémoire par tâche:")
        
        for script in scripts:
            last_memory = db.script_metrics.find_one(
                {"script": script},
                sort=[("timestamp", -1)]
            )
            if last_memory and "memory_mb" in last_memory:
                send_metric(
                    "pipeline.memory.mb",
                    last_memory["memory_mb"],
                    "MB",
                    f"Memory usage for {script}",
                    {"script": script}
                )
            
            # Mémoire moyenne
            avg_memory_docs = list(db.script_metrics.find(
                {"script": script, "memory_mb": {"$exists": True}}
            ).sort("timestamp", -1).limit(10))
            
            if avg_memory_docs:
                avg_memory = sum(d.get("memory_mb", 0) for d in avg_memory_docs) / len(avg_memory_docs)
                send_metric(
                    "pipeline.memory.avg",
                    round(avg_memory, 2),
                    "MB",
                    f"Average memory usage for {script}",
                    {"script": script}
                )
        
        print("\n✅ Toutes les métriques envoyées avec succès !")
        return {"status": "success", "step": "send_metrics"}
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
        return {"status": "error", "message": str(e), "step": "send_metrics"}