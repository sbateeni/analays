from flask import Flask, render_template, Blueprint, jsonify, request
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Case, Analysis
from utils.export import AnalysisExporter
from utils.cache import AnalysisCache
from utils.documentation import DocumentationManager
from utils.metrics import PerformanceTracker
from utils.translation import LegalTranslator

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

# المتغيرات العامة
STAGE_NAMES = {
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
    'gemini': 'Google Gemini',
    'llama': 'Groq Llama'
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
                         stage_names=STAGE_NAMES,
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
    
    for stage_num, stage_name in STAGE_NAMES.items():
        metrics = performance_tracker.get_metrics(metric_name='confidence_score', stage=stage_num)
        avg_confidence = sum(m.metric_value for m in metrics) / len(metrics) if metrics else 0
        
        time_metrics = performance_tracker.get_metrics(metric_name='execution_time', stage=stage_num)
        avg_time = sum(m.metric_value for m in time_metrics) / len(time_metrics) if time_metrics else 0
        
        stages.append({
            'name': stage_name,
            'avg_confidence': avg_confidence,
            'avg_time': avg_time,
            'executions': len(metrics),
            'success_rate': (len([m for m in metrics if m.metric_value >= 70]) / len(metrics) * 100) if metrics else 0,
            'status': 'good' if avg_confidence >= 80 else 'warning' if avg_confidence >= 60 else 'danger'
        })
        stage_names.append(stage_name)
        confidence_data.append(avg_confidence)
        time_data.append(avg_time)
    
    return render_template('metrics.html',
                         total_analyses=summary.get('total_analyses', 0),
                         avg_confidence=summary.get('average_confidence', 0),
                         avg_execution_time=summary.get('average_execution_time', 0),
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
        {'code': 'gemini', 'name': 'Google Gemini'},
        {'code': 'llama', 'name': 'Groq Llama'}
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
    
    app.register_blueprint(main_bp)
    app.register_blueprint(analysis_bp)
    
    return app

app = create_app()

if __name__ == '__main__':
    app.run(debug=True) 