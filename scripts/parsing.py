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
    records = []

    if 'tables' in html_data and html_data['tables']:
        table_blob = html_data['tables']

        if table_blob and isinstance(table_blob[0], list) and table_blob[0] and isinstance(table_blob[0][0], list):
            candidate_tables = table_blob
        else:
            candidate_tables = [table_blob]

        for table in candidate_tables:
            if not table or len(table) < 2:
                continue

            headers = table[0]
            for values in table[1:]:
                record = {}
                for i, header in enumerate(headers):
                    if i >= len(values):
                        continue

                    header_lower = header.lower().strip()
                    value = values[i]

                    if 'id' in header_lower or 'product' in header_lower:
                        record['id'] = value
                    elif 'name' in header_lower:
                        record['name'] = value
                    elif 'price' in header_lower or 'amount' in header_lower:
                        clean_price = value.replace('$', '').replace('€', '').replace(',', '').strip()
                        record['amount'] = clean_price
                    elif 'date' in header_lower:
                        record['date'] = value
                    elif 'country' in header_lower or 'origin' in header_lower:
                        record['country'] = value
                    elif 'email' in header_lower or 'contact' in header_lower:
                        record['email'] = value

                if record:
                    records.append(record)

    if records:
        return records

    result = {}

    if 'titles' in html_data and html_data['titles']:
        result['title'] = html_data['titles'][0]

    if not result and 'paragraphs' in html_data and html_data['paragraphs']:
        text = ' '.join(html_data['paragraphs'])
        import re
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
        if email_match:
            result['email'] = email_match.group()
        price_match = re.search(r'\$?(\d+\.?\d*)', text)
        if price_match:
            result['amount'] = price_match.group(1)
    
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
                records = []
            else:
                records = raw_data
                print(f"📊 Liste de {len(raw_data)} éléments conservée")
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
        elif isinstance(records, list):
            print(f"📊 Records length: {len(records)}")
        print("=" * 60)
        
        parsed_data = {
            "format": format,
            "records": records,
            "record_count": len(records) if isinstance(records, list) else 1
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