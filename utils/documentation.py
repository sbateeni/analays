import os
import json
from typing import Dict, List, Optional
from datetime import datetime
import markdown
from bs4 import BeautifulSoup

class DocumentationManager:
    """فئة لإدارة التوثيق ونظام المساعدة"""
    
    def __init__(self):
        self.docs_path = 'docs'
        self.help_path = os.path.join(self.docs_path, 'help')
        self.examples_path = os.path.join(self.docs_path, 'examples')
        self.faq_path = os.path.join(self.docs_path, 'faq')
        
        # إنشاء المجلدات اللازمة
        for path in [self.docs_path, self.help_path, self.examples_path, self.faq_path]:
            os.makedirs(path, exist_ok=True)
    
    def add_help_article(self, title: str, content: str, category: str) -> str:
        """إضافة مقال مساعدة جديد"""
        # تنظيف العنوان لاستخدامه في اسم الملف
        filename = self._clean_filename(title)
        filepath = os.path.join(self.help_path, f"{filename}.md")
        
        # إنشاء محتوى Markdown
        markdown_content = f"""# {title}

{content}

---
التصنيف: {category}
تاريخ الإنشاء: {datetime.now().strftime('%Y-%m-%d')}
"""
        
        # حفظ الملف
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        return filepath
    
    def add_example(self, title: str, description: str, code: str, output: str) -> str:
        """إضافة مثال جديد"""
        filename = self._clean_filename(title)
        filepath = os.path.join(self.examples_path, f"{filename}.md")
        
        markdown_content = f"""# {title}

## الوصف
{description}

## الكود
```python
{code}
```

## النتيجة
```
{output}
```

---
تاريخ الإضافة: {datetime.now().strftime('%Y-%m-%d')}
"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        return filepath
    
    def add_faq(self, question: str, answer: str, category: str) -> str:
        """إضافة سؤال شائع جديد"""
        filename = self._clean_filename(question[:50])  # استخدام أول 50 حرف من السؤال
        filepath = os.path.join(self.faq_path, f"{filename}.md")
        
        markdown_content = f"""# {question}

{answer}

---
التصنيف: {category}
تاريخ الإضافة: {datetime.now().strftime('%Y-%m-%d')}
"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        return filepath
    
    def search_documentation(self, query: str) -> List[Dict]:
        """البحث في التوثيق"""
        results = []
        
        # البحث في جميع الملفات
        for root, _, files in os.walk(self.docs_path):
            for file in files:
                if file.endswith('.md'):
                    filepath = os.path.join(root, file)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        content = f.read()
                        
                    if query.lower() in content.lower():
                        # تحويل Markdown إلى نص عادي للعرض
                        html = markdown.markdown(content)
                        soup = BeautifulSoup(html, 'html.parser')
                        text = soup.get_text()
                        
                        results.append({
                            'title': self._get_title_from_markdown(content),
                            'path': filepath,
                            'type': self._get_doc_type(filepath),
                            'excerpt': self._get_excerpt(text, query)
                        })
        
        return results
    
    def get_help_categories(self) -> List[str]:
        """الحصول على قائمة تصنيفات المساعدة"""
        categories = set()
        
        for file in os.listdir(self.help_path):
            if file.endswith('.md'):
                filepath = os.path.join(self.help_path, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    category = self._extract_category(content)
                    if category:
                        categories.add(category)
        
        return sorted(list(categories))
    
    def generate_documentation_index(self) -> str:
        """إنشاء فهرس للتوثيق"""
        index_content = "# فهرس التوثيق\n\n"
        
        # إضافة قسم المساعدة
        index_content += "## دليل المساعدة\n\n"
        for category in self.get_help_categories():
            index_content += f"### {category}\n\n"
            articles = self._get_articles_by_category(category)
            for article in articles:
                index_content += f"- [{article['title']}]({article['path']})\n"
            index_content += "\n"
        
        # إضافة قسم الأمثلة
        index_content += "## الأمثلة\n\n"
        for example in self._get_examples():
            index_content += f"- [{example['title']}]({example['path']})\n"
        index_content += "\n"
        
        # إضافة قسم الأسئلة الشائعة
        index_content += "## الأسئلة الشائعة\n\n"
        for faq in self._get_faqs():
            index_content += f"- [{faq['title']}]({faq['path']})\n"
        
        # حفظ الفهرس
        index_path = os.path.join(self.docs_path, 'index.md')
        with open(index_path, 'w', encoding='utf-8') as f:
            f.write(index_content)
        
        return index_path
    
    def _clean_filename(self, text: str) -> str:
        """تنظيف النص لاستخدامه كاسم ملف"""
        return "".join(c for c in text if c.isalnum() or c in (' ', '-', '_')).strip().replace(' ', '-')
    
    def _get_title_from_markdown(self, content: str) -> str:
        """استخراج العنوان من محتوى Markdown"""
        lines = content.split('\n')
        for line in lines:
            if line.startswith('# '):
                return line[2:].strip()
        return "بدون عنوان"
    
    def _get_doc_type(self, filepath: str) -> str:
        """تحديد نوع الوثيقة من مسارها"""
        if 'help' in filepath:
            return 'مساعدة'
        elif 'examples' in filepath:
            return 'مثال'
        elif 'faq' in filepath:
            return 'سؤال شائع'
        return 'وثيقة'
    
    def _get_excerpt(self, text: str, query: str, length: int = 200) -> str:
        """استخراج مقتطف من النص يحتوي على كلمة البحث"""
        index = text.lower().find(query.lower())
        if index == -1:
            return text[:length] + '...'
        
        start = max(0, index - 100)
        end = min(len(text), index + 100)
        excerpt = text[start:end]
        
        if start > 0:
            excerpt = '...' + excerpt
        if end < len(text):
            excerpt = excerpt + '...'
            
        return excerpt
    
    def _extract_category(self, content: str) -> Optional[str]:
        """استخراج التصنيف من محتوى الملف"""
        for line in content.split('\n'):
            if line.startswith('التصنيف:'):
                return line.replace('التصنيف:', '').strip()
        return None
    
    def _get_articles_by_category(self, category: str) -> List[Dict]:
        """الحصول على المقالات حسب التصنيف"""
        articles = []
        
        for file in os.listdir(self.help_path):
            if file.endswith('.md'):
                filepath = os.path.join(self.help_path, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if category == self._extract_category(content):
                        articles.append({
                            'title': self._get_title_from_markdown(content),
                            'path': filepath
                        })
        
        return sorted(articles, key=lambda x: x['title'])
    
    def _get_examples(self) -> List[Dict]:
        """الحصول على قائمة الأمثلة"""
        examples = []
        
        for file in os.listdir(self.examples_path):
            if file.endswith('.md'):
                filepath = os.path.join(self.examples_path, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    examples.append({
                        'title': self._get_title_from_markdown(content),
                        'path': filepath
                    })
        
        return sorted(examples, key=lambda x: x['title'])
    
    def _get_faqs(self) -> List[Dict]:
        """الحصول على قائمة الأسئلة الشائعة"""
        faqs = []
        
        for file in os.listdir(self.faq_path):
            if file.endswith('.md'):
                filepath = os.path.join(self.faq_path, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    faqs.append({
                        'title': self._get_title_from_markdown(content),
                        'path': filepath
                    })
        
        return sorted(faqs, key=lambda x: x['title']) 