import time
import json
import os
from typing import Literal, Dict, Any
from datetime import datetime
from pymongo import MongoClient

def get_cpu_usage():
    try:
        with open('/proc/stat', 'r') as f:
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
        with open('/proc/self/status', 'r') as f:
            for line in f:
                if line.startswith('VmRSS:'):
                    kb = int(line.split()[1])
                    return round(kb / 1024, 2)
    except:
        return 0

def extract_data_from_html(html_data):
    """
    Extrait et formate les données HTML pour les rendre compatibles avec le mapping
    """
    result = {}
    
    if 'titles' in html_data and html_data['titles']:
        result['name'] = html_data['titles'][0]
    
    if 'tables' in html_data and html_data['tables']:
        table = html_data['tables'][0]
        if len(table) > 1:
            headers = table[0] if table else []
            values = table[1] if len(table) > 1 else []
            
            for i, header in enumerate(headers):
                header_lower = header.lower().strip()
                if i < len(values):
                    value = values[i]
                    if 'id' in header_lower or 'product' in header_lower:
                        result['id'] = value
                    elif 'name' in header_lower:
                        if 'name' not in result:
                            result['name'] = value
                    elif 'price' in header_lower or 'amount' in header_lower:
                        clean_price = value.replace('$', '').replace('€', '').replace(',', '').strip()
                        result['amount'] = clean_price
                    elif 'date' in header_lower:
                        result['date'] = value
                    elif 'country' in header_lower or 'origin' in header_lower:
                        result['country'] = value
                    elif 'email' in header_lower or 'contact' in header_lower:
                        result['email'] = value
    
    if not result and 'paragraphs' in html_data and html_data['paragraphs']:
        text = ' '.join(html_data['paragraphs'])
        import re
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
        if email_match:
            result['email'] = email_match.group()
        price_match = re.search(r'\$?(\d+\.?\d*)', text)
        if price_match:
            result['amount'] = price_match.group(1)
    
    if 'name' in result and 'id' not in result:
        result['id'] = 'HTML001'
    
    if 'email' in result and 'country' not in result:
        if '@' in result['email']:
            domain = result['email'].split('@')[1].lower()
            if 'fr' in domain:
                result['country'] = 'FR'
            elif 'de' in domain:
                result['country'] = 'DE'
            elif 'uk' in domain or 'co.uk' in domain:
                result['country'] = 'UK'
            elif 'ca' in domain:
                result['country'] = 'CA'
            else:
                result['country'] = 'US'
    
    if 'date' not in result:
        from datetime import datetime
        result['date'] = datetime.now().strftime('%Y-%m-%d')
    
    if 'email' not in result:
        result['email'] = 'no-email@example.com'
    
    return result

def main(raw_data, format: Literal["csv", "excel", "json", "html", "parquet"] = "json"):
    """
    Parsing - CSV, Excel, JSON, HTML, Parquet
    """
    start_time = time.time()
    script_name = "parsing"
    
    try:
        print("=" * 60)
        print("📥 Données reçues dans parsing:")
        print(f"  - format: {format}")
        print(f"  - raw_data type: {type(raw_data)}")
        
        if isinstance(raw_data, dict):
            print(f"  - raw_data keys: {list(raw_data.keys())}")
        elif isinstance(raw_data, list):
            print(f"  - raw_data length: {len(raw_data)}")
            if len(raw_data) > 0:
                print(f"  - Premier élément type: {type(raw_data[0])}")
        else:
            print(f"  - raw_data value: {raw_data}")
        print("=" * 60)
        
        # Gestion des différents types de données
        if isinstance(raw_data, list):
            if len(raw_data) == 0:
                records = {"empty": True, "count": 0}
            else:
                # Prendre le premier élément de la liste
                records = raw_data[0]
                print(f"📊 Liste de {len(raw_data)} éléments, utilisation du premier")
        elif isinstance(raw_data, dict):
            records = raw_data
        else:
            records = {"value": raw_data}
        
        # Si c'est du HTML et que les clés caractéristiques sont présentes
        if format == 'html' or (isinstance(records, dict) and any(k in records for k in ['titles', 'paragraphs', 'tables'])):
            print("🔄 Détection de données HTML, extraction en cours...")
            records = extract_data_from_html(records)
            print(f"📊 Données extraites: {json.dumps(records, indent=2)}")
        
        print(f"📊 Records type: {type(records)}")
        if isinstance(records, dict):
            print(f"📊 Records keys: {list(records.keys())}")
        print("=" * 60)
        
        parsed_data = {
            "format": format,
            "records": records,
            "record_count": len(records) if isinstance(records, (dict, list)) else 1
        }
        
        duration_ms = (time.time() - start_time) * 1000
        client = MongoClient("mongodb://admin:changeme@mongodb:27017/")
        db = client["data_pipeline"]
        db.script_metrics.insert_one({
            "script": script_name,
            "duration_ms": duration_ms,
            "status": "success",
            "cpu_percent": get_cpu_usage(),
            "memory_mb": get_memory_mb(),
            "timestamp": datetime.now().isoformat()
        })
        
        return {
            "status": "success",
            "parsed_data": parsed_data,
            "duration_ms": round(duration_ms, 2),
            "cpu_percent": get_cpu_usage(),
            "memory_mb": get_memory_mb(),
            "step": "parsing"
        }
        
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        try:
            client = MongoClient("mongodb://admin:changeme@mongodb:27017/")
            db = client["data_pipeline"]
            db.script_metrics.insert_one({
                "script": script_name,
                "duration_ms": duration_ms,
                "status": "error",
                "error": str(e)[:100],
                "cpu_percent": get_cpu_usage(),
                "memory_mb": get_memory_mb(),
                "timestamp": datetime.now().isoformat()
            })
        except:
            pass
        return {
            "status": "error",
            "message": str(e),
            "step": "parsing"
        }