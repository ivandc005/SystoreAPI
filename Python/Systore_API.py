"""
Systore API Dashboard - Sistema Auto-Discovery
Versione semplificata con generazione dinamica di tutte le viste
"""

from flask import Flask, render_template, redirect, url_for, request, jsonify
from sqlalchemy import create_engine
from datetime import datetime
from pathlib import Path
import yaml
import logging

# Import moduli custom
from core.schema_discovery import SchemaDiscovery
from core.view_generator import ViewGenerator, MenuGenerator
from core.cache_manager import CacheManager
from translations import translation_manager

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ============================================================================
# INIZIALIZZAZIONE APP
# ============================================================================

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-in-production'

# Database connection
connection_string = "mssql+pyodbc://SYSTEM_ITALI:SYS123@localhost/WSHAVI?driver=ODBC+Driver+17+for+SQL+Server"
engine = create_engine(connection_string)

# Managers
cache_manager = CacheManager()
schema_discovery = SchemaDiscovery(engine)

# ============================================================================
# CARICAMENTO CONFIGURAZIONI
# ============================================================================

def load_overrides():
    """Carica tutti i file di override da cartella overrides/"""
    
    overrides = {
        'tables': {},
        'views': {},
        'global': {}
    }
    
    overrides_dir = Path('overrides')
    
    # Carica override tabelle
    tables_dir = overrides_dir / 'tables'
    if tables_dir.exists():
        for yaml_file in tables_dir.glob('*.yaml'):
            table_name = yaml_file.stem
            with open(yaml_file, 'r', encoding='utf-8') as f:
                overrides['tables'][table_name] = yaml.safe_load(f)
            logger.debug(f"Loaded override for table: {table_name}")
    
    # Carica viste custom
    views_dir = overrides_dir / 'views'
    if views_dir.exists():
        for yaml_file in views_dir.glob('*.yaml'):
            view_name = yaml_file.stem
            with open(yaml_file, 'r', encoding='utf-8') as f:
                overrides['views'][view_name] = yaml.safe_load(f)
            logger.debug(f"Loaded custom view: {view_name}")
    
    # Carica config globale
    global_config = overrides_dir / 'global.yaml'
    if global_config.exists():
        with open(global_config, 'r', encoding='utf-8') as f:
            overrides['global'] = yaml.safe_load(f)
    
    return overrides


# ============================================================================
# INIZIALIZZAZIONE SISTEMA
# ============================================================================

def initialize_system(force_scan=False):
    """Inizializza il sistema caricando schema e configurazioni"""
    
    logger.info("=" * 60)
    logger.info("🚀 Systore API Dashboard - Sistema Auto-Discovery")
    logger.info("=" * 60)
    
    # 1. Carica o scansiona schema database
    if force_scan or not cache_manager.is_cache_valid(Path('metadata/db_schema.json')):
        logger.info("📊 Scanning database schema...")
        schema = schema_discovery.scan_database(force=force_scan)
    else:
        logger.info("📦 Loading cached schema...")
        schema = schema_discovery.load_cached_schema()
    
    logger.info(f"✓ Schema loaded: {len(schema)} tables")
    
    # 2. Carica override
    logger.info("⚙️  Loading configuration overrides...")
    overrides = load_overrides()
    logger.info(f"✓ Loaded {len(overrides['tables'])} table overrides")
    logger.info(f"✓ Loaded {len(overrides['views'])} custom views")
    
    # 3. Registra route dinamiche
    logger.info("🔧 Registering dynamic routes...")
    view_gen = ViewGenerator(app, engine, schema, overrides)
    view_gen.register_all_table_routes()
    
    # 4. Registra viste custom
    for view_name, view_config in overrides['views'].items():
        view_gen.register_custom_view(view_name, view_config)
    
    # 5. Genera menu
    logger.info("📋 Generating menu structure...")
    menu_gen = MenuGenerator(schema, overrides)
    menu = menu_gen.generate_menu_structure()
    
    logger.info("=" * 60)
    logger.info("✅ System initialized successfully!")
    logger.info("=" * 60 + "\n")
    
    return schema, overrides, menu


# Inizializza sistema all'avvio
schema, overrides, menu = initialize_system()


# ============================================================================
# CONTEXT PROCESSOR - Traduzioni
# ============================================================================

@app.context_processor
def inject_translation_functions():
    """Inietta funzioni di traduzione in tutti i template"""
    return {
        't': translation_manager.get,
        'current_lang': translation_manager.get_current_language(),
        'supported_langs': translation_manager.supported_languages,
        'year': datetime.now().year
    }


# ============================================================================
# ROUTES - Sistema
# ============================================================================

@app.route('/')
def index():
    """Homepage con menu dinamico"""
    return render_template('homepage.html', menu=menu)


@app.route('/set-language/<lang>')
def set_language(lang):
    """Endpoint per cambiare lingua"""
    if translation_manager.set_language(lang):
        return redirect(request.referrer or url_for('index'))
    else:
        return jsonify({'error': 'Language not supported'}), 400


@app.route('/api/translations/<lang>')
def get_translations_api(lang):
    """API per recuperare traduzioni"""
    if lang in translation_manager.translations:
        return jsonify(translation_manager.translations[lang])
    return jsonify({'error': 'Language not found'}), 404


# ============================================================================
# ROUTES - Admin/Debug
# ============================================================================

@app.route('/admin/schema-info')
def schema_info():
    """Visualizza informazioni sullo schema"""
    
    scan_info = schema_discovery.get_scan_info()
    cache_info = cache_manager.get_cache_info()
    
    return jsonify({
        'scan_info': scan_info,
        'cache_info': cache_info,
        'tables_count': len(schema),
        'overrides_count': len(overrides['tables']),
        'custom_views': list(overrides['views'].keys())
    })


@app.route('/admin/rescan-database')
def rescan_database():
    """Forza una nuova scansione del database"""
    
    global schema, overrides, menu
    
    logger.info("🔄 Forcing database rescan...")
    schema, overrides, menu = initialize_system(force_scan=True)
    
    return jsonify({
        'status': 'success',
        'message': 'Database rescanned successfully',
        'tables_count': len(schema)
    })


@app.route('/admin/clear-cache')
def clear_cache():
    """Elimina tutte le cache"""
    
    cache_manager.invalidate_cache()
    
    return jsonify({
        'status': 'success',
        'message': 'All caches cleared'
    })


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(e):
    logger.error(f"Internal error: {e}")
    return render_template('500.html'), 500


# ============================================================================
# AVVIO APPLICAZIONE
# ============================================================================

if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 Systore API Dashboard - Auto-Discovery System")
    print("="*60)
    print(f"✓ Tables available: {len(schema)}")
    print(f"✓ Custom views: {len(overrides['views'])}")
    print(f"✓ Menu categories: {len(menu)}")
    print(f"✓ Languages: {', '.join(translation_manager.supported_languages)}")
    print("="*60 + "\n")
    
    app.run(debug=True, host='0.0.0.0', port=5000)