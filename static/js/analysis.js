// دالة التحليل الرئيسية
async function analyzeText() {
    const text = document.getElementById('case-text').value;
    const resultDiv = document.getElementById('analysis-result');
    const analysisButton = document.getElementById('analyze-button');
    
    if (!text) {
        alert('الرجاء إدخال نص القضية');
        return;
    }

    try {
        // تعطيل زر التحليل وإظهار مؤشر التحميل
        analysisButton.disabled = true;
        resultDiv.innerHTML = '<div class="spinner-border text-primary" role="status"><span class="visually-hidden">جاري التحليل...</span></div>';

        // إرسال طلب التحليل
        const response = await axios.post('/api/analyze', {
            text: text
        });

        // معالجة النتيجة
        if (response.data.success) {
            let results = response.data.results;
            let htmlContent = '<div class="analysis-results">';
            
            // عرض نتائج كل مرحلة
            for (let stage in results) {
                let result = results[stage];
                htmlContent += `
                    <div class="analysis-stage mb-4">
                        <h3 class="stage-title">المرحلة ${stage}</h3>
                        <div class="stage-content">
                            ${formatAnalysisResult(result)}
                        </div>
                    </div>
                `;
            }
            
            htmlContent += '</div>';
            resultDiv.innerHTML = htmlContent;
        } else {
            throw new Error(response.data.error || 'حدث خطأ أثناء التحليل');
        }
    } catch (error) {
        resultDiv.innerHTML = `
            <div class="alert alert-danger" role="alert">
                خطأ: ${error.message}
            </div>
        `;
    } finally {
        // إعادة تفعيل زر التحليل
        analysisButton.disabled = false;
    }
}

// دالة تنسيق نتيجة التحليل
function formatAnalysisResult(result) {
    if (typeof result === 'string') {
        return `<p>${result}</p>`;
    }
    
    let html = '';
    
    if (result.analysis) {
        html += `<div class="analysis-content">${result.analysis}</div>`;
    }
    
    if (result.verification) {
        html += `
            <div class="verification-section mt-3">
                <h4>التحقق من المعلومات</h4>
                <div class="verification-content">${result.verification}</div>
            </div>
        `;
    }
    
    if (result.sources) {
        html += `
            <div class="sources-section mt-3">
                <h4>المصادر</h4>
                <div class="sources-content">${result.sources}</div>
            </div>
        `;
    }
    
    return html || `<p>${JSON.stringify(result)}</p>`;
}

// إضافة مستمع الحدث لزر التحليل
document.addEventListener('DOMContentLoaded', function() {
    const analyzeButton = document.getElementById('analyze-button');
    if (analyzeButton) {
        analyzeButton.addEventListener('click', analyzeText);
    }
}); 