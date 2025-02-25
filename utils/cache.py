import redis
import json
from datetime import timedelta
import hashlib

class AnalysisCache:
    """فئة للتعامل مع التخزين المؤقت لنتائج التحليل"""
    
    def __init__(self, host='localhost', port=6379, db=0):
        self.redis = redis.Redis(host=host, port=port, db=db, decode_responses=True)
        self.default_expiry = timedelta(hours=24)  # مدة الصلاحية الافتراضية
        self.enabled = True  # حالة التخزين المؤقت
    
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
        # استخدام MD5 لتوليد مفتاح قصير وفريد
        text_hash = hashlib.md5(text.encode()).hexdigest()
        return f"analysis:{text_hash}:stage:{stage}"
    
    def get_cached_result(self, text, stage):
        """استرجاع نتيجة مخزنة مؤقتاً"""
        key = self._generate_key(text, stage)
        cached = self.redis.get(key)
        if cached:
            try:
                return json.loads(cached)
            except json.JSONDecodeError:
                return None
        return None
    
    def cache_result(self, text, stage, result, expiry=None):
        """تخزين نتيجة في الذاكرة المؤقتة"""
        key = self._generate_key(text, stage)
        try:
            # تحويل النتيجة إلى JSON
            result_json = json.dumps(result, ensure_ascii=False)
            # تخزين النتيجة
            self.redis.set(
                key,
                result_json,
                ex=expiry or self.default_expiry
            )
            return True
        except Exception as e:
            print(f"Error caching result: {e}")
            return False
    
    def invalidate_cache(self, text, stage=None):
        """إبطال التخزين المؤقت لنص معين"""
        if stage:
            # إبطال مرحلة محددة
            key = self._generate_key(text, stage)
            self.redis.delete(key)
        else:
            # إبطال جميع المراحل
            text_hash = hashlib.md5(text.encode()).hexdigest()
            pattern = f"analysis:{text_hash}:stage:*"
            keys = self.redis.keys(pattern)
            if keys:
                self.redis.delete(*keys)
    
    def get_cache_stats(self):
        """الحصول على إحصائيات التخزين المؤقت"""
        info = self.redis.info()
        return {
            'used_memory': info.get('used_memory_human'),
            'hits': info.get('keyspace_hits'),
            'misses': info.get('keyspace_misses'),
            'total_keys': self.redis.dbsize()
        }
    
    def clear_all_cache(self):
        """مسح جميع البيانات المخزنة مؤقتاً"""
        self.redis.flushdb() 