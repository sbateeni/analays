from flask import Blueprint, render_template, request, jsonify
import google.generativeai as genai
from groq import Groq
import os
from dotenv import load_dotenv
import asyncio
import json
from datetime import datetime

# تحميل المتغيرات البيئية
load_dotenv()

# تهيئة النماذج
models = {}

# تهيئة نموذج Google Gemini إذا كان المفتاح متوفراً
gemini_api_key = os.getenv('GOOGLE_API_KEY')
if gemini_api_key:
    try:
        genai.configure(api_key=gemini_api_key)
        models['gemini'] = genai.GenerativeModel('gemini-pro')
        print("Gemini model initialized successfully")
    except Exception as e:
        print(f"Error initializing Gemini model: {e}")

# تهيئة نموذج Groq Llama إذا كان المفتاح متوفراً
groq_api_key = os.getenv('GROQ_API_KEY')
if groq_api_key:
    try:
        models['llama'] = Groq(api_key=groq_api_key)
        print("Llama model initialized successfully")
    except Exception as e:
        print(f"Error initializing Llama model: {e}")

analysis_bp = Blueprint('analysis', __name__, url_prefix='/api')

# تحديد النموذج المناسب لكل مرحلة
STAGE_MODELS = {
    1: 'gemini',    # التحليل الأولي - يحتاج إلى بحث في الإنترنت
    2: 'gemini',    # تحليل الوقائع والأحداث - يحتاج إلى فهم عام
    3: 'llama',     # التحليل القانوني الأساسي - يحتاج إلى معرفة قانونية عميقة
    4: 'llama',     # تحليل الأدلة والمستندات - يحتاج إلى تحليل متخصص
    5: 'gemini',    # تحليل السوابق القضائية - يحتاج إلى بحث في الإنترنت
    6: 'llama',     # تحليل الحجج القانونية - يحتاج إلى تحليل متعمق
    7: 'llama',     # تحليل الدفوع القانونية - يحتاج إلى معرفة قانونية متخصصة
    8: 'llama',     # التحليل الإجرائي - يحتاج إلى معرفة بالإجراءات القانونية
    9: 'llama',     # صياغة الاستراتيجية القانونية - يحتاج إلى تفكير استراتيجي
    10: 'gemini',   # تحليل المخاطر والفرص - يحتاج إلى معلومات حديثة
    11: 'llama',    # اقتراح الحلول والبدائل - يحتاج إلى تحليل شامل
    12: 'gemini'    # الملخص النهائي - يحتاج إلى دمج كل المعلومات
}

def get_analysis_prompt(stage, text, previous_results=None):
    """إنشاء النص التوجيهي المناسب للمرحلة"""
    base_prompts = {
        1: f"""قم بالتحليل الأولي للنص التالي مع البحث عن معلومات ذات صلة:
{text}

يجب أن يتضمن التحليل:
- تحديد نوع القضية
- فهم الأطراف المعنية
- استخراج التواريخ والمعلومات الأساسية
- البحث عن قوانين وتشريعات ذات صلة""",
        
        2: f"""قم بتحليل الوقائع والأحداث في القضية التالية مع الاستناد إلى التحليل الأولي:
{text}

التحليل الأولي:
{previous_results.get(1, '')}

يجب أن يتضمن التحليل:
- ترتيب الأحداث زمنياً
- تحديد النقاط الرئيسية في القضية
- ربط الأحداث بالقوانين ذات الصلة""",
        
        3: f"""قم بالتحليل القانوني الأساسي للقضية التالية مع الاستناد إلى التحليلات السابقة:
{text}

التحليلات السابقة:
{json.dumps(previous_results, ensure_ascii=False, indent=2)}

يجب أن يتضمن التحليل:
- تحديد المواد القانونية ذات الصلة
- تصنيف القضية قانونياً
- تحليل الأساس القانوني للقضية""",
        
        4: f"""قم بتحليل الأدلة والمستندات في القضية التالية:\n{text}\n\nيجب أن يتضمن التحليل:\n- تقييم قوة الأدلة المقدمة\n- تحديد الثغرات في الأدلة""",
        
        5: f"""قم بتحليل السوابق القضائية المتعلقة بالقضية التالية:\n{text}\n\nيجب أن يتضمن التحليل:\n- البحث عن قضايا مشابهة\n- تحليل الأحكام السابقة ذات الصلة""",
        
        6: f"""قم بتحليل الحجج القانونية في القضية التالية:\n{text}\n\nيجب أن يتضمن التحليل:\n- تحديد نقاط القوة في القضية\n- تحديد نقاط الضعف المحتملة""",
        
        7: f"""قم بتحليل الدفوع القانونية الممكنة في القضية التالية:\n{text}\n\nيجب أن يتضمن التحليل:\n- اقتراح الدفوع الممكنة\n- تقييم فعالية كل دفع""",
        
        8: f"""قم بالتحليل الإجرائي للقضية التالية:\n{text}\n\nيجب أن يتضمن التحليل:\n- تحديد الإجراءات القانونية المطلوبة\n- تحديد المواعيد والمهل القانونية""",
        
        9: f"""قم بصياغة الاستراتيجية القانونية للقضية التالية:\n{text}\n\nيجب أن يتضمن التحليل:\n- وضع خطة التعامل مع القضية\n- تحديد أولويات العمل""",
        
        10: f"""قم بتحليل المخاطر والفرص في القضية التالية:\n{text}\n\nيجب أن يتضمن التحليل:\n- تقييم احتمالات النجاح\n- تحديد المخاطر المحتملة""",
        
        11: f"""قم باقتراح الحلول والبدائل للقضية التالية:\n{text}\n\nيجب أن يتضمن التحليل:\n- تقديم خيارات التسوية الممكنة\n- اقتراح حلول بديلة""",
        
        12: f"""قم بإعداد الملخص النهائي للقضية بناءً على جميع التحليلات السابقة:
{text}

التحليلات السابقة:
{json.dumps(previous_results, ensure_ascii=False, indent=2)}

يجب أن يتضمن التحليل:
- تلخيص جميع النتائج
- تقديم التوصيات النهائية
- تحديد الخطوات التالية"""
    }
    
    prompt = base_prompts.get(stage, "قم بتحليل القضية التالية")
    model_type = STAGE_MODELS[stage]
    
    if model_type == "llama":
        prompt = f"""أنت محامٍ خبير في القانون الفلسطيني ومتخصص في التحليل القانوني باللغة العربية.

تعليمات هامة:
1. يجب أن تكون إجابتك باللغة العربية الفصحى
2. استخدم المصطلحات القانونية العربية الصحيحة
3. قم بتنظيم إجابتك في نقاط وفقرات واضحة
4. اذكر المواد القانونية والتشريعات بدقة
5. اكتب الأرقام والتواريخ بالأرقام العربية (١، ٢، ٣)

القضية المطروحة:
{text}

المطلوب تحليله:
{prompt}

قم بتقديم تحليل قانوني شامل ومفصل باللغة العربية، مع التركيز على الجوانب القانونية المهمة والاستناد إلى القوانين والتشريعات الفلسطينية."""

    return prompt, model_type

async def verify_legal_information(text, analysis_result):
    """التحقق من صحة المعلومات القانونية باستخدام Gemini"""
    try:
        verification_prompt = f"""
قم بالتحقق من صحة المعلومات القانونية التالية وتأكيد دقتها:

النص الأصلي:
{text}

التحليل المقترح:
{analysis_result}

المطلوب:
1. تحقق من صحة المواد القانونية المذكورة
2. تأكد من دقة الإشارات للقوانين والتشريعات
3. تحقق من صحة الأحكام القضائية المذكورة
4. ابحث عن أي تعديلات حديثة على القوانين المذكورة
5. قم بتصحيح أي معلومات غير دقيقة

يجب تقديم:
1. تأكيد صحة المعلومات الدقيقة
2. تصحيح أي معلومات غير دقيقة
3. إضافة المصادر الموثوقة لكل معلومة:
   - روابط للقوانين والتشريعات
   - روابط للأحكام القضائية
   - تاريخ آخر تحديث للقوانين
4. إضافة أي معلومات مهمة ناقصة
5. تحديد درجة الموثوقية (عالية، متوسطة، منخفضة) لكل جزء من التحليل"""

        response = models['gemini'].generate_content(verification_prompt)
        verification_result = response.text

        # تحليل النتيجة وإضافة معلومات إضافية
        try:
            # محاولة استخراج المصادر والروابط
            sources_prompt = f"""
استخرج المصادر والروابط من النتيجة التالية:
{verification_result}

قم بتنظيمها في الشكل التالي:
1. القوانين والتشريعات
2. الأحكام القضائية
3. المراجع الإضافية"""

            sources_response = models['gemini'].generate_content(sources_prompt)
            sources = sources_response.text

            # تنسيق النتيجة النهائية
            final_result = {
                "verified_result": verification_result,
                "sources": sources,
                "verification_date": datetime.now().isoformat(),
                "is_verified": True
            }

            return final_result

        except Exception as e:
            print(f"Error processing sources: {e}")
            return {
                "verified_result": verification_result,
                "verification_date": datetime.now().isoformat(),
                "is_verified": True
            }

    except Exception as e:
        print(f"Error in verification: {e}")
        return {
            "error": str(e),
            "is_verified": False
        }

async def analyze_stage(stage, text, previous_results):
    """تحليل مرحلة واحدة"""
    prompt, model_type = get_analysis_prompt(stage, text, previous_results)
    
    try:
        # تحليل أولي
        if model_type == 'gemini':
            response = models['gemini'].generate_content(prompt)
            result = response.text
        else:  # llama
            completion = models['llama'].chat.completions.create(
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                model="llama-3.3-70b-versatile",
                temperature=1,
                max_tokens=1024,
                top_p=1,
                stream=False,
                stop=None
            )
            result = completion.choices[0].message.content

        # التحقق من المعلومات القانونية إذا كانت المرحلة تتطلب ذلك
        needs_verification = stage in [1, 3, 5, 8]  # المراحل التي تحتاج إلى تحقق
        if needs_verification:
            verification = await verify_legal_information(text, result)
            if verification.get("is_verified"):
                result = {
                    "analysis": result,
                    "verification": verification.get("verified_result"),
                    "sources": verification.get("sources", ""),
                    "verification_date": verification.get("verification_date")
                }
            else:
                print(f"Warning: Verification failed for stage {stage}")
                result = {
                    "analysis": result,
                    "verification_error": verification.get("error", "فشل التحقق من المعلومات")
                }
        
        return {
            "stage": stage,
            "result": result,
            "model_used": model_type,
            "verified": needs_verification
        }
    except Exception as e:
        print(f"Error in stage {stage}: {e}")
        return {
            "stage": stage,
            "error": str(e),
            "model_used": model_type
        }

@analysis_bp.route('/analyze', methods=['POST'])
def analyze():
    """تحليل النص المدخل"""
    try:
        data = request.json
        if not data:
            print("No JSON data received")
            return jsonify({
                "status": "error",
                "message": "لم يتم استلام بيانات"
            }), 400

        text = data.get('text')
        if not text:
            print("No text provided")
            return jsonify({
                "status": "error",
                "message": "يرجى إدخال النص المراد تحليله"
            }), 400

        start_stage = int(data.get('stage', 1))
        end_stage = int(data.get('end_stage', start_stage))
        
        print(f"Analyzing text from stage {start_stage} to {end_stage}")
        
        # التأكد من وجود النماذج المطلوبة
        required_models = set(STAGE_MODELS[stage] for stage in range(start_stage, end_stage + 1))
        missing_models = required_models - set(models.keys())
        
        if missing_models:
            print(f"Missing models: {missing_models}")
            return jsonify({
                "status": "error",
                "message": f"النماذج التالية غير متوفرة: {', '.join(missing_models)}"
            }), 400
        
        # تحليل المراحل
        results = {}
        for stage in range(start_stage, end_stage + 1):
            print(f"Processing stage {stage}")
            result = asyncio.run(analyze_stage(stage, text, results))
            if "error" in result:
                print(f"Error in stage {stage}: {result['error']}")
                return jsonify({
                    "status": "error",
                    "message": f"خطأ في المرحلة {stage}: {result['error']}"
                }), 500
            
            # إضافة النتيجة
            results[stage] = result["result"]
            print(f"Stage {stage} completed successfully")
        
        return jsonify({
            "status": "success",
            "results": results,
            "current_stage": end_stage
        })
    except Exception as e:
        print(f"Unexpected error in analysis: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "message": f"خطأ غير متوقع: {str(e)}"
        }), 500 