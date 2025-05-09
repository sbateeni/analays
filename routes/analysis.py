from flask import Blueprint, render_template, request, jsonify
import google.generativeai as genai
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
if not gemini_api_key:
    print("Warning: GOOGLE_API_KEY not found in environment variables")
else:
    try:
        # تكوين Gemini
        genai.configure(api_key=gemini_api_key)
        
        # البحث عن نموذج Gemini 2.0 Flash
        model_name = 'models/gemini-2.0-flash-001'
        available_models = list(genai.list_models())
        print("Available models:", [model.name for model in available_models])
        
        model_found = any(model.name == model_name for model in available_models)
        
        if not model_found:
            print(f"Model {model_name} not found in available models")
            # محاولة استخدام نموذج بديل
            model_name = 'gemini-pro'
            model_found = any(model.name == model_name for model in available_models)
            if not model_found:
                raise Exception(f"النموذج {model_name} غير متوفر")
            
        print(f"Model {model_name} found, initializing...")
        model = genai.GenerativeModel(model_name)
        
        # اختبار النموذج
        response = model.generate_content("Test connection")
        if response and response.text:
            models['gemini'] = model
            print(f"Gemini model {model_name} initialized and tested successfully")
        else:
            raise Exception("Model response was empty")
            
    except Exception as e:
        error_msg = str(e).lower()
        print(f"Detailed error: {str(e)}")
        
        if "invalid api key" in error_msg:
            print("The provided Google API key appears to be invalid")
        elif "quota exceeded" in error_msg:
            print("API quota has been exceeded")
        elif "not found" in error_msg:
            print("Model not found. Please ensure you have:")
            print("1. A valid API key")
            print("2. Access to the Gemini API")
            print("3. The Gemini API enabled in your Google Cloud project")
        elif "permission denied" in error_msg:
            print("Permission denied. Please check your API key permissions")
        else:
            print("Unexpected error initializing Gemini model")

analysis_bp = Blueprint('analysis', __name__, url_prefix='/api')

# تحديد النموذج المناسب لكل مرحلة - الآن كلها تستخدم Gemini
STAGE_MODELS = {
    1: 'gemini',    # التحليل الأولي
    2: 'gemini',    # تحليل الوقائع والأحداث
    3: 'gemini',    # التحليل القانوني الأساسي
    4: 'gemini',    # تحليل الأدلة والمستندات
    5: 'gemini',    # تحليل السوابق القضائية
    6: 'gemini',    # تحليل الحجج القانونية
    7: 'gemini',    # تحليل الدفوع القانونية
    8: 'gemini',    # التحليل الإجرائي
    9: 'gemini',    # صياغة الاستراتيجية القانونية
    10: 'gemini',   # تحليل المخاطر والفرص
    11: 'gemini',   # اقتراح الحلول والبدائل
    12: 'gemini'    # الملخص النهائي
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
    
    if model_type == "gemini":
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
        # التأكد من توفر النموذج المطلوب
        if model_type not in models:
            raise Exception(f"النموذج {model_type} غير متوفر. يرجى التحقق من تكوين API")
            
        # تحليل أولي
        if model_type == 'gemini':
            try:
                response = models['gemini'].generate_content(prompt)
                result = response.text
            except Exception as e:
                error_msg = str(e)
                if "invalid api key" in error_msg.lower():
                    raise Exception("مفتاح API غير صالح. يرجى التحقق من تكوين GOOGLE_API_KEY")
                elif "quota exceeded" in error_msg.lower():
                    raise Exception("تم تجاوز حصة API. يرجى المحاولة لاحقاً")
                else:
                    raise Exception(f"خطأ في استخدام نموذج Gemini: {error_msg}")
        else:  # gemini
            completion = models['gemini'].chat.completions.create(
                messages=[{
                    "role": "user",
                    "content": prompt
                }],
                model="deepseek-r1-distill-gemini-70b",
                temperature=0.6,
                max_tokens=4096,
                top_p=0.95,
                stream=False
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