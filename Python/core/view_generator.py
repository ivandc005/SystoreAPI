"""
View Generator - Genera automaticamente viste e route Flask per ogni tabella
"""

from flask import render_template, request, jsonify
from .query_builder import QueryBuilder
from .formatters import TableFormatter
import logging

logger = logging.getLogger(__name__)


class ViewGenerator:
    """Genera dinamicamente viste Flask per tabelle del database"""
    
    def __init__(self, app, engine, schema, overrides=None):
        self.app = app
        self.engine = engine
        self.schema = schema
        self.overrides = overrides or {}
        self.query_builder = QueryBuilder(engine)
    
    def register_all_table_routes(self):
        """Registra automaticamente route per tutte le tabelle"""
        
        logger.info("🔧 Registering dynamic routes for all tables...")
        
        registered_count = 0
        
        for table_name, table_schema in self.schema.items():
            try:
                # Skip tabelle di sistema
                if self._should_skip_table(table_name):
                    continue
                
                # Registra route
                self._register_table_route(table_name, table_schema)
                registered_count += 1
                
                logger.debug(f"✓ Registered route for {table_name}")
                
            except Exception as e:
                logger.error(f"✗ Error registering {table_name}: {e}")
        
        logger.info(f"✅ Registered {registered_count} dynamic table routes")
    
    def register_custom_view(self, view_name, view_config):
        """Registra una vista custom (query complessa/stored procedure)"""
        
        route_path = view_config.get('route', f'/{view_name}')
        
        @self.app.route(route_path)
        def custom_view():
            try:
                # Costruisci query
                query = self.query_builder.build_custom_query(view_config)
                
                # Esegui query
                rows, columns = self.query_builder.execute_query(query)
                
                # Formattazione (se specificata)
                if 'column_overrides' in view_config:
                    formatter = TableFormatter(
                        {'columns': [{'name': c} for c in columns]},
                        view_config.get('column_overrides', {})
                    )
                    formatted_rows = formatter.format_table_data(rows)
                else:
                    formatted_rows = rows
                
                # Render template
                template = view_config.get('template', 'dynamic_custom_view.html')
                
                return render_template(
                    template,
                    dati=formatted_rows,
                    colonne=columns,
                    view_name=view_name,
                    view_config=view_config
                )
                
            except Exception as e:
                logger.error(f"Error in custom view {view_name}: {e}")
                return f"Error loading view: {str(e)}", 500
        
        # Imposta nome funzione univoco
        custom_view.__name__ = f'custom_view_{view_name}'
        
        logger.info(f"✓ Registered custom view: {view_name} at {route_path}")
    
    def _register_table_route(self, table_name, table_schema):
        """Registra una route per una singola tabella"""
        
        # Carica override se esiste
        table_override = self.overrides.get('tables', {}).get(table_name, {})
        
        # Determina route path
        route_path = table_override.get('route', f'/table/{table_name.lower()}')
        
        # Crea view function
        @self.app.route(route_path)
        def table_view():
            try:
                # Parametri dalla query string
                limit = request.args.get('limit', table_override.get('default_limit', 100), type=int)
                page = request.args.get('page', 1, type=int)
                
                # Aggiorna config con parametri runtime
                runtime_config = {**table_override}
                runtime_config['default_limit'] = limit
                
                # Costruisci query
                query = self.query_builder.build_table_query(
                    table_name, 
                    table_schema, 
                    runtime_config
                )
                
                # Esegui query
                rows, columns = self.query_builder.execute_query(query)
                
                # Formattazione intelligente
                formatter = TableFormatter(table_schema, table_override)
                formatted_rows = formatter.format_table_data(rows)
                
                # Filtra colonne nascoste
                visible_columns = [
                    col for col in columns 
                    if col not in table_override.get('hide_columns', [])
                ]
                
                # Render template
                return render_template(
                    'dynamic_table.html',
                    table_name=table_name,
                    display_name=table_override.get('display_name', table_name),
                    dati=formatted_rows,
                    colonne=visible_columns,
                    schema=table_schema,
                    config=table_override
                )
                
            except Exception as e:
                logger.error(f"Error in table view {table_name}: {e}")
                return f"Error loading table: {str(e)}", 500
        
        # Imposta nome funzione univoco (importante per Flask)
        table_view.__name__ = f'table_view_{table_name.lower()}'
    
    def _should_skip_table(self, table_name):
        """Determina se una tabella deve essere skippata"""
        
        # Skip tabelle di sistema
        system_prefixes = ['sys', 'INFORMATION_SCHEMA', 'temp', 'tmp']
        
        for prefix in system_prefixes:
            if table_name.startswith(prefix):
                return True
        
        # Check blacklist globale
        blacklist = self.overrides.get('global', {}).get('skip_tables', [])
        if table_name in blacklist:
            return True
        
        return False
    
    def generate_api_endpoint(self, table_name, table_schema):
        """Genera endpoint API REST per una tabella"""
        
        api_path = f'/api/table/{table_name.lower()}'
        
        @self.app.route(api_path)
        def api_table():
            try:
                # Parametri
                limit = request.args.get('limit', 100, type=int)
                offset = request.args.get('offset', 0, type=int)
                
                # Costruisci query con paginazione
                query = self.query_builder.build_table_query(
                    table_name, 
                    table_schema,
                    {'default_limit': limit}
                )
                
                # Esegui
                rows, columns = self.query_builder.execute_query(query)
                
                return jsonify({
                    'table': table_name,
                    'columns': columns,
                    'data': rows,
                    'count': len(rows)
                })
                
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        api_table.__name__ = f'api_table_{table_name.lower()}'
        
        logger.debug(f"✓ Registered API endpoint: {api_path}")


class MenuGenerator:
    """Genera menu dinamico basato su tabelle disponibili"""
    
    def __init__(self, schema, overrides=None):
        self.schema = schema
        self.overrides = overrides or {}
    
    def generate_menu_structure(self):
        """
        Genera struttura menu categorizzando automaticamente le tabelle
        
        Returns:
            dict: Struttura menu con categorie
        """
        
        categories = {
            'import_export': {
                'name': 'Import/Export Management',
                'icon': '📦',
                'tables': []
            },
            'operations': {
                'name': 'Operations & Execution',
                'icon': '⚙️',
                'tables': []
            },
            'master_data': {
                'name': 'Master Data',
                'icon': '📋',
                'tables': []
            },
            'reports': {
                'name': 'Reports & Analysis',
                'icon': '📊',
                'tables': []
            },
            'other': {
                'name': 'Other Tables',
                'icon': '📁',
                'tables': []
            }
        }
        
        # Categorizza automaticamente
        for table_name in self.schema.keys():
            category = self._categorize_table(table_name)
            
            table_config = self.overrides.get('tables', {}).get(table_name, {})
            
            table_info = {
                'name': table_name,
                'display_name': table_config.get('display_name', table_name),
                'description': table_config.get('description', ''),
                'route': table_config.get('route', f'/table/{table_name.lower()}'),
                'icon': table_config.get('icon', '📄'),
                'badges': table_config.get('badges', [])
            }
            
            categories[category]['tables'].append(table_info)
        
        # Rimuovi categorie vuote
        categories = {k: v for k, v in categories.items() if v['tables']}
        
        return categories
    
    def _categorize_table(self, table_name):
        """Categorizza automaticamente una tabella in base al nome"""
        
        name_upper = table_name.upper()
        
        # Pattern matching
        if 'HOST_IMPORT' in name_upper or 'HOST_EXPORT' in name_upper:
            return 'import_export'
        
        if any(x in name_upper for x in ['RUN_', 'EXEC', 'OPERATION', 'MISSION']):
            return 'operations'
        
        if any(x in name_upper for x in ['DAT_', 'MAG_', 'MASTER', 'ARTICOL']):
            return 'master_data'
        
        if any(x in name_upper for x in ['REPORT', 'FLOW', 'CHECK', 'STAT']):
            return 'reports'
        
        return 'other'