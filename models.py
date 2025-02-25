from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Float, JSON, Table, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

# جدول العلاقة بين القضايا والتصنيفات
case_categories = Table('case_categories', Base.metadata,
    Column('case_id', Integer, ForeignKey('cases.id')),
    Column('category_id', Integer, ForeignKey('categories.id'))
)

class Case(Base):
    """نموذج القضية"""
    __tablename__ = 'cases'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    case_number = Column(String(50), unique=True)
    case_type = Column(String(50))  # مدني، جنائي، تجاري، إداري
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # العلاقات
    analyses = relationship("Analysis", back_populates="case")
    categories = relationship("Category", secondary=case_categories, back_populates="cases")
    comments = relationship("Comment", back_populates="case")
    documents = relationship("Document", back_populates="case")

class Analysis(Base):
    """نموذج التحليل"""
    __tablename__ = 'analyses'
    
    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey('cases.id'))
    stage = Column(Integer)  # رقم المرحلة
    content = Column(Text)  # محتوى التحليل
    verification_status = Column(String(50))  # حالة التحقق
    sources = Column(JSON)  # المصادر والمراجع
    model_used = Column(String(50))  # النموذج المستخدم
    confidence_score = Column(Float)  # درجة الثقة
    execution_time = Column(Float)  # وقت التنفيذ
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # العلاقات
    case = relationship("Case", back_populates="analyses")
    comments = relationship("Comment", back_populates="analysis")

class Category(Base):
    """نموذج التصنيف"""
    __tablename__ = 'categories'
    
    id = Column(Integer, primary_key=True)
    name = Column(String(100), unique=True)
    description = Column(Text)
    
    # العلاقات
    cases = relationship("Case", secondary=case_categories, back_populates="categories")

class Comment(Base):
    """نموذج التعليق"""
    __tablename__ = 'comments'
    
    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey('cases.id'))
    analysis_id = Column(Integer, ForeignKey('analyses.id'), nullable=True)
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # العلاقات
    case = relationship("Case", back_populates="comments")
    analysis = relationship("Analysis", back_populates="comments")

class Document(Base):
    """نموذج المستند"""
    __tablename__ = 'documents'
    
    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey('cases.id'))
    title = Column(String(200))
    file_path = Column(String(500))
    file_type = Column(String(50))  # نوع الملف (PDF, Word, Excel)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # العلاقات
    case = relationship("Case", back_populates="documents")

class LegalReference(Base):
    """نموذج المرجع القانوني"""
    __tablename__ = 'legal_references'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(200))
    content = Column(Text)
    reference_type = Column(String(50))  # قانون، حكم قضائي، مرسوم
    publication_date = Column(DateTime)
    last_update = Column(DateTime)
    source_url = Column(String(500))
    is_active = Column(Boolean, default=True)

class PerformanceMetric(Base):
    """نموذج مؤشرات الأداء"""
    __tablename__ = 'performance_metrics'
    
    id = Column(Integer, primary_key=True)
    metric_name = Column(String(100))
    metric_value = Column(Float)
    case_id = Column(Integer, ForeignKey('cases.id'), nullable=True)
    analysis_id = Column(Integer, ForeignKey('analyses.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

# دالة لإنشاء جميع الجداول
def create_tables(engine):
    Base.metadata.create_all(engine) 