import multiprocessing

# تكوين Gunicorn
bind = "0.0.0.0:10000"  # عنوان IP والمنفذ
workers = multiprocessing.cpu_count() * 2 + 1  # عدد العمليات
worker_class = "sync"  # نوع العامل
threads = 2  # عدد الخيوط لكل عامل
timeout = 120  # مهلة الانتظار بالثواني
keepalive = 5  # وقت الاحتفاظ بالاتصال

# إعدادات التسجيل
accesslog = "-"  # تسجيل الوصول إلى stdout
errorlog = "-"   # تسجيل الأخطاء إلى stderr
loglevel = "info"

# إعدادات الأمان
limit_request_line = 4096
limit_request_fields = 100
limit_request_field_size = 8190 