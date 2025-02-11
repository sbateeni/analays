// تفعيل التحقق من صحة النماذج
(function () {
    'use strict'

    // جلب جميع النماذج التي تحتوي على الفئة needs-validation
    const forms = document.querySelectorAll('.needs-validation')

    // التحقق من صحة كل نموذج عند الإرسال
    Array.from(forms).forEach(form => {
        form.addEventListener('submit', event => {
            if (!form.checkValidity()) {
                event.preventDefault()
                event.stopPropagation()
            }

            form.classList.add('was-validated')
        }, false)
    })
})()

// تنسيق النص في نتيجة التحليل
function formatAnalysisResult(text) {
    return text
        .replace(/\n/g, '<br>')
        .replace(/•/g, '&#8226;')
        .replace(/- /g, '&#8226; ')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/\*(.*?)\*/g, '<em>$1</em>');
}

// إضافة مستمع لأحداث النقر على الروابط في شريط التنقل
document.addEventListener('DOMContentLoaded', function() {
    const navLinks = document.querySelectorAll('.nav-link');
    const currentPath = window.location.pathname;

    navLinks.forEach(link => {
        if (link.getAttribute('href') === currentPath) {
            link.classList.add('active');
        }
    });
}); 