import time
import os
import json
import csv
import re
import requests
import pandas as pd
from datetime import datetime
from pymongo import MongoClient
from io import StringIO
from bs4 import BeautifulSoup
import sqlalchemy as sa

# ============================================
# FONCTIONS DE CONNEXION AUX SOURCES
# ============================================

def read_csv_file(file_path):
    """Lit un fichier CSV"""
    data = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data

def read_json_file(file_path):
    """Lit un fichier JSON"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def read_xml_file(file_path):
    """Lit un fichier XML"""
    import xml.etree.ElementTree as ET

    def element_to_dict(element):
        record = {}
        for child in element:
            if len(list(child)) > 0:
                record[child.tag] = element_to_dict(child)
            else:
                record[child.tag] = child.text
        return record

    tree = ET.parse(file_path)
    root = tree.getroot()
    children = list(root)

    if not children:
        return {}

    if all(len(list(child)) > 0 for child in children):
        return [element_to_dict(child) for child in children]

    if len(children) > 1 and all(len(list(child)) == 0 for child in children):
        return [{child.tag: child.text for child in children}]

    first_child = children[0]
    if len(list(first_child)) > 0:
        return [element_to_dict(first_child)]

    return {child.tag: child.text for child in children}

def read_excel_file(file_path):
    """Lit un fichier Excel"""
    df = pd.read_excel(file_path)
    return df.to_dict('records') if not df.empty else []

def read_parquet_file(file_path):
    """Lit un fichier Parquet"""
    df = pd.read_parquet(file_path)
    return df.to_dict('records') if not df.empty else []

def read_html_file(file_path):
    """Lit un fichier HTML (scraping)"""
    with open(file_path, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f.read(), 'html.parser')
    
    data = {}
    
    titles = soup.find_all(['h1', 'h2', 'h3'])
    if titles:
        data['titles'] = [t.get_text(strip=True) for t in titles[:5]]
    
    paragraphs = soup.find_all('p')
    if paragraphs:
        data['paragraphs'] = [p.get_text(strip=True) for p in paragraphs[:5]]
    
    links = soup.find_all('a')
    if links:
        data['links'] = [{'text': l.get_text(strip=True), 'href': l.get('href')} for l in links[:10]]
    
    tables = soup.find_all('table')
    if tables:
        table_data = []
        for table in tables[:2]:
            rows = table.find_all('tr')
            for row in rows:
                cells = [c.get_text(strip=True) for c in row.find_all(['td', 'th'])]
                if cells:
                    table_data.append(cells)
        data['tables'] = table_data
    
    return data

def read_sql_database(connection_string, query):
    """Lit depuis une base de données SQL"""
    engine = sa.create_engine(connection_string)
    with engine.connect() as conn:
        df = pd.read_sql(query, conn)
    return df.to_dict('records') if not df.empty else []

def fetch_api_rest(url, method='GET', headers=None, params=None, data=None):
    """Appelle une API REST"""
    if method.upper() == 'GET':
        response = requests.get(url, headers=headers, params=params)
    elif method.upper() == 'POST':
        response = requests.post(url, headers=headers, json=data)
    elif method.upper() == 'PUT':
        response = requests.put(url, headers=headers, json=data)
    elif method.upper() == 'DELETE':
        response = requests.delete(url, headers=headers)
    else:
        raise ValueError(f"Méthode non supportée: {method}")
    
    response.raise_for_status()
    return response.json()

def fetch_api_graphql(url, query, variables=None, headers=None):
    """Appelle une API GraphQL"""
    payload = {'query': query}
    if variables:
        payload['variables'] = variables
    
    response = requests.post(url, json=payload, headers=headers)
    response.raise_for_status()
    return response.json()


# ============================================
# DÉTECTION DU FORMAT / SOURCE
# ============================================

def detect_format(file_path):
    """Détecte le format à partir de l'extension"""
    ext = os.path.splitext(file_path)[1].lower()
    formats = {
        '.csv': 'csv',
        '.json': 'json',
        '.xml': 'xml',
        '.xlsx': 'excel',
        '.xls': 'excel',
        '.parquet': 'parquet',
        '.html': 'html',
        '.htm': 'html'
    }
    return formats.get(ext, 'unknown')

def detect_source_type(source_type, source_path):
    """Détecte le type de source"""
    if source_type:
        return source_type
    if source_path.startswith('http://') or source_path.startswith('https://'):
        return 'api'
    if source_path.startswith('postgresql://') or source_path.startswith('mysql://') or source_path.startswith('sqlite://'):
        return 'sql'
    ext = os.path.splitext(source_path)[1].lower()
    if ext in ['.csv']:
        return 'csv'
    if ext in ['.json']:
        return 'json'
    if ext in ['.xml']:
        return 'xml'
    if ext in ['.xlsx', '.xls']:
        return 'excel'
    if ext in ['.parquet']:
        return 'parquet'
    if ext in ['.html', '.htm']:
        return 'html'
    return 'unknown'


# ============================================
# LECTURE DES DONNÉES SELON LA SOURCE
# ============================================

def read_data_from_source(source_type, source_path, file_path=None, format=None, **kwargs):
    """
    Lit les données selon le type de source
    """
    if source_type in ['csv', 'json', 'xml', 'excel', 'parquet', 'html']:
        actual_path = file_path or source_path
        if not os.path.exists(actual_path):
            raise FileNotFoundError(f"Fichier introuvable: {actual_path}")
        
        if source_type == 'csv':
            return read_csv_file(actual_path)
        elif source_type == 'json':
            return read_json_file(actual_path)
        elif source_type == 'xml':
            return read_xml_file(actual_path)
        elif source_type == 'excel':
            return read_excel_file(actual_path)
        elif source_type == 'parquet':
            return read_parquet_file(actual_path)
        elif source_type == 'html':
            return read_html_file(actual_path)
    
    elif source_type == 'api':
        url = source_path
        method = kwargs.get('method', 'GET')
        headers = kwargs.get('headers', {})
        data = kwargs.get('data', {})
        params = kwargs.get('params', {})
        return fetch_api_rest(url, method, headers, params, data)
    
    elif source_type == 'graphql':
        url = source_path
        query = kwargs.get('query', '')
        variables = kwargs.get('variables', {})
        headers = kwargs.get('headers', {})
        return fetch_api_graphql(url, query, variables, headers)
    
    elif source_type == 'sql':
        connection_string = source_path
        query = kwargs.get('query', 'SELECT * FROM table LIMIT 1')
        return read_sql_database(connection_string, query)
    
    else:
        raise ValueError(f"Type de source non supporté: {source_type}")


# ============================================
# MÉTRIQUES (CPU / Mémoire)
# ============================================

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


# ============================================
# SCRIPT PRINCIPAL
# ============================================

def main(
    source_type: str = None,
    source_path: str = None,
    file_path: str = None,
    format: str = None,
    method: str = 'GET',
    headers: str = None,
    params: str = None,
    data: str = None,
    query: str = None,
    variables: str = None
):
    """
    Ingestion - Connecteur vers toutes les sources de données
    """
    start_time = time.time()
    script_name = "ingestion"
    
    try:
        actual_source_type = detect_source_type(source_type, source_path)
        print(f"🔍 Type de source détecté: {actual_source_type}")
        
        actual_file_path = file_path
        if actual_file_path is None and actual_source_type in ['csv', 'json', 'xml', 'excel', 'parquet', 'html']:
            if source_path.startswith('/'):
                actual_file_path = source_path
            else:
                actual_file_path = f"/data/{source_path}"
        
        headers_dict = json.loads(headers) if headers else {}
        params_dict = json.loads(params) if params else {}
        data_dict = json.loads(data) if data else {}
        variables_dict = json.loads(variables) if variables else {}
        
        print(f"📁 Source: {source_path}")
        print(f"📄 Type: {actual_source_type}")
        
        raw_data = read_data_from_source(
            source_type=actual_source_type,
            source_path=source_path,
            file_path=actual_file_path,
            format=format,
            method=method,
            headers=headers_dict,
            params=params_dict,
            data=data_dict,
            query=query,
            variables=variables_dict
        )
        
        print(f"📊 Données lues: {json.dumps(raw_data, indent=2)}")
        
        client = MongoClient("mongodb://admin:changeme@mongodb:27017/")
        db = client["data_pipeline"]
        
        raw_payload = {
            "source_type": actual_source_type,
            "source_path": source_path,
            "ingested_at": datetime.now().isoformat(),
            "data": raw_data,
            "file_format": format,
            "method": method if actual_source_type == 'api' else None
        }
        
        result = db.raw_data.insert_one({
            "source_type": actual_source_type,
            "source_path": source_path,
            "ingested_at": datetime.now().isoformat(),
            "step": script_name,
            "raw_payload": raw_payload,
            "status": "pending"
        })
        
        duration_ms = (time.time() - start_time) * 1000
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
            "raw_payload": raw_payload,
            "document_id": str(result.inserted_id),
            "source_type": actual_source_type,
            "source_path": source_path,
            "duration_ms": round(duration_ms, 2),
            "cpu_percent": get_cpu_usage(),
            "memory_mb": get_memory_mb(),
            "step": "ingestion"
        }
        
    except FileNotFoundError as e:
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
            "step": "ingestion"
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
            "step": "ingestion"
        }