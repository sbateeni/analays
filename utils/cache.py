import json
from datetime import timedelta
import hashlib

class AnalysisCache:
    """فئة للتعامل مع التخزين المؤقت لنتائج التحليل"""
    
    def __init__(self):
        self.cache = {}  # تخزين مؤقت في الذاكرة
        self.default_expiry = timedelta(hours=24)
        self.enabled = True
    
    def enable(self):
        """تفعيل التخزين المؤقت"""
        self.enabled = True
    
    def disable(self):
        """تعطيل التخزين المؤقت"""
        self.enabled = False
    
    def set_expiry(self, minutes: int):
        """تعيين مدة الصلاحية الافتراضية"""
        self.default_expiry = timedelta(minutes=minutes)
    
    def _generate_key(self, text, stage):
        """توليد مفتاح فريد للتخزين المؤقت"""
        text_hash = hashlib.md5(text.encode()).hexdigest()
        return f"analysis:{text_hash}:stage:{stage}"
    
    def get_cached_result(self, text, stage):
        """استرجاع نتيجة مخزنة مؤقتاً"""
        if not self.enabled:
            return None
            
        key = self._generate_key(text, stage)
        if key in self.cache:
            return self.cache[key]
        return None
    
    def cache_result(self, text, stage, result, expiry=None):
        """تخزين نتيجة في الذاكرة المؤقتة"""
        if not self.enabled:
            return
            
        key = self._generate_key(text, stage)
        self.cache[key] = result
    
    def invalidate_cache(self, text, stage=None):
        """إبطال نتيجة مخزنة مؤقتاً"""
        if stage:
            key = self._generate_key(text, stage)
            if key in self.cache:
                del self.cache[key]
        else:
            # إبطال جميع النتائج لنفس النص
            for key in list(self.cache.keys()):
                if text in key:
                    del self.cache[key]
    
    def get_cache_stats(self):
        """الحصول على إحصائيات التخزين المؤقت"""
        return {
            'enabled': self.enabled,
            'size': len(self.cache),
            'default_expiry': str(self.default_expiry)
        }
    
    def clear_all_cache(self):
        """مسح جميع النتائج المخزنة مؤقتاً"""
        self.cache.clear() 