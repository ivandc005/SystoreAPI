"""
Schema Discovery Engine - Estrae automaticamente metadati dal database
"""

import json
from pathlib import Path
from datetime import datetime
from sqlalchemy import inspect, text
import logging

logger = logging.getLogger(__name__)


class SchemaDiscovery:
    """Scansiona il database ed estrae metadati strutturali"""
    
    def __init__(self, engine, metadata_dir='metadata'):
        self.engine = engine
        self.metadata_dir = Path(metadata_dir)
        self.metadata_dir.mkdir(exist_ok=True)
        
        self.schema_file = self.metadata_dir / 'db_schema.json'
        self.scan_info_file = self.metadata_dir / 'last_scan.json'
    
    def scan_database(self, force=False):
        """
        Scansiona il database e salva i metadati
        
        Args:
            force: Se True, forza una nuova scansione anche se cache esiste
        
        Returns:
            dict: Schema completo del database
        """
        # Se esiste cache recente e non è forzato, usa quella
        if not force and self.schema_file.exists():
            cache_age = datetime.now() - datetime.fromtimestamp(
                self.schema_file.stat().st_mtime
            )
            if cache_age.seconds < 3600:  # Cache valida per 1 ora
                logger.info("Using cached schema (less than 1 hour old)")
                return self.load_cached_schema()
        
        logger.info("🔍 Starting database scan...")
        inspector = inspect(self.engine)
        schema = {}
        
        # Ottieni lista tabelle
        table_names = inspector.get_table_names()
        logger.info(f"Found {len(table_names)} tables")
        
        for table_name in table_names:
            try:
                schema[table_name] = self._extract_table_metadata(
                    inspector, table_name
                )
                logger.debug(f"✓ Scanned {table_name}")
            except Exception as e:
                logger.error(f"✗ Error scanning {table_name}: {e}")
                continue
        
        # Salva schema
        self._save_schema(schema)
        
        logger.info(f"✅ Database scan completed: {len(schema)} tables processed")
        return schema
    
    def _extract_table_metadata(self, inspector, table_name):
        """Estrae metadati completi di una singola tabella"""
        
        metadata = {
            'name': table_name,
            'columns': [],
            'primary_keys': [],
            'foreign_keys': [],
            'indexes': [],
            'sample_data': None
        }
        
        # Estrai colonne con dettagli
        for column in inspector.get_columns(table_name):
            col_info = {
                'name': column['name'],
                'type': str(column['type']),
                'nullable': column['nullable'],
                'default': str(column.get('default')) if column.get('default') else None,
                'autoincrement': column.get('autoincrement', False)
            }
            
            # Aggiungi hint per formatter basato sul nome
            col_info['suggested_formatter'] = self._suggest_formatter(
                column['name'], 
                str(column['type'])
            )
            
            metadata['columns'].append(col_info)
        
        # Estrai primary keys
        pk_constraint = inspector.get_pk_constraint(table_name)
        if pk_constraint:
            metadata['primary_keys'] = pk_constraint.get('constrained_columns', [])
        
        # Estrai foreign keys
        for fk in inspector.get_foreign_keys(table_name):
            metadata['foreign_keys'].append({
                'column': fk['constrained_columns'][0] if fk['constrained_columns'] else None,
                'referenced_table': fk['referred_table'],
                'referenced_column': fk['referred_columns'][0] if fk['referred_columns'] else None
            })
        
        # Estrai indici
        for idx in inspector.get_indexes(table_name):
            metadata['indexes'].append({
                'name': idx['name'],
                'columns': idx['column_names'],
                'unique': idx.get('unique', False)
            })
        
        # Ottieni sample data per analisi
        try:
            metadata['sample_data'] = self._get_sample_data(table_name)
        except Exception as e:
            logger.warning(f"Could not get sample data for {table_name}: {e}")
        
        return metadata
    
    def _suggest_formatter(self, column_name, column_type):
        """Suggerisce un formatter basato su nome e tipo colonna"""
        
        col_upper = column_name.upper()
        type_lower = column_type.lower()
        
        # Pattern matching su nome colonna
        if 'STATUS' in col_upper or 'STATE' in col_upper:
            return 'status_badge'
        
        if 'XML' in col_upper or 'JSON' in col_upper:
            return 'expandable_code'
        
        if any(x in col_upper for x in ['DATE', 'TIME', 'TIMESTAMP']):
            return 'datetime'
        
        if col_upper.endswith('_ID') or col_upper.endswith('ID'):
            return 'monospace_id'
        
        if 'SSCC' in col_upper or 'UDC' in col_upper:
            return 'monospace_code'
        
        # Pattern matching su tipo SQL
        if 'datetime' in type_lower or 'timestamp' in type_lower:
            return 'datetime'
        
        if any(x in type_lower for x in ['int', 'bigint', 'smallint', 'tinyint']):
            return 'number'
        
        if 'decimal' in type_lower or 'numeric' in type_lower or 'float' in type_lower:
            return 'decimal'
        
        if 'bit' in type_lower or 'boolean' in type_lower:
            return 'boolean'
        
        # Default
        return 'text'
    
    def _get_sample_data(self, table_name, limit=5):
        """Ottiene dati di esempio per analisi pattern"""
        
        with self.engine.connect() as conn:
            result = conn.execute(
                text(f"SELECT TOP {limit} * FROM {table_name}")
            )
            
            sample = []
            for row in result:
                sample.append(dict(row._mapping))
            
            return sample
    
    def _save_schema(self, schema):
        """Salva schema su file JSON"""
        
        with open(self.schema_file, 'w', encoding='utf-8') as f:
            json.dump(schema, f, indent=2, ensure_ascii=False, default=str)
        
        # Salva info scan
        scan_info = {
            'timestamp': datetime.now().isoformat(),
            'tables_count': len(schema),
            'total_columns': sum(len(t['columns']) for t in schema.values())
        }
        
        with open(self.scan_info_file, 'w', encoding='utf-8') as f:
            json.dump(scan_info, f, indent=2)
        
        logger.info(f"Schema saved to {self.schema_file}")
    
    def load_cached_schema(self):
        """Carica schema dalla cache"""
        
        if not self.schema_file.exists():
            raise FileNotFoundError(
                "Schema cache not found. Run scan_database() first."
            )
        
        with open(self.schema_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def get_table_info(self, table_name):
        """Ottieni info di una singola tabella dalla cache"""
        
        schema = self.load_cached_schema()
        return schema.get(table_name)
    
    def get_scan_info(self):
        """Ottieni informazioni sull'ultimo scan"""
        
        if not self.scan_info_file.exists():
            return None
        
        with open(self.scan_info_file, 'r', encoding='utf-8') as f:
            return json.load(f)