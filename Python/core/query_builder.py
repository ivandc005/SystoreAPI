"""
Query Builder - Costruisce query SQL dinamiche basate su configurazione
"""

from sqlalchemy import text


class QueryBuilder:
    """Costruisce query SQL dinamiche"""
    
    def __init__(self, engine):
        self.engine = engine
    
    def build_table_query(self, table_name, schema, config=None):
        """
        Costruisce query per visualizzare una tabella
        
        Args:
            table_name: Nome tabella
            schema: Metadati tabella
            config: Configurazione override (opzionale)
        
        Returns:
            str: Query SQL
        """
        
        config = config or {}
        
        # Colonne da selezionare
        columns = self._get_columns_list(schema, config)
        columns_str = ', '.join(columns)
        
        # Limit
        limit = config.get('default_limit', 100)
        
        # Order by
        order_by = self._get_order_by(schema, config)
        
        # Where clause
        where_clause = self._get_where_clause(config)
        
        # Costruisci query
        query = f"SELECT TOP {limit} {columns_str} FROM {table_name}"
        
        if where_clause:
            query += f" WHERE {where_clause}"
        
        if order_by:
            query += f" ORDER BY {order_by}"
        
        return query
    
    def build_custom_query(self, view_config):
        """
        Costruisce query custom da configurazione vista
        
        Args:
            view_config: Configurazione vista custom
        
        Returns:
            str/callable: Query SQL o callable per stored procedure
        """
        
        query_type = view_config.get('query_type', 'sql')
        
        if query_type == 'stored_procedure':
            return self._build_stored_procedure_call(view_config)
        
        elif query_type == 'sql':
            return view_config.get('query')
        
        elif query_type == 'template':
            return self._build_from_template(view_config)
        
        else:
            raise ValueError(f"Unknown query_type: {query_type}")
    
    def execute_query(self, query, params=None):
        """
        Esegue una query e restituisce risultati
        
        Args:
            query: Query SQL o callable
            params: Parametri per la query
        
        Returns:
            tuple: (rows, columns)
        """
        
        params = params or {}
        
        with self.engine.connect() as conn:
            # Se è una callable (stored procedure)
            if callable(query):
                result = query(conn, params)
            else:
                # Query SQL normale
                result = conn.execute(text(query), params)
            
            # Converti risultati
            columns = list(result.keys())
            rows = [dict(row._mapping) for row in result]
            
            return rows, columns
    
    def _get_columns_list(self, schema, config):
        """Determina quali colonne selezionare"""
        
        all_columns = [col['name'] for col in schema.get('columns', [])]
        
        # Colonne da nascondere
        hide_columns = config.get('hide_columns', [])
        
        # Filtra colonne
        columns = [col for col in all_columns if col not in hide_columns]
        
        # Se specificate esplicitamente, usa solo quelle
        if 'show_columns' in config:
            columns = config['show_columns']
        
        return columns
    
    def _get_order_by(self, schema, config):
        """Determina ORDER BY clause"""
        
        # Check override
        if 'order_by' in config:
            return config['order_by']
        
        # Default: primary key DESC
        primary_keys = schema.get('primary_keys', [])
        if primary_keys:
            return f"{primary_keys[0]} DESC"
        
        # Fallback: prima colonna
        first_col = schema['columns'][0]['name'] if schema.get('columns') else '*'
        return f"{first_col} DESC"
    
    def _get_where_clause(self, config):
        """Costruisce WHERE clause"""
        
        filters = config.get('filters', [])
        
        if not filters:
            return None
        
        # Combina filtri con AND
        return ' AND '.join(f"({f})" for f in filters)
    
    def _build_stored_procedure_call(self, view_config):
        """Costruisce chiamata a stored procedure"""
        
        proc_name = view_config.get('procedure')
        params = view_config.get('parameters', {})
        
        def call_procedure(conn, runtime_params=None):
            # Merge parametri statici e runtime
            all_params = {**params}
            if runtime_params:
                all_params.update(runtime_params)
            
            # Prepara parametri per SQL Server
            param_declarations = []
            param_assignments = []
            
            for key, value in all_params.items():
                if value == 'TODAY':
                    param_assignments.append(
                        f"@{key} = FORMAT(GETDATE(), 'yyyy-MM-dd')"
                    )
                elif value == 'TOMORROW':
                    param_assignments.append(
                        f"@{key} = FORMAT(DATEADD(day, 1, GETDATE()), 'yyyy-MM-dd')"
                    )
                else:
                    param_declarations.append(f"@{key} = :{key}")
            
            # Costruisci query completa
            query_parts = ["SET DATEFORMAT YMD"]
            
            if param_assignments:
                query_parts.extend([
                    f"DECLARE {', '.join(f'@{k} nvarchar(20)' for k in all_params.keys())}",
                    f"SELECT {', '.join(param_assignments)}"
                ])
            
            query_parts.append(f"EXEC {proc_name} {', '.join(f'@{k}' for k in all_params.keys())}")
            
            final_query = '; '.join(query_parts)
            
            return conn.execute(text(final_query), all_params)
        
        return call_procedure
    
    def _build_from_template(self, view_config):
        """Costruisce query da template"""
        
        template = view_config.get('query_template')
        params = view_config.get('parameters', {})
        
        # Sostituisci placeholders
        query = template
        for key, value in params.items():
            query = query.replace(f"{{{key}}}", str(value))
        
        return query