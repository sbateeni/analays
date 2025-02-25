from flask import Blueprint, request, jsonify
from models import Case, Analysis
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import json
from datetime import datetime

case_bp = Blueprint('case', __name__, url_prefix='/api/cases')

# تهيئة قاعدة البيانات
engine = create_engine('sqlite:///legal_analysis.db')
Session = sessionmaker(bind=engine)

@case_bp.route('/save', methods=['POST'])
def save_case():
    """حفظ قضية جديدة مع نتائج التحليل"""
    try:
        data = request.json
        if not data:
            return jsonify({
                "status": "error",
                "message": "لم يتم استلام بيانات"
            }), 400

        # إنشاء جلسة قاعدة البيانات
        session = Session()

        try:
            # إنشاء قضية جديدة
            case = Case(
                title=data.get('title', 'قضية جديدة'),
                content=data.get('text', ''),
                case_type=data.get('case_type', 'عام'),
                created_at=datetime.utcnow()
            )
            session.add(case)
            session.flush()  # للحصول على معرف القضية

            # حفظ نتائج التحليل
            results = data.get('results', {})
            for stage, result in results.items():
                analysis = Analysis(
                    case_id=case.id,
                    stage=int(stage),
                    content=result if isinstance(result, str) else json.dumps(result, ensure_ascii=False),
                    verification_status='verified' if isinstance(result, dict) and result.get('verification') else 'pending',
                    sources=result.get('sources') if isinstance(result, dict) else None,
                    model_used=data.get('model_used', 'gemini'),
                    confidence_score=result.get('confidence_score', 0.0) if isinstance(result, dict) else 0.0,
                    execution_time=result.get('execution_time', 0.0) if isinstance(result, dict) else 0.0,
                    created_at=datetime.utcnow()
                )
                session.add(analysis)

            # حفظ التغييرات
            session.commit()

            return jsonify({
                "status": "success",
                "message": "تم حفظ القضية بنجاح",
                "case_id": case.id
            })

        except Exception as e:
            session.rollback()
            raise e

        finally:
            session.close()

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"حدث خطأ أثناء حفظ القضية: {str(e)}"
        }), 500 