import time
import json
import os
from datetime import datetime
from pymongo import MongoClient


def get_cpu_usage():
    try:
        with open("/proc/stat", "r") as f:
            line = f.readline()
            parts = line.split()
            user = int(parts[1])
            nice = int(parts[2])
            system = int(parts[3])
            idle = int(parts[4])
            total = user + nice + system + idle
            return round(((total - idle) / total) * 100, 2) if total > 0 else 0
    except:
        return 0


def get_memory_mb():
    try:
        with open("/proc/self/status", "r") as f:
            for line in f:
                if line.startswith("VmRSS:"):
                    kb = int(line.split()[1])
                    return round(kb / 1024, 2)
    except:
        return 0


def main(typed_data: dict):
    """
    Standardisation - noms, unités, devises, pays
    """
    start_time = time.time()
    script_name = "standardization"

    try:
        print("=" * 60)
        print("📥 Données reçues dans standardization:")
        print(f"  - Type: {type(typed_data)}")
        print(
            f"  - Clés: {list(typed_data.keys()) if isinstance(typed_data, dict) else 'Not a dict'}"
        )
        print("=" * 60)

        if not isinstance(typed_data, dict):
            duration_ms = (time.time() - start_time) * 1000
            client = MongoClient("mongodb://admin:changeme@mongodb:27017/")
            db = client["data_pipeline"]
            db.script_metrics.insert_one(
                {
                    "script": script_name,
                    "duration_ms": duration_ms,
                    "status": "error",
                    "error": "typed_data is not a dict",
                    "cpu_percent": get_cpu_usage(),
                    "memory_mb": get_memory_mb(),
                    "timestamp": datetime.now().isoformat(),
                }
            )
            return {
                "status": "error",
                "message": f"typed_data is not a dict: {type(typed_data)}",
                "step": "standardization",
            }

        print(f"📊 Données avant standardisation: {json.dumps(typed_data, indent=2)}")
        print("=" * 60)

        standardized = typed_data.copy()
        std_stats = {
            "countries_normalized": 0,
            "currencies_converted": 0,
            "units_normalized": 0,
        }

        country_mapping = {
            "FR": "France",
            "DE": "Germany",
            "US": "United States",
            "UK": "United Kingdom",
            "CA": "Canada",
            "ES": "Spain",
            "IT": "Italy",
            "JP": "Japan",
            "BR": "Brazil",
            "AU": "Australia",
        }

        if "country" in standardized:
            if standardized["country"] in country_mapping:
                standardized["country_name"] = country_mapping[standardized["country"]]
                std_stats["countries_normalized"] += 1
                print(
                    f"  ✅ country: '{standardized['country']}' → '{standardized['country_name']}'"
                )
            elif (
                "country_code" in standardized
                and standardized["country_code"] in country_mapping
            ):
                standardized["country_name"] = country_mapping[
                    standardized["country_code"]
                ]
                std_stats["countries_normalized"] += 1
                print(
                    f"  ✅ country_code: '{standardized['country_code']}' → '{standardized['country_name']}'"
                )

        if "amount" in standardized:
            standardized["amount_usd"] = standardized["amount"] * 1.08
            std_stats["currencies_converted"] += 1
            print(
                f"  ✅ amount: {standardized['amount']} EUR → {standardized['amount_usd']} USD"
            )

        print("=" * 60)
        print(f"📊 Statistiques de standardisation: {json.dumps(std_stats, indent=2)}")
        print(f"📊 Données après standardisation: {json.dumps(standardized, indent=2)}")
        print("=" * 60)

        duration_ms = (time.time() - start_time) * 1000
        client = MongoClient("mongodb://admin:changeme@mongodb:27017/")
        db = client["data_pipeline"]
        db.script_metrics.insert_one(
            {
                "script": script_name,
                "duration_ms": duration_ms,
                "status": "success",
                "cpu_percent": get_cpu_usage(),
                "memory_mb": get_memory_mb(),
                "timestamp": datetime.now().isoformat(),
            }
        )

        return {
            "status": "success",
            "standardized_data": standardized,
            "standardization_stats": std_stats,
            "duration_ms": round(duration_ms, 2),
            "cpu_percent": get_cpu_usage(),
            "memory_mb": get_memory_mb(),
            "step": "standardization",
        }

    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        try:
            client = MongoClient("mongodb://admin:changeme@mongodb:27017/")
            db = client["data_pipeline"]
            db.script_metrics.insert_one(
                {
                    "script": script_name,
                    "duration_ms": duration_ms,
                    "status": "error",
                    "error": str(e)[:100],
                    "cpu_percent": get_cpu_usage(),
                    "memory_mb": get_memory_mb(),
                    "timestamp": datetime.now().isoformat(),
                }
            )
        except:
            pass
        return {"status": "error", "message": str(e), "step": "standardization"}