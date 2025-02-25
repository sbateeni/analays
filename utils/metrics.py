from datetime import datetime
from typing import Dict, List, Optional
import json
import os
import matplotlib.pyplot as plt
from models import PerformanceMetric, Analysis
from sqlalchemy.orm import Session

class PerformanceTracker:
    """فئة لتتبع وتحليل مؤشرات الأداء"""
    
    def __init__(self, db_session: Session):
        self.db = db_session
        self.metrics_path = 'data/metrics'
        os.makedirs(self.metrics_path, exist_ok=True)
    
    def record_metric(self, 
                     metric_name: str, 
                     metric_value: float, 
                     case_id: Optional[int] = None,
                     analysis_id: Optional[int] = None):
        """تسجيل مؤشر أداء جديد"""
        metric = PerformanceMetric(
            metric_name=metric_name,
            metric_value=metric_value,
            case_id=case_id,
            analysis_id=analysis_id
        )
        self.db.add(metric)
        self.db.commit()
    
    def get_metrics(self, 
                   metric_name: Optional[str] = None,
                   case_id: Optional[int] = None,
                   analysis_id: Optional[int] = None,
                   stage: Optional[int] = None,
                   start_date: Optional[datetime] = None,
                   end_date: Optional[datetime] = None) -> List[Dict]:
        """استرجاع مؤشرات الأداء مع إمكانية التصفية"""
        query = self.db.query(PerformanceMetric)
        
        if metric_name:
            query = query.filter(PerformanceMetric.metric_name == metric_name)
        if case_id:
            query = query.filter(PerformanceMetric.case_id == case_id)
        if analysis_id:
            query = query.filter(PerformanceMetric.analysis_id == analysis_id)
        if stage:
            # Join with Analysis table to filter by stage
            query = query.join(Analysis).filter(Analysis.stage == stage)
        if start_date:
            query = query.filter(PerformanceMetric.created_at >= start_date)
        if end_date:
            query = query.filter(PerformanceMetric.created_at <= end_date)
        
        return query.all()
    
    def calculate_statistics(self, metric_name: str) -> Dict:
        """حساب إحصائيات لمؤشر معين"""
        metrics = self.get_metrics(metric_name=metric_name)
        values = [m.metric_value for m in metrics]
        
        if not values:
            return {}
        
        return {
            'count': len(values),
            'average': sum(values) / len(values),
            'min': min(values),
            'max': max(values),
            'latest': values[-1]
        }
    
    def generate_report(self, 
                       metrics: List[str] = None, 
                       start_date: Optional[datetime] = None,
                       end_date: Optional[datetime] = None) -> Dict:
        """إنشاء تقرير شامل عن الأداء"""
        if metrics is None:
            # استخدام جميع المؤشرات المتوفرة
            metrics = self.db.query(PerformanceMetric.metric_name).distinct().all()
            metrics = [m[0] for m in metrics]
        
        report = {
            'generated_at': datetime.now().isoformat(),
            'period': {
                'start': start_date.isoformat() if start_date else None,
                'end': end_date.isoformat() if end_date else None
            },
            'metrics': {}
        }
        
        for metric in metrics:
            report['metrics'][metric] = self.calculate_statistics(metric)
        
        return report
    
    def save_report(self, report: Dict, filename: Optional[str] = None):
        """حفظ التقرير إلى ملف"""
        if filename is None:
            filename = f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        filepath = os.path.join(self.metrics_path, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        return filepath
    
    def plot_metric_trend(self, 
                         metric_name: str,
                         start_date: Optional[datetime] = None,
                         end_date: Optional[datetime] = None) -> str:
        """رسم اتجاه مؤشر معين"""
        metrics = self.get_metrics(
            metric_name=metric_name,
            start_date=start_date,
            end_date=end_date
        )
        
        dates = [m.created_at for m in metrics]
        values = [m.metric_value for m in metrics]
        
        plt.figure(figsize=(12, 6))
        plt.plot(dates, values, marker='o')
        plt.title(f'اتجاه {metric_name}')
        plt.xlabel('التاريخ')
        plt.ylabel('القيمة')
        plt.xticks(rotation=45)
        plt.grid(True)
        
        # حفظ الرسم البياني
        filename = f"metric_trend_{metric_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        filepath = os.path.join(self.metrics_path, filename)
        plt.savefig(filepath, bbox_inches='tight')
        plt.close()
        
        return filepath
    
    def track_analysis_performance(self, 
                                 case_id: int,
                                 analysis_id: int,
                                 execution_time: float,
                                 confidence_score: float,
                                 verification_status: str):
        """تتبع أداء تحليل معين"""
        metrics = {
            'execution_time': execution_time,
            'confidence_score': confidence_score,
            'verification_success': 1 if verification_status == 'verified' else 0
        }
        
        for name, value in metrics.items():
            self.record_metric(
                metric_name=name,
                metric_value=value,
                case_id=case_id,
                analysis_id=analysis_id
            )
    
    def get_performance_summary(self) -> Dict:
        """الحصول على ملخص الأداء العام"""
        return {
            'average_execution_time': self.calculate_statistics('execution_time').get('average'),
            'average_confidence': self.calculate_statistics('confidence_score').get('average'),
            'verification_success_rate': self.calculate_statistics('verification_success').get('average'),
            'total_analyses': len(self.get_metrics()),
            'unique_cases': len(set(m.case_id for m in self.get_metrics() if m.case_id))
        } 