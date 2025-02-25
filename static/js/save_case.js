// دالة حفظ القضية
async function saveCase() {
    const text = document.getElementById('case-text').value;
    const results = window.analysisResults; // النتائج المخزنة من التحليل

    if (!text || !results) {
        alert('لا توجد نتائج تحليل للحفظ');
        return;
    }

    // فتح نافذة إدخال عنوان القضية
    const title = prompt('أدخل عنوان القضية:', 'قضية جديدة');
    if (!title) return; // إلغاء إذا لم يتم إدخال عنوان

    try {
        const response = await fetch('/api/cases/save', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                title: title,
                text: text,
                results: results,
                model_used: 'gemini',
                case_type: 'عام'
            })
        });

        const data = await response.json();
        
        if (data.status === 'success') {
            alert('تم حفظ القضية بنجاح');
            // الانتقال إلى صفحة القضايا
            window.location.href = '/cases';
        } else {
            throw new Error(data.message);
        }
    } catch (error) {
        alert('حدث خطأ أثناء حفظ القضية: ' + error.message);
    }
} 