# translations.py - Sistema di traduzione centralizzato per Systore API Dashboard

import json
from pathlib import Path
from functools import wraps
from flask import session, request

class TranslationManager:
    """
    Gestore centralizzato delle traduzioni.
    Supporta caricamento dinamico, fallback e facile estensione.
    """
    
    def __init__(self, translations_dir='translations'):
        self.translations_dir = Path(translations_dir)
        self.translations = {}
        self.default_language = 'it'
        self.supported_languages = []
        self.load_all_translations()
    
    def load_all_translations(self):
        """Carica tutte le traduzioni disponibili dalla directory"""
        if not self.translations_dir.exists():
            self.translations_dir.mkdir(parents=True)
            self._create_default_translations()
        
        for lang_file in self.translations_dir.glob('*.json'):
            lang_code = lang_file.stem
            with open(lang_file, 'r', encoding='utf-8') as f:
                self.translations[lang_code] = json.load(f)
                self.supported_languages.append(lang_code)
        
        print(f"✓ Lingue caricate: {', '.join(self.supported_languages)}")
    
    def get(self, key, lang=None, **kwargs):
        """
        Recupera una traduzione con supporto per variabili dinamiche.
        
        Args:
            key: Chiave della traduzione (supporta notazione dot: 'header.title')
            lang: Codice lingua (default: lingua sessione o default)
            **kwargs: Variabili da sostituire nel template
        
        Returns:
            Stringa tradotta o chiave originale se non trovata
        """
        if lang is None:
            lang = session.get('language', self.default_language)
        
        # Fallback alla lingua di default se non supportata
        if lang not in self.translations:
            lang = self.default_language
        
        # Naviga la struttura JSON usando la notazione dot
        keys = key.split('.')
        value = self.translations.get(lang, {})
        
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                break
        
        # Se non trovata, usa chiave come fallback
        if value is None:
            print(f"⚠️ Traduzione mancante: {key} ({lang})")
            return key
        
        # Sostituisci variabili dinamiche {var}
        if kwargs and isinstance(value, str):
            try:
                value = value.format(**kwargs)
            except KeyError as e:
                print(f"⚠️ Variabile mancante in '{key}': {e}")
        
        return value
    
    def get_current_language(self):
        """Restituisce la lingua corrente della sessione"""
        return session.get('language', self.default_language)
    
    def set_language(self, lang):
        """Imposta la lingua per la sessione corrente"""
        if lang in self.supported_languages:
            session['language'] = lang
            return True
        return False
    
    def _create_default_translations(self):
        """Crea i file di traduzione di default (IT e EN)"""
        
        # Traduzioni italiane (default)
        it_translations = {
            "meta": {
                "language_name": "Italiano",
                "language_code": "it"
            },
            "header": {
                "title": "Systore API Dashboard",
                "subtitle": "Visualizza e gestisci i dati del tuo Impianto",
                "home_aria": "Homepage"
            },
            "footer": {
                "copyright": "© {year} Database Management System | Powered by SystemLogistics"
            },
            "search": {
                "placeholder": "🔍 Cerca tabelle, report o visualizzazioni...",
                "table_placeholder": "🔍 Cerca nella tabella...",
                "clear": "Cancella",
                "no_results": "🔍 Nessun risultato trovato per la tua ricerca.",
                "results_count": "{visible} / {total} righe"
            },
            "categories": {
                "import_export": "Gestione Import/Export",
                "movement": "Gestione Movimentazione",
                "reports": "Report e Analisi",
                "custom": "Visualizzazioni Personalizzate"
            },
            "cards": {
                "import": {
                    "title": "IMPORT",
                    "description": "Visualizza gli ultimi 100 record della tabella HOST_IMPORT ordinati per data. Include formattazione XML avanzata.",
                    "keywords": "import host xml tabella"
                },
                "export": {
                    "title": "EXPORT",
                    "description": "Visualizza gli ultimi 100 record della tabella HOST_EXPORT ordinati per data. Include formattazione XML avanzata.",
                    "keywords": "export host xml tabella"
                },
                "entry_notices": {
                    "title": "Avvisi di Ingresso",
                    "description": "Visualizza gli avvisi di ingresso in attesa, in esecuzione o in incompleto",
                    "keywords": "avvisi ingresso attesa incompleto"
                },
                "launch_orders": {
                    "title": "Lancio Ordini",
                    "description": "Visualizza tutti gli ordini di uscita in attesa di esecuzione, in esecuzione o in incompleto.",
                    "keywords": "ordini incompleto lancio uscita"
                },
                "operations": {
                    "title": "Operazioni da eseguire",
                    "description": "Elenco delle operazioni da eseguire generate da un ordine in esecuzione",
                    "keywords": "operazioni esegui eseguire"
                },
                "missions": {
                    "title": "Missioni",
                    "description": "Elenco delle missioni in esecuzioni associate ad una riga di esegui",
                    "keywords": "Missioni esecuzione"
                },
                "report_dry": {
                    "title": "Flow Check - Dry Report",
                    "description": "Report di controllo flusso con analisi delle ultime 24 ore del magazzino dry. Mostra statistiche e anomalie rilevate.",
                    "keywords": "report dry flow check analisi"
                },
                "report_frozen": {
                    "title": "Flow Check - Frozen Report",
                    "description": "Report di controllo flusso con analisi delle ultime 24 ore del magazzino frozen. Mostra statistiche e anomalie rilevate.",
                    "keywords": "report frozen flow check analisi"
                },
                "custom_dashboard": {
                    "title": "Dashboard Custom",
                    "description": "Visualizzazione personalizzata con grafici e KPI principali.",
                    "keywords": "esempio custom dashboard"
                }
            },
            "badges": {
                "top_100": "Top 100",
                "xml": "XML",
                "entry": "Ingresso",
                "notices": "Avvisi",
                "incomplete": "Incompleto",
                "orders": "Ordini",
                "exit": "Uscita",
                "operations": "Operazioni",
                "execute": "Esegui",
                "missions": "Missioni",
                "executions": "Esecuzioni",
                "24h": "24h",
                "live": "Live",
                "dashboard": "Dashboard",
                "coming_soon": "Coming Soon"
            },
            "xml_popup": {
                "title": "XML Content",
                "copy": "Copia",
                "copied": "Copiato!",
                "error": "Errore!",
                "close": "Chiudi",
                "click_details": "🔍 Click per dettagli"
            },
            "table": {
                "row_number": "#",
                "empty_cell": "—",
                "status": {
                    "completed": "COMPL",
                    "waiting": "WAIT",
                    "error": "ERR"
                }
            },
            "language_selector": {
                "change_language": "Cambia lingua",
                "current": "Lingua corrente: {language}"
            }
        }
        
        # Traduzioni inglesi
        en_translations = {
            "meta": {
                "language_name": "English",
                "language_code": "en"
            },
            "header": {
                "title": "Systore API Dashboard",
                "subtitle": "View and manage your Plant data",
                "home_aria": "Homepage"
            },
            "footer": {
                "copyright": "© {year} Database Management System | Powered by SystemLogistics"
            },
            "search": {
                "placeholder": "🔍 Search tables, reports or views...",
                "table_placeholder": "🔍 Search in table...",
                "clear": "Clear",
                "no_results": "🔍 No results found for your search.",
                "results_count": "{visible} / {total} rows"
            },
            "categories": {
                "import_export": "Import/Export Management",
                "movement": "Movement Management",
                "reports": "Reports and Analysis",
                "custom": "Custom Views"
            },
            "cards": {
                "import": {
                    "title": "IMPORT",
                    "description": "View the last 100 records from HOST_IMPORT table sorted by date. Includes advanced XML formatting.",
                    "keywords": "import host xml table"
                },
                "export": {
                    "title": "EXPORT",
                    "description": "View the last 100 records from HOST_EXPORT table sorted by date. Includes advanced XML formatting.",
                    "keywords": "export host xml table"
                },
                "entry_notices": {
                    "title": "Entry Notices",
                    "description": "View entry notices that are waiting, executing or incomplete",
                    "keywords": "notices entry waiting incomplete"
                },
                "launch_orders": {
                    "title": "Launch Orders",
                    "description": "View all exit orders waiting for execution, executing or incomplete.",
                    "keywords": "orders incomplete launch exit"
                },
                "operations": {
                    "title": "Operations to Execute",
                    "description": "List of operations to execute generated by an order in execution",
                    "keywords": "operations execute run"
                },
                "missions": {
                    "title": "Missions",
                    "description": "List of missions in execution associated with an execute row",
                    "keywords": "Missions execution"
                },
                "report_dry": {
                    "title": "Flow Check - Dry Report",
                    "description": "Flow control report with 24-hour analysis of the dry warehouse. Shows statistics and detected anomalies.",
                    "keywords": "report dry flow check analysis"
                },
                "report_frozen": {
                    "title": "Flow Check - Frozen Report",
                    "description": "Flow control report with 24-hour analysis of the frozen warehouse. Shows statistics and detected anomalies.",
                    "keywords": "report frozen flow check analysis"
                },
                "custom_dashboard": {
                    "title": "Custom Dashboard",
                    "description": "Custom view with charts and main KPIs.",
                    "keywords": "example custom dashboard"
                }
            },
            "badges": {
                "top_100": "Top 100",
                "xml": "XML",
                "entry": "Entry",
                "notices": "Notices",
                "incomplete": "Incomplete",
                "orders": "Orders",
                "exit": "Exit",
                "operations": "Operations",
                "execute": "Execute",
                "missions": "Missions",
                "executions": "Executions",
                "24h": "24h",
                "live": "Live",
                "dashboard": "Dashboard",
                "coming_soon": "Coming Soon"
            },
            "xml_popup": {
                "title": "XML Content",
                "copy": "Copy",
                "copied": "Copied!",
                "error": "Error!",
                "close": "Close",
                "click_details": "🔍 Click for details"
            },
            "table": {
                "row_number": "#",
                "empty_cell": "—",
                "status": {
                    "completed": "COMPL",
                    "waiting": "WAIT",
                    "error": "ERR"
                }
            },
            "language_selector": {
                "change_language": "Change language",
                "current": "Current language: {language}"
            }
        }
        
        # Salva i file JSON
        with open(self.translations_dir / 'it.json', 'w', encoding='utf-8') as f:
            json.dump(it_translations, f, ensure_ascii=False, indent=2)
        
        with open(self.translations_dir / 'en.json', 'w', encoding='utf-8') as f:
            json.dump(en_translations, f, ensure_ascii=False, indent=2)
        
        print("✓ File di traduzione creati: it.json, en.json")


# Istanza globale del gestore traduzioni
translation_manager = TranslationManager()


# Decoratore per iniettare automaticamente le traduzioni nei template
def inject_translations(f):
    """Decoratore che inietta le funzioni di traduzione nei template"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Aggiungi le funzioni di traduzione al contesto
        from flask import g
        g.t = translation_manager.get
        g.current_lang = translation_manager.get_current_language()
        g.supported_langs = translation_manager.supported_languages
        return f(*args, **kwargs)
    return decorated_function