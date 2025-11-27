#!/usr/bin/env python3
"""
Script di verifica completezza traduzioni
Controlla che tutte le lingue abbiano le stesse chiavi
"""

import json
from pathlib import Path
from collections import defaultdict

class TranslationChecker:
    """Verifica la completezza e consistenza delle traduzioni"""
    
    def __init__(self, translations_dir='translations'):
        self.translations_dir = Path(translations_dir)
        self.translations = {}
        self.all_keys = defaultdict(set)
        
    def load_translations(self):
        """Carica tutte le traduzioni"""
        if not self.translations_dir.exists():
            print(f"❌ Directory {self.translations_dir} non trovata!")
            return False
        
        json_files = list(self.translations_dir.glob('*.json'))
        if not json_files:
            print(f"❌ Nessun file JSON trovato in {self.translations_dir}")
            return False
        
        print(f"\n📁 Caricamento traduzioni da {self.translations_dir}/")
        print("=" * 60)
        
        for lang_file in json_files:
            lang_code = lang_file.stem
            try:
                with open(lang_file, 'r', encoding='utf-8') as f:
                    self.translations[lang_code] = json.load(f)
                    keys = self._extract_keys(self.translations[lang_code])
                    self.all_keys[lang_code] = set(keys)
                    print(f"✓ {lang_code}.json: {len(keys)} chiavi")
            except json.JSONDecodeError as e:
                print(f"❌ Errore nel file {lang_file}: {e}")
                return False
        
        print("=" * 60 + "\n")
        return True
    
    def _extract_keys(self, data, prefix=''):
        """Estrae ricorsivamente tutte le chiavi da un dizionario"""
        keys = []
        for key, value in data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, dict):
                keys.extend(self._extract_keys(value, full_key))
            else:
                keys.append(full_key)
        
        return keys
    
    def check_completeness(self):
        """Verifica che tutte le lingue abbiano le stesse chiavi"""
        if not self.translations:
            print("❌ Nessuna traduzione caricata!")
            return
        
        print("🔍 VERIFICA COMPLETEZZA TRADUZIONI")
        print("=" * 60)
        
        # Trova tutte le chiavi uniche
        all_unique_keys = set()
        for keys in self.all_keys.values():
            all_unique_keys.update(keys)
        
        total_keys = len(all_unique_keys)
        print(f"📊 Totale chiavi uniche: {total_keys}\n")
        
        # Verifica per ogni lingua
        issues_found = False
        for lang_code in sorted(self.translations.keys()):
            lang_keys = self.all_keys[lang_code]
            missing_keys = all_unique_keys - lang_keys
            extra_keys = lang_keys - all_unique_keys
            
            if missing_keys or extra_keys:
                issues_found = True
                print(f"\n⚠️  {lang_code.upper()}: PROBLEMI TROVATI")
                print("-" * 60)
                
                if missing_keys:
                    print(f"  ❌ Chiavi mancanti ({len(missing_keys)}):")
                    for key in sorted(missing_keys)[:10]:  # Mostra max 10
                        print(f"     - {key}")
                    if len(missing_keys) > 10:
                        print(f"     ... e altre {len(missing_keys) - 10} chiavi")
                
                if extra_keys:
                    print(f"  ⚡ Chiavi extra ({len(extra_keys)}):")
                    for key in sorted(extra_keys)[:10]:
                        print(f"     - {key}")
                    if len(extra_keys) > 10:
                        print(f"     ... e altre {len(extra_keys) - 10} chiavi")
            else:
                print(f"✓ {lang_code.upper()}: Completo ({len(lang_keys)} chiavi)")
        
        print("\n" + "=" * 60)
        
        if issues_found:
            print("❌ TROVATI PROBLEMI - Controlla le chiavi mancanti/extra sopra")
            return False
        else:
            print("✅ TUTTO OK - Tutte le lingue sono complete e consistenti!")
            return True
    
    def show_statistics(self):
        """Mostra statistiche sulle traduzioni"""
        print("\n📊 STATISTICHE TRADUZIONI")
        print("=" * 60)
        
        for lang_code in sorted(self.translations.keys()):
            lang_data = self.translations[lang_code]
            lang_name = lang_data.get('meta', {}).get('language_name', lang_code)
            
            # Conta diverse tipologie
            total_keys = len(self.all_keys[lang_code])
            
            # Stima dimensione
            json_str = json.dumps(lang_data, ensure_ascii=False, indent=2)
            size_kb = len(json_str.encode('utf-8')) / 1024
            
            print(f"\n🌐 {lang_name} ({lang_code})")
            print(f"   Chiavi totali: {total_keys}")
            print(f"   Dimensione: {size_kb:.2f} KB")
        
        print("\n" + "=" * 60)
    
    def compare_values(self):
        """Confronta i valori per trovare possibili traduzioni mancanti"""
        print("\n🔎 ANALISI VALORI")
        print("=" * 60)
        
        # Prendi la prima lingua come riferimento
        reference_lang = list(self.translations.keys())[0]
        
        print(f"Lingua di riferimento: {reference_lang}")
        print("\nChiavi con possibili traduzioni identiche (potrebbero essere mancanti):")
        print("-" * 60)
        
        found_issues = False
        
        for key in sorted(self.all_keys[reference_lang]):
            values = {}
            for lang_code in self.translations.keys():
                if key in self.all_keys[lang_code]:
                    value = self._get_value_by_key(self.translations[lang_code], key)
                    if value:
                        values[lang_code] = value
            
            # Se tutti i valori sono uguali, potrebbe essere un problema
            if len(values) > 1 and len(set(values.values())) == 1:
                # Escludi casi validi (codici, numeri, etc.)
                first_value = list(values.values())[0]
                if not self._is_valid_identical(first_value):
                    found_issues = True
                    print(f"\n⚠️  {key}")
                    print(f"   Valore: '{first_value}'")
                    print(f"   Lingue: {', '.join(values.keys())}")
        
        if not found_issues:
            print("\n✓ Nessun problema rilevato")
        
        print("\n" + "=" * 60)
    
    def _get_value_by_key(self, data, key):
        """Recupera un valore usando la notazione dot"""
        keys = key.split('.')
        for k in keys:
            if isinstance(data, dict) and k in data:
                data = data[k]
            else:
                return None
        return data if not isinstance(data, dict) else None
    
    def _is_valid_identical(self, value):
        """Verifica se è valido avere lo stesso valore in tutte le lingue"""
        # Codici di stato, numeri, simboli, etc.
        if not isinstance(value, str):
            return True
        
        # Molto corto (es: "#", "XML", "ID")
        if len(value) <= 5:
            return True
        
        # Contiene solo maiuscole/numeri/simboli
        if value.replace('_', '').replace('-', '').isalnum() and value.isupper():
            return True
        
        # Brand names, technical terms
        technical_terms = ['XML', 'JSON', 'API', 'ID', 'CSV', 'URL', 'HTTP']
        if any(term in value for term in technical_terms):
            return True
        
        return False
    
    def export_missing_template(self, output_file='missing_translations.json'):
        """Esporta un template con le chiavi mancanti per ogni lingua"""
        print(f"\n📝 ESPORTAZIONE TEMPLATE CHIAVI MANCANTI")
        print("=" * 60)
        
        all_unique_keys = set()
        for keys in self.all_keys.values():
            all_unique_keys.update(keys)
        
        for lang_code in self.translations.keys():
            missing = all_unique_keys - self.all_keys[lang_code]
            
            if missing:
                output = Path(f"missing_{lang_code}.json")
                
                # Crea struttura
                template = {}
                for key in sorted(missing):
                    self._set_nested_key(template, key, f"[TRANSLATE: {key}]")
                
                with open(output, 'w', encoding='utf-8') as f:
                    json.dump(template, f, ensure_ascii=False, indent=2)
                
                print(f"✓ {output}: {len(missing)} chiavi mancanti esportate")
        
        print("=" * 60)
    
    def _set_nested_key(self, data, key, value):
        """Imposta una chiave nidificata in un dizionario"""
        keys = key.split('.')
        for k in keys[:-1]:
            if k not in data:
                data[k] = {}
            data = data[k]
        data[keys[-1]] = value


def main():
    """Funzione principale"""
    checker = TranslationChecker()
    
    print("\n" + "=" * 60)
    print("🌍 TRANSLATION CHECKER - Systore API Dashboard")
    print("=" * 60)
    
    # Carica traduzioni
    if not checker.load_translations():
        return
    
    # Verifica completezza
    is_complete = checker.check_completeness()
    
    # Mostra statistiche
    checker.show_statistics()
    
    # Analizza valori
    checker.compare_values()
    
    # Se ci sono problemi, esporta template
    if not is_complete:
        checker.export_missing_template()
    
    print("\n✅ Verifica completata!\n")


if __name__ == "__main__":
    main()