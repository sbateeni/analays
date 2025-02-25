from deep_translator import GoogleTranslator
import json
import os
from typing import Dict, List, Union

class LegalTranslator:
    """فئة للتعامل مع الترجمة القانونية"""
    
    def __init__(self):
        self.translator = GoogleTranslator(source='ar', target='en')
        self.legal_terms_path = 'data/legal_terms.json'
        self.legal_terms = self._load_legal_terms()
    
    def _load_legal_terms(self) -> Dict[str, str]:
        """تحميل المصطلحات القانونية من ملف JSON"""
        if os.path.exists(self.legal_terms_path):
            try:
                with open(self.legal_terms_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except json.JSONDecodeError:
                print(f"Error loading legal terms from {self.legal_terms_path}")
                return {}
        return {}
    
    def _save_legal_terms(self):
        """حفظ المصطلحات القانونية إلى ملف JSON"""
        os.makedirs(os.path.dirname(self.legal_terms_path), exist_ok=True)
        with open(self.legal_terms_path, 'w', encoding='utf-8') as f:
            json.dump(self.legal_terms, f, ensure_ascii=False, indent=2)
    
    def add_legal_term(self, arabic: str, english: str):
        """إضافة مصطلح قانوني جديد"""
        self.legal_terms[arabic] = english
        self._save_legal_terms()
    
    def translate_text(self, text: str, preserve_legal_terms: bool = True) -> str:
        """ترجمة النص مع الحفاظ على المصطلحات القانونية"""
        if preserve_legal_terms:
            # استبدال المصطلحات القانونية برموز مؤقتة
            placeholders = {}
            for ar_term, en_term in self.legal_terms.items():
                if ar_term in text:
                    placeholder = f"__LEGAL_TERM_{len(placeholders)}__"
                    text = text.replace(ar_term, placeholder)
                    placeholders[placeholder] = en_term
            
            # ترجمة النص
            translated = self.translator.translate(text)
            
            # استعادة المصطلحات القانونية
            for placeholder, term in placeholders.items():
                translated = translated.replace(placeholder, term)
            
            return translated
        else:
            return self.translator.translate(text)
    
    def translate_legal_document(self, document: Dict[str, Union[str, List[str]]]) -> Dict[str, Union[str, List[str]]]:
        """ترجمة وثيقة قانونية كاملة"""
        translated_doc = {}
        
        for key, value in document.items():
            if isinstance(value, str):
                translated_doc[key] = self.translate_text(value)
            elif isinstance(value, list):
                translated_doc[key] = [self.translate_text(item) if isinstance(item, str) else item for item in value]
            else:
                translated_doc[key] = value
        
        return translated_doc
    
    def batch_translate(self, texts: List[str]) -> List[str]:
        """ترجمة مجموعة من النصوص دفعة واحدة"""
        return [self.translate_text(text) for text in texts]
    
    def suggest_translation(self, text: str) -> List[str]:
        """اقتراح ترجمات بديلة للنص"""
        # يمكن تنفيذ هذا باستخدام نماذج مختلفة أو خدمات ترجمة متعددة
        translations = []
        
        # الترجمة الأساسية
        translations.append(self.translate_text(text))
        
        # يمكن إضافة ترجمات من مصادر أخرى هنا
        
        return translations
    
    def validate_translation(self, arabic: str, english: str) -> bool:
        """التحقق من صحة الترجمة"""
        # يمكن تنفيذ التحقق باستخدام نماذج لغوية أو قواعد محددة
        # هذا مثال بسيط
        back_translation = self.translator.translate(english, source='en', target='ar')
        similarity = self._calculate_similarity(arabic, back_translation)
        return similarity > 0.7
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """حساب درجة التشابه بين نصين"""
        # يمكن استخدام خوارزميات مثل Levenshtein distance
        # هذا مثال بسيط
        words1 = set(text1.split())
        words2 = set(text2.split())
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        return len(intersection) / len(union) if union else 0.0 