"""
Smart Formatters - Formattazione intelligente dei dati per rendering HTML
"""

from datetime import datetime
import xml.dom.minidom
import json


class SmartFormatter:
    """Applica formattazione intelligente ai dati della tabella"""
    
    @staticmethod
    def format_value(value, formatter_type, column_name=None, config=None):
        """
        Formatta un valore singolo
        
        Args:
            value: Valore da formattare
            formatter_type: Tipo di formatter da applicare
            column_name: Nome colonna (opzionale)
            config: Configurazione aggiuntiva (opzionale)
        
        Returns:
            dict: {'value': formatted_value, 'css_class': css_class, 'raw': original}
        """
        
        if value is None or value == '':
            return {
                'value': '—',
                'css_class': 'empty-cell',
                'raw': None
            }
        
        formatter_map = {
            'status_badge': SmartFormatter._format_status,
            'expandable_code': SmartFormatter._format_expandable_code,
            'datetime': SmartFormatter._format_datetime,
            'monospace_id': SmartFormatter._format_monospace_id,
            'monospace_code': SmartFormatter._format_monospace_code,
            'number': SmartFormatter._format_number,
            'decimal': SmartFormatter._format_decimal,
            'boolean': SmartFormatter._format_boolean,
            'text': SmartFormatter._format_text
        }
        
        formatter_func = formatter_map.get(formatter_type, SmartFormatter._format_text)
        return formatter_func(value, column_name, config)
    
    @staticmethod
    def _format_status(value, column_name=None, config=None):
        """Formatta colonne STATUS con badge colorati"""
        
        # Default colors
        status_colors = {
            'COMPL': 'green',
            'COMPLETED': 'green',
            'SUCCESS': 'green',
            'OK': 'green',
            'WAIT': 'yellow',
            'WAITING': 'yellow',
            'PENDING': 'yellow',
            'ERR': 'red',
            'ERROR': 'red',
            'FAILED': 'red',
            'CANCEL': 'gray',
            'CANCELLED': 'gray'
        }
        
        # Override con config se disponibile
        if config and 'status_colors' in config:
            status_colors.update(config['status_colors'])
        
        value_upper = str(value).upper()
        color = status_colors.get(value_upper, 'blue')
        
        return {
            'value': value,
            'css_class': f'campo-evidenziato-{color}',
            'raw': value,
            'is_status': True
        }
    
    @staticmethod
    def _format_expandable_code(value, column_name=None, config=None):
        """Formatta XML/JSON con popup espandibile"""
        
        # Prova a pretty-print XML
        if value and (str(value).strip().startswith('<') or 'XML' in str(column_name or '').upper()):
            try:
                dom = xml.dom.minidom.parseString(str(value))
                pretty = dom.toprettyxml(indent="  ")
            except:
                pretty = str(value)
        else:
            # Potrebbe essere JSON
            try:
                parsed = json.loads(str(value))
                pretty = json.dumps(parsed, indent=2)
            except:
                pretty = str(value)
        
        # Preview (prime 2 righe)
        lines = pretty.split('\n')
        preview = '\n'.join(lines[:2])
        if len(lines) > 2:
            preview += '...'
        
        return {
            'value': preview,
            'css_class': 'campo-xml',
            'raw': value,
            'full_content': pretty,
            'is_expandable': True
        }
    
    @staticmethod
    def _format_datetime(value, column_name=None, config=None):
        """Formatta date e timestamp"""
        
        if isinstance(value, datetime):
            dt = value
        elif isinstance(value, str):
            try:
                dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
            except:
                return {'value': value, 'css_class': 'datetime', 'raw': value}
        else:
            return {'value': str(value), 'css_class': 'datetime', 'raw': value}
        
        # Formato: YYYY-MM-DD HH:MM:SS
        formatted = dt.strftime('%Y-%m-%d %H:%M:%S')
        
        return {
            'value': formatted,
            'css_class': 'datetime',
            'raw': value,
            'timestamp': dt.timestamp()
        }
    
    @staticmethod
    def _format_monospace_id(value, column_name=None, config=None):
        """Formatta ID con font monospace"""
        
        return {
            'value': str(value),
            'css_class': 'monospace-id',
            'raw': value
        }
    
    @staticmethod
    def _format_monospace_code(value, column_name=None, config=None):
        """Formatta codici (SSCC, UDC, etc.) con font monospace"""
        
        return {
            'value': str(value),
            'css_class': 'monospace-code',
            'raw': value
        }
    
    @staticmethod
    def _format_number(value, column_name=None, config=None):
        """Formatta numeri interi"""
        
        try:
            num = int(value)
            formatted = f"{num:,}".replace(',', '.')  # Formato italiano
        except:
            formatted = str(value)
        
        return {
            'value': formatted,
            'css_class': 'number',
            'raw': value
        }
    
    @staticmethod
    def _format_decimal(value, column_name=None, config=None):
        """Formatta numeri decimali"""
        
        try:
            num = float(value)
            decimals = config.get('decimals', 2) if config else 2
            formatted = f"{num:,.{decimals}f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        except:
            formatted = str(value)
        
        return {
            'value': formatted,
            'css_class': 'decimal',
            'raw': value
        }
    
    @staticmethod
    def _format_boolean(value, column_name=None, config=None):
        """Formatta valori booleani"""
        
        if value in [True, 1, '1', 'true', 'True', 'TRUE', 'Yes', 'YES']:
            return {
                'value': '✓',
                'css_class': 'boolean-true',
                'raw': value
            }
        elif value in [False, 0, '0', 'false', 'False', 'FALSE', 'No', 'NO']:
            return {
                'value': '✗',
                'css_class': 'boolean-false',
                'raw': value
            }
        else:
            return {
                'value': str(value),
                'css_class': 'boolean-unknown',
                'raw': value
            }
    
    @staticmethod
    def _format_text(value, column_name=None, config=None):
        """Formattazione testo standard"""
        
        text = str(value)
        
        # Se troppo lungo, tronca con tooltip
        max_length = config.get('max_length', 100) if config else 100
        
        if len(text) > max_length:
            return {
                'value': text[:max_length] + '...',
                'css_class': 'text-truncated',
                'raw': value,
                'full_text': text
            }
        
        return {
            'value': text,
            'css_class': 'text',
            'raw': value
        }


class TableFormatter:
    """Formatta un'intera tabella di dati"""
    
    def __init__(self, schema, overrides=None):
        self.schema = schema
        self.overrides = overrides or {}
    
    def format_table_data(self, rows):
        """
        Formatta tutte le righe di una tabella
        
        Args:
            rows: Lista di dizionari (righe della query)
        
        Returns:
            list: Righe formattate con metadati
        """
        
        formatted_rows = []
        
        for row in rows:
            formatted_row = {}
            
            for col_name, value in row.items():
                # Trova metadati colonna
                col_meta = self._get_column_metadata(col_name)
                
                # Determina formatter
                formatter_type = self._get_formatter_for_column(col_name, col_meta)
                
                # Applica formattazione
                formatted_row[col_name] = SmartFormatter.format_value(
                    value, 
                    formatter_type,
                    col_name,
                    self.overrides.get('columns', {}).get(col_name)
                )
            
            formatted_rows.append(formatted_row)
        
        return formatted_rows
    
    def _get_column_metadata(self, column_name):
        """Ottiene metadati della colonna dallo schema"""
        
        for col in self.schema.get('columns', []):
            if col['name'] == column_name:
                return col
        return None
    
    def _get_formatter_for_column(self, column_name, col_meta):
        """Determina quale formatter usare"""
        
        # 1. Check override esplicito
        if column_name in self.overrides.get('columns', {}):
            override_formatter = self.overrides['columns'][column_name].get('formatter')
            if override_formatter:
                return override_formatter
        
        # 2. Usa suggested formatter dallo schema
        if col_meta and 'suggested_formatter' in col_meta:
            return col_meta['suggested_formatter']
        
        # 3. Default
        return 'text'