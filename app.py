from flask import Flask, render_template, Blueprint, jsonify, request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Case, Analysis
from utils.export import AnalysisExporter
from utils.cache import AnalysisCache
from utils.documentation import DocumentationManager
from utils.metrics import PerformanceTracker
from utils.translation import LegalTranslator
import google.generativeai as genai
import os
from dotenv import load_dotenv

# تحميل متغيرات البيئة
load_dotenv()

# Create main blueprint
main_bp = Blueprint('main', __name__)

# تهيئة قاعدة البيانات
engine = create_engine('sqlite:///legal_analysis.db')
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

# تهيئة الأدوات المساعدة
cache = AnalysisCache()
doc_manager = DocumentationManager()
performance_tracker = PerformanceTracker(Session())
translator = LegalTranslator()

# تهيئة نموذج Gemini
genai.configure(api_key=os.getenv('GOOGLE_API_KEY'))

# تعريف المراحل
STAGES = {
    1: "التحليل الأولي",
    2: "تحليل الوقائع والأحداث",
    3: "التحليل القانوني الأساسي",
    4: "تحليل الأدلة والمستندات",
    5: "تحليل السوابق القضائية",
    6: "تحليل الحجج القانونية",
    7: "تحليل الدفوع القانونية",
    8: "التحليل الإجرائي",
    9: "صياغة الاستراتيجية القانونية",
    10: "تحليل المخاطر والفرص",
    11: "اقتراح الحلول والبدائل",
    12: "الملخص النهائي"
}

MODEL_NAMES = {
    'gemini': 'Google Gemini'
}

@main_bp.route('/')
def index():
    return render_template('index.html')

@main_bp.route('/about')
def about():
    return render_template('about.html')

@main_bp.route('/cases')
def cases():
    """عرض قائمة التحليلات السابقة"""
    session = Session()
    cases = session.query(Case).order_by(Case.created_at.desc()).all()
    return render_template('cases.html', cases=cases)

@main_bp.route('/cases/<int:case_id>')
def view_case(case_id):
    """عرض تفاصيل قضية معينة"""
    session = Session()
    case = session.query(Case).get_or_404(case_id)
    
    # حساب الإحصائيات
    analyses = case.analyses
    confidence_scores = [a.confidence_score for a in analyses if a.confidence_score]
    execution_times = [a.execution_time for a in analyses if a.execution_time]
    verified_stages = len([a for a in analyses if a.verification_status == 'verified'])
    
    stats = {
        'confidence_avg': sum(confidence_scores) / len(confidence_scores) if confidence_scores else 0,
        'total_time': sum(execution_times) if execution_times else 0,
        'verified_stages': verified_stages
    }
    
    return render_template('case_details.html',
                         case=case,
                         stage_names=STAGES,
                         model_names=MODEL_NAMES,
                         **stats)

@main_bp.route('/help')
def help():
    """عرض صفحة المساعدة"""
    categories = doc_manager.get_help_categories()
    articles = {}
    for category in categories:
        articles[category] = doc_manager._get_articles_by_category(category)
    return render_template('help.html', categories=categories, articles=articles)

@main_bp.route('/help/search')
def search_help():
    """البحث في التوثيق"""
    query = request.args.get('q', '')
    results = doc_manager.search_documentation(query)
    return jsonify(results)

@main_bp.route('/metrics')
def metrics():
    """عرض إحصائيات الأداء"""
    summary = performance_tracker.get_performance_summary() or {}
    stages = []
    stage_names = []
    confidence_data = []
    time_data = []
    
    for stage_num, stage_name in STAGES.items():
        metrics = performance_tracker.get_metrics(metric_name='confidence_score', stage=stage_num)
        avg_confidence = sum(m.metric_value for m in metrics) / len(metrics) if metrics else 0.0
        
        time_metrics = performance_tracker.get_metrics(metric_name='execution_time', stage=stage_num)
        avg_time = sum(m.metric_value for m in time_metrics) / len(time_metrics) if time_metrics else 0.0
        
        stages.append({
            'name': stage_name,
            'avg_confidence': float(avg_confidence),
            'avg_time': float(avg_time),
            'executions': len(metrics),
            'success_rate': float((len([m for m in metrics if m.metric_value >= 70]) / len(metrics) * 100) if metrics else 0),
            'status': 'good' if avg_confidence >= 80 else 'warning' if avg_confidence >= 60 else 'danger'
        })
        stage_names.append(stage_name)
        confidence_data.append(float(avg_confidence))
        time_data.append(float(avg_time))
    
    # Ensure all numeric values have proper defaults and are converted to float
    return render_template('metrics.html',
                         total_analyses=int(summary.get('total_analyses', 0)),
                         avg_confidence=float(summary.get('average_confidence', 0) or 0),
                         avg_execution_time=float(summary.get('average_execution_time', 0) or 0),
                         success_rate=float(summary.get('verification_success_rate', 0) or 0) * 100,
                         stages=stages,
                         stage_names=stage_names,
                         confidence_data=confidence_data,
                         time_data=time_data)

@main_bp.route('/translation')
def translation():
    """عرض صفحة الترجمة"""
    languages = [
        {'code': 'ar', 'name': 'العربية'},
        {'code': 'en', 'name': 'English'},
        {'code': 'fr', 'name': 'Français'},
    ]
    settings = {
        'source_language': 'ar',
        'target_language': 'en',
        'preserve_terms': True,
        'validate_translation': True
    }
    legal_terms = [
        {'id': 1, 'source': term, 'target': translation}
        for term, translation in translator.legal_terms.items()
    ]
    translation_history = []  # يمكن إضافة التاريخ الفعلي من قاعدة البيانات
    
    return render_template('translation.html',
                         languages=languages,
                         settings=settings,
                         legal_terms=legal_terms,
                         translation_history=translation_history)

@main_bp.route('/settings')
def settings():
    """عرض صفحة الإعدادات"""
    settings = {
        'system_name': 'نظام التحليل القانوني',
        'system_description': 'نظام متقدم للتحليل القانوني باستخدام الذكاء الاصطناعي',
        'interface_language': 'ar',
        'timezone': 'Asia/Riyadh',
        'default_model': 'gemini',
        'parallel_stages': 4,
        'max_text_size': 10000,
        'enable_verification': True,
        'enable_cache': True,
        'cache_ttl': 60,
        'max_cache_size': 1000,
        'enable_encryption': True,
        'session_timeout': 30,
        'enable_audit_log': True
    }
    
    interface_languages = [
        {'code': 'ar', 'name': 'العربية'},
        {'code': 'en', 'name': 'English'}
    ]
    
    timezones = [
        {'code': 'Asia/Riyadh', 'name': 'توقيت الرياض'},
        {'code': 'Asia/Dubai', 'name': 'توقيت دبي'},
        {'code': 'Africa/Cairo', 'name': 'توقيت القاهرة'}
    ]
    
    analysis_models = [
        {'code': 'gemini', 'name': 'Google Gemini'}
    ]
    
    return render_template('settings.html',
                         settings=settings,
                         interface_languages=interface_languages,
                         timezones=timezones,
                         analysis_models=analysis_models)

@main_bp.route('/privacy')
def privacy():
    """عرض سياسة الخصوصية"""
    return render_template('legal.html',
                         page_type='privacy',
                         page_title='سياسة الخصوصية')

@main_bp.route('/terms')
def terms():
    """عرض شروط الاستخدام"""
    return render_template('legal.html',
                         page_type='terms',
                         page_title='شروط الاستخدام')

@main_bp.route('/settings/<string:type>', methods=['POST'])
def update_settings(type):
    """تحديث الإعدادات"""
    data = request.get_json()
    
    if type == 'cache':
        # تحديث إعدادات التخزين المؤقت
        cache.set_expiry(data.get('cache_ttl', 60))
        if data.get('enable_cache'):
            cache.enable()
        else:
            cache.disable()
        return jsonify({'success': True})
    
    # ... handle other settings types ...
    return jsonify({'success': False, 'message': 'نوع إعدادات غير معروف'})

@main_bp.route('/settings/cache/clear', methods=['POST'])
def clear_cache():
    """مسح التخزين المؤقت"""
    cache.clear_all_cache()
    return jsonify({'success': True})

@main_bp.route('/analyze', methods=['POST'])
def analyze():
    try:
        text = request.json.get('text')
        if not text:
            return jsonify({'error': 'النص مطلوب'}), 400

        results = []
        model = genai.GenerativeModel('gemini-pro')

        for stage_num, stage_name in STAGES.items():
            try:
                prompt = f"""
                قم بتحليل النص التالي في المرحلة {stage_num} ({stage_name}):

                {text}

                ركز فقط على هذه المرحلة وقدم تحليلاً مفصلاً.
                """
                
                response = model.generate_content(prompt)
                
                results.append({
                    'stage': stage_num,
                    'stage_name': stage_name,
                    'analysis': response.text,
                    'confidence': 0.9
                })
                
            except Exception as e:
                results.append({
                    'stage': stage_num,
                    'stage_name': stage_name,
                    'error': f'خطأ في التحليل: {str(e)}'
                })

        return jsonify({'results': results})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main_bp.route('/api/collect-results', methods=['POST'])
def collect_results():
    try:
        data = request.get_json()
        text = data.get('text')
        
        if not text:
            return jsonify({'error': 'النص مطلوب'}), 400
        
        all_results = []
        
        # جمع نتائج جميع المراحل
        for stage in range(1, len(STAGES) + 1):
            # التحقق من وجود نتيجة مخزنة مؤقتاً
            cached_result = cache.get_cached_result(text, stage)
            if cached_result:
                all_results.append(cached_result)
            else:
                # إذا لم تكن النتيجة مخزنة، قم بتحليل المرحلة
                result = {
                    'stage': stage,
                    'stage_name': STAGES[stage],
                    'analysis': None,
                    'sources': [],
                    'confidence': 0.0
                }
                
                try:
                    model = genai.GenerativeModel('gemini-pro')
                    prompt = f"""
                    قم بتحليل النص التالي في المرحلة {stage} ({STAGES[stage]}):

                    {text}

                    ركز فقط على هذه المرحلة وقدم تحليلاً مفصلاً.
                    """
                    
                    response = model.generate_content(prompt)
                    result['analysis'] = response.text
                    result['confidence'] = 0.9
                    
                    # تخزين النتيجة في الذاكرة المؤقتة
                    cache.cache_result(text, stage, result)
                    all_results.append(result)
                    
                except Exception as e:
                    error_msg = f"خطأ في استخدام نموذج Gemini: {str(e)}"
                    print(f"Error in stage {stage}: {error_msg}")
                    result['error'] = error_msg
                    all_results.append(result)
        
        return jsonify({
            'success': True,
            'results': all_results
        })
        
    except Exception as e:
        print(f"Error in collect-results endpoint: {str(e)}")
        return jsonify({'error': str(e)}), 500

def create_app():
    app = Flask(__name__)
    
    # إضافة فلتر datetime
    @app.template_filter('datetime')
    def format_datetime(value):
        if value is None:
            return ""
        return value.strftime('%Y-%m-%d %H:%M')
    
    # Register blueprints
    from routes.analysis import analysis_bp
    from routes.case_management import case_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(analysis_bp)
    app.register_blueprint(case_bp)
    
    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True) 