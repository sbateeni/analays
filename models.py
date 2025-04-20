from sqlalchemy import Column, Integer, String, Text, Float, DateTime, ForeignKey, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Case(Base):
    __tablename__ = 'cases'
    
    id = Column(Integer, primary_key=True)
    title = Column(String(200))
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    analyses = relationship("Analysis", back_populates="case")

class Analysis(Base):
    __tablename__ = 'analyses'
    
    id = Column(Integer, primary_key=True)
    case_id = Column(Integer, ForeignKey('cases.id'))
    stage = Column(Integer)
    content = Column(Text)
    confidence_score = Column(Float)
    execution_time = Column(Float)
    verification_status = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)
    case = relationship("Case", back_populates="analyses")

class PerformanceMetric(Base):
    __tablename__ = 'performance_metrics'
    
    id = Column(Integer, primary_key=True)
    stage = Column(Integer)
    metric_name = Column(String(50))
    metric_value = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow) 