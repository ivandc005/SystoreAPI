"""
Cache Manager - Gestisce cache dei metadati e configurazioni
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class CacheManager:
    """Gestisce cache per performance ottimali"""
    
    def __init__(self, cache_dir='metadata'):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
    
    def is_cache_valid(self, cache_file, max_age_hours=1):
        """
        Verifica se la cache è ancora valida
        
        Args:
            cache_file: Path del file cache
            max_age_hours: Età massima in ore
        
        Returns:
            bool: True se cache valida
        """
        
        if not cache_file.exists():
            return False
        
        # Controlla età file
        file_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
        age = datetime.now() - file_time
        
        if age > timedelta(hours=max_age_hours):
            logger.info(f"Cache expired for {cache_file.name} (age: {age})")
            return False
        
        return True
    
    def load_json_cache(self, cache_name):
        """
        Carica cache JSON
        
        Args:
            cache_name: Nome file cache (senza estensione)
        
        Returns:
            dict: Dati dalla cache o None se non valida
        """
        
        cache_file = self.cache_dir / f"{cache_name}.json"
        
        if not self.is_cache_valid(cache_file):
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            logger.debug(f"Loaded cache: {cache_name}")
            return data
            
        except Exception as e:
            logger.error(f"Error loading cache {cache_name}: {e}")
            return None
    
    def save_json_cache(self, cache_name, data):
        """
        Salva cache JSON
        
        Args:
            cache_name: Nome file cache
            data: Dati da salvare
        """
        
        cache_file = self.cache_dir / f"{cache_name}.json"
        
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False, default=str)
            
            logger.debug(f"Saved cache: {cache_name}")
            
        except Exception as e:
            logger.error(f"Error saving cache {cache_name}: {e}")
    
    def invalidate_cache(self, cache_name=None):
        """
        Invalida cache (elimina file)
        
        Args:
            cache_name: Nome cache specifica, o None per tutto
        """
        
        if cache_name:
            cache_file = self.cache_dir / f"{cache_name}.json"
            if cache_file.exists():
                cache_file.unlink()
                logger.info(f"Invalidated cache: {cache_name}")
        else:
            # Elimina tutte le cache
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
            logger.info("Invalidated all caches")
    
    def get_cache_info(self):
        """
        Ottiene informazioni su tutte le cache
        
        Returns:
            dict: Info su ogni cache
        """
        
        cache_info = {}
        
        for cache_file in self.cache_dir.glob("*.json"):
            cache_name = cache_file.stem
            file_time = datetime.fromtimestamp(cache_file.stat().st_mtime)
            age = datetime.now() - file_time
            size_kb = cache_file.stat().st_size / 1024
            
            cache_info[cache_name] = {
                'file': cache_file.name,
                'last_modified': file_time.isoformat(),
                'age_hours': age.total_seconds() / 3600,
                'size_kb': round(size_kb, 2),
                'valid': self.is_cache_valid(cache_file)
            }
        
        return cache_info