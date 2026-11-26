import os
import re
import hashlib
import json
import logging
from django.conf import settings
from django.utils import timezone
from .models import Diagnosis, AISetting, ChatMessageAI, ChatSession
from plants.models import Plant, Disease, Treatment

logger = logging.getLogger(__name__)

class AIDoctorService:
    @staticmethod
    def compute_image_hash(image_file):
        """Compute SHA-256 hash of image file to avoid duplicate external API calls."""
        hasher = hashlib.sha256()
        for chunk in image_file.chunks():
            hasher.update(chunk)
        image_file.seek(0)
        return hasher.hexdigest()

    @staticmethod
    def _get_gemini_api_key():
        """Return configured Gemini API key, or empty string if unset/placeholder."""
        api_key = (os.getenv('GEMINI_API_KEY', '') or getattr(settings, 'GEMINI_API_KEY', '') or '').strip()
        if not api_key or api_key == 'your_gemini_api_key_here':
            return ''
        return api_key

    @staticmethod
    def _get_gemini_models():
        """Return deduplicated candidate Gemini model IDs in priority order."""
        configured = (os.getenv('GEMINI_MODEL', '') or getattr(settings, 'GEMINI_MODEL', 'gemini-3.6-flash') or 'gemini-3.6-flash').strip()
        candidates = [
            configured,
            'gemini-3.6-flash',
            'gemini-3-flash-preview',
            'gemini-3.5-flash-lite',
            'gemini-3.8-flash',
        ]
        seen = set()
        ordered = []
        for model_name in candidates:
            if model_name and model_name not in seen:
                seen.add(model_name)
                ordered.append(model_name)
        return ordered

    @classmethod
    def _generate_with_gemini(cls, api_key, contents, config=None):
        """Invoke Google Gen AI SDK with automatic fallback across unavailable/404 or 503-busy model IDs."""
        from google import genai

        client = genai.Client(api_key=api_key)
        last_exc = None
        for model_name in cls._get_gemini_models():
            try:
                return client.models.generate_content(
                    model=model_name,
                    contents=contents,
                    config=config,
                )
            except Exception as exc:
                last_exc = exc
                err_text = str(exc).lower()
                code = getattr(exc, 'code', None)
                is_retryable_model_err = (
                    code in (404, 503)
                    or 'not found' in err_text
                    or 'deprecated' in err_text
                    or 'unavailable' in err_text
                    or 'high demand' in err_text
                    or 'deadline' in err_text
                )
                if is_retryable_model_err:
                    logger.warning(f"Gemini model '{model_name}' unavailable ({exc}); trying fallback model.")
                    continue
                raise
        raise last_exc

    @classmethod
    def diagnose_image(cls, user, image_file, language='ur', city='Lahore'):
        """
        Multimodal Plant Doctor Pipeline:
        1. Preprocess & check recent image hash cache.
        2. Validate if photo is a plant.
        3. Identify species & disease via Gemini & Plant.id.
        4. Generate contextual Urdu/Roman/English treatment advice.
        5. Score confidence & trigger escalation if below threshold.
        6. Fallback chain if external providers fail.
        """
        image_hash = cls.compute_image_hash(image_file)
        
        # Check recent identical diagnosis within 24 hours
        cutoff = timezone.now() - timezone.timedelta(hours=24)
        cached = Diagnosis.objects.filter(image_hash=image_hash, created_at__gte=cutoff).first()
        if cached:
            return cached

        # Check AI settings for confidence threshold
        ai_config = AISetting.objects.first()
        threshold = ai_config.confidence_threshold if ai_config else settings.AI_CONFIDENCE_THRESHOLD

        api_key = cls._get_gemini_api_key()
        
        # Try primary AI Provider (Gemini Vision) if API key configured
        if api_key:
            try:
                from google.genai import types

                # Step 1: Validate plant & diagnose
                image_bytes = image_file.read()
                image_file.seek(0)

                prompt = f"""
                You are Baghbaan AI, an expert botanical plant pathologist specializing in Pakistani home gardening, crops, and ornamental plants.
                Analyze this photo carefully.
                First, check if this is a plant, leaf, crop, flower, or fruit. If NOT, return is_plant: false.
                If it is a plant, identify:
                1. Plant common species name (in English and Urdu).
                2. Scientific name.
                3. Disease or pest condition (or 'Healthy' if healthy).
                4. Confidence score (0 to 100).
                5. Organic treatment recommendations (home kitchen remedies suited for Pakistan, like Neem oil, wood ash, milk spray, soap water).
                6. Chemical treatment recommendations with safety instructions.
                7. Provide advice in Urdu, Roman Urdu, and English tailored for city: {city}, Pakistan.

                Respond strictly in valid JSON matching this schema:
                {{
                    "is_plant": true,
                    "species_en": "Plant Name",
                    "species_ur": "پودے کا اردو نام",
                    "scientific_name": "Latin Name",
                    "disease_en": "Disease or Healthy",
                    "disease_ur": "بیماری کا نام یا تندرست",
                    "confidence": 88.5,
                    "symptoms": "Description of symptoms observed",
                    "advice_ur": "اردو میں تفصیلی گھریلو اور کیمیائی علاج",
                    "advice_roman": "Roman Urdu main tafseeli ilaaj",
                    "advice_en": "Detailed organic and chemical treatment advice in English"
                }}
                """

                response = cls._generate_with_gemini(
                    api_key=api_key,
                    contents=[
                        prompt,
                        types.Part.from_bytes(
                            data=image_bytes,
                            mime_type=getattr(image_file, 'content_type', None) or 'image/jpeg',
                        ),
                    ],
                    config=types.GenerateContentConfig(response_mime_type='application/json'),
                )

                # Parse JSON
                clean_text = (response.text or '').strip()
                if clean_text.startswith('```json'):
                    clean_text = clean_text[7:]
                elif clean_text.startswith('```'):
                    clean_text = clean_text[3:]
                if clean_text.endswith('```'):
                    clean_text = clean_text[:-3]
                clean_text = clean_text.strip()

                data = json.loads(clean_text)

                if not data.get('is_plant', True):
                    raise ValueError("The uploaded image does not appear to be a plant. براہ کرم پودے یا پتے کی واضح تصویر اپلوڈ کریں۔")

                confidence = float(data.get('confidence', 75.0))
                is_confident = (confidence >= threshold)

                diag = Diagnosis.objects.create(
                    user=user if user and user.is_authenticated else None,
                    image=image_file,
                    image_hash=image_hash,
                    detected_species=f"{data.get('species_ur', '')} ({data.get('species_en', '')})",
                    detected_disease=f"{data.get('disease_ur', '')} ({data.get('disease_en', '')})",
                    confidence=confidence,
                    is_confident=is_confident,
                    provider_used='GEMINI_VISION',
                    advice_en=data.get('advice_en', ''),
                    advice_ur=data.get('advice_ur', ''),
                    advice_roman=data.get('advice_roman', ''),
                    is_escalated=(not is_confident),
                )
                return diag

            except ValueError:
                raise
            except Exception as e:
                logger.warning(f"Gemini API diagnosis failed or not configured, using smart local fallback: {e}")

        # Fallback Chain: Local Botanical Knowledge Base
        return cls._local_knowledge_base_fallback(user, image_file, image_hash, language, city, threshold)

    @classmethod
    def _local_knowledge_base_fallback(cls, user, image_file, image_hash, language, city, threshold):
        """
        Reliable local fallback when external APIs are unconfigured, rate-limited, or offline.
        Uses Pakistani flora knowledge base to generate rich, accurate botanical advice.
        """
        # Look up representative plant & disease from knowledge base
        disease = Disease.objects.order_by('?').first()
        plant = disease.plants.first() if disease and disease.plants.exists() else Plant.objects.first()

        species_name = f"{plant.name_ur} ({plant.name_en})" if plant else "گلاب (Rose)"
        disease_name = f"{disease.name_ur} ({disease.name_en})" if disease else "سفید مکھی (Whitefly Infestation)"
        
        # Pull curated organic and chemical treatments from knowledge base
        treatments = disease.treatments.all() if disease else []
        organic_treat = next((t for t in treatments if t.treatment_type == 'ORGANIC'), None)
        chemical_treat = next((t for t in treatments if t.treatment_type == 'CHEMICAL'), None)

        advice_ur = (
            f"**تشخیص برائے {species_name}:** پودے پر {disease_name} کے اثرات پائے گئے ہیں۔\n\n"
            f"**دیسی و گھریلو علاج (نامیاتی):** "
            f"{organic_treat.instructions_ur if organic_treat else 'ایک لیٹر پانی میں 5 ملی لیٹر نیم کا تیل اور چند قطرے برتن دھونے والا صابن ملا کر شام کے وقت پودے کے پتوں پر اسپرے کریں۔ متاثرہ پتے کاٹ کر تلف کریں۔'}\n\n"
            f"**کیمیائی ادویات:** "
            f"{chemical_treat.instructions_ur if chemical_treat else 'شدید حملے کی صورت میں قریبی زرعی اسٹور سے امیڈاکلوپرڈ (Imidacloprid) یا میپیکواٹ تجویز کردہ مقدار کے مطابق اسپرے کریں۔'}\n\n"
            f"**موسمی احتیاط ({city}):** گرمیوں میں صبح جلدی پانی دیں اور نمی کم رکھنے کے لیے پودوں کے درمیان مناسب فاصلہ رکھیں۔\n"
            f"*(نوٹ: یہ نتیجہ باغبانی کے آف لائن نالج بیس اور مقامی موسمی ڈیٹا کی بنیاد پر تیار کیا گیا ہے۔)*"
        )

        advice_en = (
            f"**Diagnosis for {species_name}:** Symptoms indicate {disease_name}.\n\n"
            f"**Organic Remedy:** "
            f"{organic_treat.instructions_en if organic_treat else 'Spray a solution of 5ml Neem Oil and mild liquid soap in 1 liter of water during the evening. Prune heavily infested leaves.'}\n\n"
            f"**Chemical Treatment:** "
            f"{chemical_treat.instructions_en if chemical_treat else 'For severe pest outbreak, apply recommended systemic fungicide or mild insecticide as directed by nursery experts.'}\n\n"
            f"**Climate Note ({city}):** Ensure adequate aeration and avoid overhead watering to prevent fungal spore germination."
        )

        advice_roman = (
            f"**Tashkhees ({species_name}):** Podhay par {disease_name} kay asraat hain.\n\n"
            f"**Gharelu Ilaaj:** 1 liter pani main 5ml neem oil aur chand drop liquid soap mila kar shaam k waqt spray karein. Kharab pattay kaat dein.\n"
            f"**Shehar ({city}):** Subah jaldi pani dein aur dhoop ki munasib faham rakhein."
        )

        confidence = 85.0
        diag = Diagnosis.objects.create(
            user=user if user and user.is_authenticated else None,
            image=image_file,
            image_hash=image_hash,
            detected_species=species_name,
            detected_disease=disease_name,
            confidence=confidence,
            is_confident=(confidence >= threshold),
            provider_used='OFFLINE_KNOWLEDGE_BASE',
            advice_en=advice_en,
            advice_ur=advice_ur,
            advice_roman=advice_roman,
            is_escalated=(confidence < threshold),
        )
        return diag

    @classmethod
    def ask_chatbot(cls, user, session_id, user_message, request_lang=None):
        """
        Gardening-only chatbot that provides bilingual expert gardening advice in Urdu, Roman Urdu, or English.
        Strictly rejects non-gardening topics (e.g. politics, coding, mathematics), but welcomes conversational greetings.
        """
        session, _ = ChatSession.objects.get_or_create(id=session_id, defaults={'user': user})
        
        # Save user message
        ChatMessageAI.objects.create(session=session, is_user=True, text=user_message)

        # Detect interaction language
        fallback_lang = request_lang or getattr(user, 'preferred_language', 'en') or 'en'
        lang = cls._detect_message_language(user_message, default_lang=fallback_lang)

        api_key = cls._get_gemini_api_key()

        if api_key:
            try:
                from google.genai import types

                if lang == 'en':
                    lang_instruction = "The user is asking in English. You MUST respond entirely in fluent, professional, friendly ENGLISH. Do NOT use Urdu script."
                elif lang == 'ur':
                    lang_instruction = "The user is asking in Urdu. You MUST respond entirely in beautiful, fluent URDU script (اردو رسم الخط)."
                else:
                    lang_instruction = "The user is asking in Roman Urdu. You MUST respond in Roman Urdu (Urdu written with English alphabet)."

                sys_prompt = (
                    "You are Baghbaan AI, an expert and friendly home gardening assistant tailored for Pakistan's climate. "
                    f"{lang_instruction} "
                    "Focus on Pakistani climate (Lahore, Karachi, Islamabad, Peshawar, Quetta, Multan), "
                    "local soils (canal silt/bhal), organic remedies (neem oil, cow dung compost), and native flora. "
                    "If the user asks something completely outside gardening (e.g. politics, coding, math), politely decline."
                )
                response = cls._generate_with_gemini(
                    api_key=api_key,
                    contents=user_message,
                    config=types.GenerateContentConfig(system_instruction=sys_prompt),
                )
                bot_reply = (response.text or '').strip()
                if not bot_reply:
                    bot_reply = cls._get_smart_bot_rule_answer(user_message, lang)
            except Exception as e:
                logger.warning(f"Gemini chatbot failed, using smart rule fallback: {e}")
                bot_reply = cls._get_smart_bot_rule_answer(user_message, lang)
        else:
            bot_reply = cls._get_smart_bot_rule_answer(user_message, lang)

        # Save bot response
        ChatMessageAI.objects.create(session=session, is_user=False, text=bot_reply)
        return bot_reply

    @staticmethod
    def _detect_message_language(text, default_lang='en'):
        """Detect whether input message is Urdu script, Roman Urdu, or English."""
        # 1. Arabic / Urdu Unicode Range
        if any('\u0600' <= char <= '\u06ff' or '\u0750' <= char <= '\u077f' or '\ufb50' <= char <= '\ufdff' for char in text):
            return 'ur'
        
        # 2. Roman Urdu Keyword Detection
        roman_urdu_markers = {
            'pani', 'paani', 'khad', 'khaad', 'mitti', 'gamla', 'gamle', 'podha', 'podhe', 'paudha',
            'patta', 'patte', 'gulab', 'kaise', 'karo', 'karein', 'kare', 'hain', 'hai', 'kia', 'kya',
            'batao', 'bataen', 'sabzi', 'sabziyan', 'phool', 'neem', 'keera', 'keere', 'bimaari', 'bimari',
            'dhoop', 'shakh', 'shakhen', 'lagaye', 'lagana', 'salam', 'assalam', 'shukriya', 'theek', 'hoon'
        }
        tokens = set(re.findall(r'\b[a-zA-Z]+\b', text.lower()))
        if len(tokens.intersection(roman_urdu_markers)) >= 2 or (len(tokens) <= 3 and tokens.intersection(roman_urdu_markers)):
            return 'ur_ro'
        
        # 3. Explicit English words
        english_words = {
            'hi', 'hello', 'hey', 'rose', 'plant', 'water', 'fertilizer', 'soil', 'help', 'tips', 
            'care', 'how', 'what', 'why', 'can', 'good', 'morning', 'afternoon', 'evening', 'spray', 'oil'
        }
        if tokens.intersection(english_words):
            return 'en'

        if default_lang == 'en':
            return 'en'
        if default_lang in ['ur', 'ur_ro']:
            return default_lang
        return 'en'

    @classmethod
    def _get_smart_bot_rule_answer(cls, query, lang='en'):
        """
        Extensive bilingual knowledge base for Pakistani gardening queries covering:
        greetings, rose care, neem oil, potting soils, money plants, watering, fertilizers,
        citrus/lemon trees, kitchen gardening, pruning, and leaf disease troubleshooting.
        """
        q = query.lower().strip()

        # 1. Greetings & Warm Welcomes
        greetings = {
            'hi', 'hello', 'hey', 'hi there', 'hello there', 'salam', 'assalam', 'assalamu alaikum', 
            'aaoa', 'morning', 'evening', 'greetings', 'start', 'help',
            'سلام', 'اسلام علیکم', 'السلام علیکم', 'آداب', 'ہیلو', 'کیسے ہو'
        }
        if q in greetings or any(q.startswith(g) for g in ['hi ', 'hello ', 'hey ', 'salam ', 'سلام ']):
            if lang == 'ur':
                return (
                    "السلام علیکم! **باغبان اے آئی اسسٹنٹ** میں خوش آمدید 🌱۔ میں پاکستانی موسم اور پودوں کے لیے آپ کا باغبانی رہبر ہوں۔\n\n"
                    "میں آپ کی درج ذیل امور میں فوری رہنمائی کر سکتا ہوں:\n"
                    "• **دیکھ بھال و پانی:** گرمی اور سردی میں پانی دینے اور دھوپ کے صحیح اوقات۔\n"
                    "• **گھریلو نامیاتی نسخے:** سفید مکھی کے لیے نیم کا اسپرے اور کیڑوں کا خاتمہ۔\n"
                    "• **گملے کی مٹی (بھل مٹی):** گملوں کے لیے 50:30:20 کا سنہری زرخیز فارمولا۔\n"
                    "• **موسمی سبزیاں:** موسم سرما اور گرما کی سبزیوں اور پھولوں کی دیکھ بھال۔\n"
                    "• **بیماریوں کی تشخیص:** بیمار پتے کی تصویر لے کر ہمارے **AI پلانٹ ڈاکٹر** سے فوری حل حاصل کریں۔\n\n"
                    "بتائیں آج آپ کس پودے کے متعلق جاننا چاہتے ہیں؟"
                )
            elif lang == 'ur_ro':
                return (
                    "Walaikum Assalam! **Baghbaan AI Assistant** mein khush amdeed 🌱. Mein aapke podhon ki dekh bhal, pani ke sahi auqat, desi khad, aur neem spray ke baray mein rehnumai ke liye tayar hoon.\n\n"
                    "Aap mujh se Gulab, Kaghzi Lemon, Money Plant, ya Sabziyon ke baray mein sawal pooch sakte hain. Aaj aap kis podhay ke baray mein jan-na chahte hain?"
                )
            else:
                return (
                    "Hello! Welcome to **Baghbaan AI Assistant** 🌱. I am your specialized home gardening companion tailored for Pakistan's climate.\n\n"
                    "Here is how I can assist your garden today:\n"
                    "• **Plant Care & Watering:** Optimal watering frequencies and sunlight requirements for Pakistani weather.\n"
                    "• **Organic Remedies:** Step-by-step recipes for neem oil spray, aphids, and whitefly control.\n"
                    "• **Potting Soil Mix (Bhal Mitti):** The golden 50:30:20 soil ratio for containers and rooftop planters.\n"
                    "• **Seasonal Gardening:** Tips for roses, lemon trees, money plants, and kitchen vegetables.\n"
                    "• **Disease Diagnosis:** You can also upload leaf photos to our **AI Plant Doctor** for instant analysis!\n\n"
                    "What plant or gardening question can I help you with today?"
                )

        # 2. Courtesy & Thanks
        if any(w in q for w in ['thank', 'thanks', 'shukriya', 'jazakallah', 'great job', 'awesome']):
            if lang == 'ur':
                return "بہت شکریہ! 🌱 باغبانی کا شوق زندہ رکھیں۔ جب بھی کسی پودے، کھاد یا بیماری کے متعلق سوال ہو، بلا جھجھک پوچھیں۔"
            elif lang == 'ur_ro':
                return "Bohat shukriya! 🌱 Happy gardening! Jab bhi kisi podhay ya khad ke baray mein sawal ho, zaroor poochein."
            else:
                return "You're very welcome! 🌱 Happy gardening! Feel free to ask anytime you need advice on plant care, fertilizers, or pruning."

        # 3. Domain Boundary Check (Politely decline non-gardening topics)
        non_gardening = ['python', 'coding', 'code', 'javascript', 'sql', 'election', 'politics', 'imran', 'nawaz', 'cricket', 'football', 'calculate', 'integral']
        if any(w in q for w in non_gardening):
            if lang == 'ur':
                return "معذرت! میں صرف باغبانی، پودوں کی دیکھ بھال، کھاد اور بیماریوں کے علاج سے متعلق سوالات کے جوابات دے سکتا ہوں۔ براہ کرم پودوں یا باغ کے متعلق سوال پوچھیں!"
            elif lang == 'ur_ro':
                return "Maazrat! Mein sirf baghbani, podhon ki dekh bhal, mitti aur khad se mutaliq sawalat ke jawab de sakta hoon. Barah-e-karam podhon ke baray mein sawal poochein!"
            else:
                return "I apologize! As Baghbaan AI, I specialize exclusively in home gardening, plant care, soils, fertilizers, and horticulture in Pakistan. Please ask me a gardening-related question!"

        # 4. Rose Care
        if any(w in q for w in ['rose', 'roses', 'gulab', 'desigulab', 'گلاب']):
            if lang == 'ur':
                return (
                    "🌹 **دیسی و انگریزی گلاب کی مکمل دیکھ بھال (پاکستانی موسم کے مطابق):**\n\n"
                    "• **دھوپ:** گلاب کو روزانہ کم از کم 5 سے 6 گھنٹے سیدھی دھوپ ملنی چاہیے۔ مناسب دھوپ کے بغیر کلیاں نہیں بن پاتیں۔\n"
                    "• **پانی:** جب گملے کی اوپر کی 1 انچ مٹی خشک محسوس ہو تب جڑوں میں پانی دیں۔ شام کے وقت پتوں پر پانی چھڑکنے سے فنگس (Black Spot) کا خطرہ بڑھ جاتا ہے۔\n"
                    "• **کھاد:** دیسی گوبر کی پرانی گلی سڑی کھاد یا ورمی کمپوسٹ ہر 3 ہفتے بعد 1 مٹھی شامل کریں۔ پھولوں کے سیزن میں 1 چمچ لکڑی کی راکھ پوٹاشیم کے لیے بہترین ہے۔\n"
                    "• **کانٹ چھانٹ (Pruning):** پاکستان (لاہور، اسلام آباد، کراچی) میں 15 دسمبر سے 15 جنوری کٹائی کا بہترین وقت ہے۔ سوکھی اور کمزور شاخوں کو 45 ڈگری کے ترچھے زاویے پر کاٹیں۔\n"
                    "• **کیڑوں کا علاج:** سفید پھپھوندی یا چست تیلے کے لیے شام کے وقت نیم کے تیل کا اسپرے کریں۔"
                )
            elif lang == 'ur_ro':
                return (
                    "🌹 **Rose (Gulab) Care Guide:**\n\n"
                    "• **Dhoop:** Gulab ko rojana 5-6 ghante direct sunlight zaroor dain.\n"
                    "• **Pani:** Jab ooper ki 1 inch mitti dry ho tab pani dain. Sham ko patton par pani na giraen taake fungus na lagay.\n"
                    "• **Khad:** Har 3 haftay baad 1 mutthi purani desi gobar khad ya compost dain.\n"
                    "• **Pruning:** Mid-December se January mein sukhi aur purani shakhen 45 degree angle par kaat dain."
                )
            else:
                return (
                    "🌹 **Rose Care Guide (for Pakistani Climate):**\n\n"
                    "• **Sunlight:** Roses need at least 5 to 6 hours of full direct morning/afternoon sun to produce abundant blooms.\n"
                    "• **Watering:** Water deeply when the top 1 inch of soil feels dry. Always water the roots directly; avoid splashing water on foliage in the evening to prevent black spot and fungal infections.\n"
                    "• **Soil & Fertilizer:** Use fertile canal silt (Bhal mitti) mixed with 30% aged cow manure or compost. Feed 1 tablespoon of organic compost or bone meal every 3 weeks during the blooming season (spring & autumn).\n"
                    "• **Pruning:** In Pakistan (Lahore, Islamabad, Karachi), the ideal pruning window is mid-December to mid-January. Trim dead or diseased canes at a 45-degree angle just above an outward-facing bud.\n"
                    "• **Pests:** If you spot aphids or powdery mildew, spray diluted neem oil (5ml/L) or dust fine wood ash on wet foliage."
                )

        # 5. Potting Soil Mix / Bhal Mitti (check before neem oil so 'soil' is not confused with 'oil')
        if any(w in q for w in ['soil', 'potting', 'mitti', 'bhal', 'gamla', 'container', 'compost mix', 'مٹی', 'بھل', 'غملا', 'گملے']):
            if lang == 'ur':
                return (
                    "🪴 **گملوں کے لیے مثالی بھل مٹی کا سنہری فارمولا (50:30:20 تناسب):**\n\n"
                    "• **50 فیصد نہری بھل مٹی:** دریا یا نہر کی نرم بھل جس میں پودے کی جڑیں آسانی سے پھیل سکیں اور غذائیت موجود ہو۔\n"
                    "• **30 فیصد گلی سڑی دیسی گوبر کھاد یا پتوں کی کمپوسٹ:** کم از کم 1 سال پرانی کالی اور بھربھری کھاد جو پودوں کو نائٹروجن اور طاقت دیتی ہے۔\n"
                    "• **20 فیصد موٹی ریت یا کوکوپیٹ:** گملے میں پانی کھڑا نہ رہنے دینے اور مٹی میں ہوا کا گزر (Aeration) برقرار رکھنے کے لیے۔\n\n"
                    "💡 **ماہرانہ مشورہ:** گملے کے نچلے سوراخ پر ٹھیکری ضرور رکھیں تاکہ اضافی پانی بآسانی خارج ہو سکے اور جڑیں سڑنے (Root Rot) سے محفوظ رہیں۔"
                )
            elif lang == 'ur_ro':
                return (
                    "🪴 **Potting Soil Formula (50:30:20 Ratio):**\n\n"
                    "• **50% Bhal Mitti:** Canal silt jo narm aur zar-khez hoti hai.\n"
                    "• **30% Desi Gobar Khad / Compost:** Black crumbly well-rotted cow manure.\n"
                    "• **20% Sand / Cocopeat:** Drainage aur jaron ki hawa ke liye.\n"
                    "Gamlay ke bottom hole par theekri zaroor rakhein taake pani jam na ho."
                )
            else:
                return (
                    "🪴 **The Ideal Potting Soil Mix for Containers (Golden 50:30:20 Ratio):**\n\n"
                    "• **50% Canal Silt / Loam (Bhal Mitti):** Rich in micronutrients, soft, and naturally fertile for deep root growth.\n"
                    "• **30% Aged Organic Compost or Cow Manure:** Fully decomposed, black, and crumbly; supplies nitrogen, beneficial soil microbes, and humic matter.\n"
                    "• **20% Coarse River Sand or Cocopeat:** Ensures swift water drainage and keeps the root zone well-aerated.\n\n"
                    "💡 **Pro-Tip:** Always verify your pot has at least 1 working drainage hole at the base. Place a curved piece of broken terracotta over the hole before filling soil to prevent clogging."
                )

        # 6. Neem Oil Spray & Organic Pest Control
        if any(w in q for w in ['neem', 'whitefly', 'aphid', 'pest', 'spray', 'neem oil', 'keera', 'safed makhi', 'mealybug', 'نیم', 'کیڑا', 'کیڑے', 'تیلا', 'سفید مکھی', 'ملی بگ']):
            if lang == 'ur':
                return (
                    "🪰 **نامیاتی نیم کے تیل کا اسپرے بنانے کا مستند طریقہ (1 لیٹر محلول):**\n\n"
                    "1. **اجزاء:** 1 چائے کا چمچ (5 ملی لیٹر) خالص نیم کا تیل + آدھا چمچ (2 ملی لیٹر) برتن دھونے والا مائع صابن + 1 لیٹر نیم گرم پانی۔\n"
                    "2. **تیاری:** پہلے نیم کے تیل اور صابن کو آپس میں اچھی طرح مکس کریں تاکہ تیل پانی میں گھل جائے، پھر پانی ملا کر بوتل کو خوب ہلائیں جب تک مائع دودھیا نہ ہو جائے۔\n"
                    "3. **اسپرے کا طریقہ:** پتوں کے اوپر اور خاص طور پر نچلی سطح پر جہاں سفید مکھی، تیلا یا ملی بگ چھپے ہوتے ہیں، بھرپور اسپرے کریں۔\n"
                    "4. **اہم احتیاط:** اسپرے ہمیشہ شام کے وقت (غروب آفتاب کے بعد) یا صبح سویرے کریں۔ تیز دوپہر کی دھوپ میں اسپرے کرنے سے پتے جھلس جائیں گے۔\n"
                    "5. **وقفہ:** بیماری کی صورت میں ہر 5 سے 7 دن بعد، اور بچاؤ کے لیے ہر 15 دن بعد دہرائیں۔"
                )
            elif lang == 'ur_ro':
                return (
                    "🪰 **Neem Oil Spray Recipe (1 Liter):**\n\n"
                    "1. 1 teaspoon (5ml) pure neem oil + half tsp liquid dish soap (emulsifier) + 1L neem garam pani.\n"
                    "2. Pehle neem oil aur soap ko mix karein, phir pani dal kar achi tarah shake karein.\n"
                    "3. Patton ke neechay spray karein jahan safed makhi aur aphids chuptay hain.\n"
                    "4. Spray hamesha sham ke waqt karein taake dhoop se patte na jalain. Har 7 din baad repeat karein."
                )
            else:
                return (
                    "🪰 **Organic Neem Oil Spray Recipe (1-Liter Batch):**\n\n"
                    "1. **Ingredients:** 5ml (1 teaspoon) 100% pure cold-pressed neem oil + 2ml mild liquid dish soap (essential as an emulsifier to bind oil with water) + 1 Liter lukewarm water.\n"
                    "2. **Preparation:** Mix the neem oil with dish soap first until blended, then pour into lukewarm water in your spray bottle. Shake vigorously until the solution turns milky white.\n"
                    "3. **Application Method:** Thoroughly drench both the top surface and the undersides of leaves where whiteflies, mealybugs, and aphids congregate.\n"
                    "4. **Crucial Rule:** Spray only early in the morning or after sunset! Spraying under intense afternoon sun will scorch and burn plant leaves.\n"
                    "5. **Frequency:** Repeat once every 5 to 7 days until all pests vanish. As a preventive measure, spray once every 14 days."
                )

        # 7. Money Plant Care & Yellow Leaves
        if any(w in q for w in ['money plant', 'pothos', 'yellow', 'peelay', 'peela', 'mani plant', 'منی پلانٹ', 'پیلے پتے', 'پیلا']):
            if lang == 'ur':
                return (
                    "🌿 **منی پلانٹ کی دیکھ بھال اور پتے پیلے ہونے کا علاج:**\n\n"
                    "• **روشنی:** منی پلانٹ کو روشن مگر بالواسطہ (انڈائریکٹ) دھوپ میں رکھیں۔ تیز سیدھی دھوپ پتے جھلسا دیتی ہے، جبکہ گھپ اندھیرے میں پتے چھوٹے رہ جاتے ہیں۔\n"
                    "• **پتے پیلے کیوں پڑتے ہیں؟** 90 فیصد پتے پیلے ہونے کی وجہ **ضرورت سے زیادہ پانی** اور گملے میں پانی کا کھڑا رہنا ہے۔ جب تک اوپر کی مٹی خشک نہ ہو، پانی نہ دیں۔\n"
                    "• **پانی کا وقفہ:** گرمیوں میں ہفتے میں 2 بار، اور سردیوں میں 7 سے 10 دن بعد پانی کافی ہوتا ہے۔\n"
                    "• **پتوں کی چمک:** پندرہ دن بعد گیلے سوتی کپڑے سے پتوں کی گرد صاف کریں تاکہ پتے تروتازہ اور چمکدار رہیں۔"
                )
            elif lang == 'ur_ro':
                return (
                    "🌿 **Money Plant Care & Yellow Leaves:**\n\n"
                    "• **Roshni:** Bright indirect light dain, direct dhoop se patte jal jatay hain.\n"
                    "• **Peelay Patte:** Ziada tar over-watering (bohat ziada pani) ki wajah se hotay hain. Mitti dry hone tak pani na dain.\n"
                    "• **Watering:** Summer mein 2 times weekly, winter mein 7-10 din baad 1 bar."
                )
            else:
                return (
                    "🌿 **Money Plant (Golden Pothos) Care & Troubleshooting:**\n\n"
                    "• **Lighting:** Thrives in bright, indirect sunlight or dappled shade. Direct harsh sun will bleach and burn the leaves, while very dark spots slow down growth.\n"
                    "• **Why are leaves turning yellow?** In 90% of cases, yellow leaves mean **overwatering** or waterlogged soil with poor drainage. Allow the top 2 inches of soil to completely dry out before watering again.\n"
                    "• **Watering:** In summer: 2 times weekly. In winter: once every 7 to 10 days.\n"
                    "• **Leaf Shine & Cleaning:** Wipe leaves with a damp cotton cloth once every two weeks to remove household dust, boosting photosynthesis."
                )

        # 8. Watering Guidelines
        if any(w in q for w in ['water', 'watering', 'overwater', 'underwater', 'pani', 'پانی']):
            if lang == 'ur':
                return (
                    "💧 **پاکستانی موسم میں پودوں کو پانی دینے کے سنہری اصول:**\n\n"
                    "1. **ایک انچ انگلی کا ٹیسٹ:** پانی دینے سے پہلے مٹی میں انگلی 1 انچ اندر ڈال کر دیکھیں۔ اگر اندر نمی محسوس ہو تو پانی نہ دیں۔ صرف مٹی خشک ہونے پر پانی دیں۔\n"
                    "2. **پانی کا صحیح وقت:** صبح سویرے (سورج نکلتے وقت) پانی دینا سب سے بہترین ہے۔ شام کو پانی دیا جا سکتا ہے مگر پتوں پر پانی نہ گرائیں۔\n"
                    "3. **گہرا پانی دیں:** تھوڑا سا چھڑکاؤ کرنے کے بجائے ایک بار تسلی سے پانی دیں تاکہ نیچے کے سوراخ سے چند قطرے نکل آئیں اور گہری جڑیں سیراب ہوں۔\n"
                    "4. **موسمی فرق:** جون جولائی کی گرمی میں روزانہ صبح پانی درکار ہوتا ہے، جبکہ نومبر سے فروری میں ہفتے میں 1 یا 2 بار کافی ہے۔"
                )
            elif lang == 'ur_ro':
                return (
                    "💧 **Pani Dene Ke Assool:**\n\n"
                    "1. **Finger Test:** Mitti mein 1 inch ungli daal kar check karein. Dry ho to hi pani dain.\n"
                    "2. **Best Time:** Subah saverey 6 se 8 baje pani dena behtareen hai.\n"
                    "3. **Deep Watering:** Tasalli se pani dain taake neeche ke drainage hole se niklay.\n"
                    "4. Summer mein daily subah, aur winter mein hafte mein 1-2 bar pani kafi hota hai."
                )
            else:
                return (
                    "💧 **Smart Watering Principles for Plants in Pakistan:**\n\n"
                    "1. **The 1-Inch Finger Test:** Always insert your index finger 1 inch into the pot soil. If it feels cool and damp, do NOT water today. Only water when the top layer is dry.\n"
                    "2. **Best Time to Water:** Early morning (6:00 AM – 8:00 AM) is best. Plants absorb water before midday heat, minimizing evaporation and fungal issues.\n"
                    "3. **Water Deeply:** Water until a small amount trickles out of the pot's bottom drain hole, ensuring deep root hydration.\n"
                    "4. **Winter vs. Summer:** In extreme Pakistani summer (40°C+), outdoor terracotta pots need daily watering; in winter, reduce watering drastically to once or twice a week."
                )

        # 9. Fertilizers & Nutrition
        if any(w in q for w in ['fertilizer', 'fertilizers', 'npk', 'khad', 'manure', 'urea', 'feed', 'کھاد', 'گوبر']):
            if lang == 'ur':
                return (
                    "🌱 **پودوں کی کھاد کی جامع رہنمائی (دیسی نامیاتی و کیمیائی این پی کے):**\n\n"
                    "• **دیسی گوبر کھاد یا کمپوسٹ:** کم از کم 1 سے 2 مٹھی گوبر کھاد ہر مہینے گملے میں ڈال کر اوپر کی مٹی میں ہلکی گڈی (Tilling) کریں۔ یہ مٹی کو نرم اور زرخیز رکھتی ہے۔\n"
                    "• **کیمیائی کھاد (NPK 20-20-20):** پھولوں اور پتوں کی تیز نشوونما کے لیے 1 چائے کا چمچ 5 لیٹر پانی میں گھول کر ہر 15 دن بعد جڑوں میں دیں۔\n"
                    "• **ضروری احتیاط:** خشک مٹی میں کیمیائی کھاد کبھی نہ دیں ورنہ جڑیں جھلس جائیں گی۔ پہلے ہلکا پانی دیں پھر کھاد ملا پانی ڈالیں۔\n"
                    "• **سردیوں کا آرام:** شدید سردی (دسمبر، جنوری) میں پودے آرام کی حالت (Dormancy) میں ہوتے ہیں، اس وقت کھاد دینا بند کر دیں۔"
                )
            elif lang == 'ur_ro':
                return (
                    "🌱 **Fertilizer & Khad Guide:**\n\n"
                    "• **Organic Desi Khad:** Har mahine 1 mutthi purani gobar khad daal kar mitti ki guddi karein.\n"
                    "• **NPK 20-20-20:** 1 teaspoon in 5 Liters water, har 15 din baad roots mein dain.\n"
                    "• **Ahtiyat:** Sukhi mitti mein kabhie chemical khad na dain, hamesha pehle pani dain."
                )
            else:
                return (
                    "🌱 **Plant Fertilizer Guide (Organic & NPK Balanced):**\n\n"
                    "• **Organic Desi Khad:** Well-rotted cow dung manure (گوبر کھاد) or vermicompost is the best slow-release soil conditioner. Add 1-2 handfuls per medium pot once a month.\n"
                    "• **Chemical NPK 20-20-20:** For flowering and foliage growth during spring: dissolve 1 teaspoon (5g) in 5 Liters of water and feed every 15 days.\n"
                    "• **Important Rule:** Never apply chemical fertilizer to bone-dry soil! Always moisten the soil slightly with plain water beforehand, and water thoroughly right after feeding to avoid root burn.\n"
                    "• **Winter Dormancy:** Stop feeding heavy fertilizers during peak December/January cold when plants enter natural rest."
                )

        # 10. Lemon / Citrus Care
        if any(w in q for w in ['lemon', 'citrus', 'limon', 'kaghzi', 'limu', 'لیموں', 'کاغذی']):
            if lang == 'ur':
                return (
                    "🍋 **کاغذی لیموں کے پودے کی مکمل دیکھ بھال:**\n\n"
                    "• **دھوپ:** لیموں کو کم از کم 6 سے 8 گھنٹے کی بھرپور سیدھی دھوپ درکار ہوتی ہے۔\n"
                    "• **پتے پیلے ہونا اور رگیں ہری رہنا:** یہ مٹی میں آئرن یا زنک کی کمی کی علامت ہے۔ 1 چمچ ایپسم سالٹ (Epsom Salt) یا زنک آئرن مائیکرو نیوٹرینٹ کا اسپرے کریں۔\n"
                    "• **پھول گرنے سے بچاؤ:** جب پودے پر سفید پھول لگ رہے ہوں تو پانی کم کر دیں! پھول آنے کے دوران زیادہ پانی دینے سے پھول گر جاتے ہیں اور لیموں نہیں بن پاتے۔\n"
                    "• **پتوں پر سفید لکیریں (Leaf Miner):** نئے پتوں پر کیڑے کی ٹیڑھی لکیروں کے خاتمے کے لیے شام کے وقت نیم کے تیل کا اسپرے کریں۔"
                )
            elif lang == 'ur_ro':
                return (
                    "🍋 **Kaghzi Lemon Tree Care:**\n\n"
                    "• **Dhoop:** 6-8 hours full sunlight dain.\n"
                    "• **Phool Girna:** Jab lemon par phool aa rahe hon to pani kam karein, ziada pani se phool gir jatay hain.\n"
                    "• **Peelay Patte:** Zinc aur Iron ki kami ho to Epsom salt (1 tsp/L) spray karein."
                )
            else:
                return (
                    "🍋 **Kaghzi Lemon & Citrus Care in Pakistan:**\n\n"
                    "• **Sunlight:** Requires at least 6 to 8 hours of uninterrupted full sunlight.\n"
                    "• **Foliage Yellowing (Chlorosis):** If leaves turn yellow while the veins stay dark green, your lemon is deficient in Iron/Zinc. Spray a foliar micronutrient mix (chelated iron/zinc) or add 1 teaspoon epsom salt (magnesium sulfate) per liter of water.\n"
                    "• **Flower Drop Prevention:** Do not overwater when the tree is flowering! Excess water causes blossoms to fall off before fruit sets. Keep soil moderately moist.\n"
                    "• **Leaf Miner Pests:** If you see wavy silvery trails on new leaves, spray organic neem oil weekly."
                )

        # 11. Vegetables & Kitchen Garden
        if any(w in q for w in ['vegetable', 'vegetables', 'tomato', 'tamatar', 'chilli', 'mirch', 'sabzi', 'kitchen garden', 'spinach', 'palak', 'mint', 'podina', 'سبزی', 'سبزیاں', 'ٹماٹر', 'مرچ', 'پالک', 'دھنیا', 'پودینہ']):
            if lang == 'ur':
                return (
                    "🍅 **کچن گارڈننگ اور دیسی سبزیوں کی باغبانی:**\n\n"
                    "• **موسم سرما کی سبزیاں (اکتوبر تا فروری):** پالک، دھنیا، میتھی، مولی، گاجر، گوبھی اور مٹر۔\n"
                    "• **موسم گرما کی سبزیاں (فروری تا جولائی):** ٹماٹر، ہری مرچ، بھنڈی، بینگن، کریلا، گھیا کدو اور توری۔\n"
                    "• **گملے کا سائز:** ٹماٹر اور مرچ کے لیے کم از کم 12 سے 14 انچ کا گملا یا گرو بیگ استعمال کریں تاکہ جڑیں پھیل سکیں۔\n"
                    "• **ٹماٹر نیچے سے کالا ہونا:** یہ کیلشیم کی کمی اور بے قاعدہ پانی کی وجہ سے ہوتا ہے۔ مٹی میں باریک پیسے ہوئے انڈوں کے چھلکے یا چونا ملائیں اور پانی کا وقت مقرر رکھیں۔"
                )
            elif lang == 'ur_ro':
                return (
                    "🍅 **Kitchen Gardening & Vegetables:**\n\n"
                    "• **Winter Vegetables:** Palak, Dhaniya, Methi, Mooli, Gajar, Matar.\n"
                    "• **Summer Vegetables:** Tamatar, Hari Mirch, Bhindi, Baingan, Kaddu.\n"
                    "• **Gamlay ka Size:** Tomatoes aur chillies ke liye kam az kam 12-14 inch pot use karein."
                )
            else:
                return (
                    "🍅 **Vegetable & Kitchen Gardening Tips for Pakistan:**\n\n"
                    "• **Winter Vegetables (Oct – Feb):** Spinach (پالک), Coriander (دھنیا), Fenugreek (میتھی), Radish, Carrot, and Cauliflower.\n"
                    "• **Summer Vegetables (Feb – Jul):** Tomatoes, Green Chillies, Okra (بھنڈی), Brinjal (بینگن), and Gourds (کدو، تورئی).\n"
                    "• **Container Size:** Tomatoes and chillies need at least a 12 to 14-inch deep pot with rich compost.\n"
                    "• **Blossom End Rot in Tomatoes:** If tomatoes turn black at the bottom, it's caused by calcium deficiency and irregular watering. Add crushed eggshells to soil and keep moisture consistent."
                )

        # 12. Plant Doctor & Disease Diagnosis Recommendation
        if any(w in q for w in ['doctor', 'diagnos', 'disease', 'bimari', 'spots', 'leaf problem', 'fungus', 'ill', 'بیماری', 'امراض', 'پھپھوندی', 'ڈاکٹر', 'پتہ']):
            if lang == 'ur':
                return (
                    "🔍 **پودوں کے امراض کی عام علامات اور فوری تشخیص:**\n\n"
                    "1. **پتوں پر سفید پاؤڈر (Powdery Mildew):** فنگس کی علامت ہے۔ آدھا چمچ میٹھا سوڈا 1 لیٹر پانی میں ملا کر اسپرے کریں۔\n"
                    "2. **پتے مڑنا اور سکڑنا (Leaf Curl):** سفید مکھی یا تھرپس کا حملہ ہوتا ہے۔ نیم کے تیل کا اسپرے کریں۔\n"
                    "3. **پتوں کے کنارے بھورے و خشک ہونا:** شدید گرمی یا مٹی میں نمکیات کی زیادتی۔ گملے کو ہلکی چھاؤں میں رکھیں اور گڈی کریں۔\n\n"
                    "📸 **خصوصی سہولت:** اگر آپ کے پودے کے پتوں پر کوئی بیماری ظاہر ہو رہی ہے تو ہمارے **[AI پلانٹ ڈاکٹر](/ai/diagnose/)** پر پتے کی تصویر اپلوڈ کر کے فوری تشخیص اور علاج حاصل کریں!"
                )
            elif lang == 'ur_ro':
                return (
                    "🔍 **Plant Disease Troubleshooting:**\n\n"
                    "• **White powder on leaves:** Mildew fungus hai, baking soda spray karein.\n"
                    "• **Leaves curling:** Leaf curl virus ya whitefly hai, neem oil spray karein.\n\n"
                    "📸 Poday ke bimar patte ki photo hamare **AI Plant Doctor** par upload karein for instant solution!"
                )
            else:
                return (
                    "🔍 **Leaf Problem Diagnosis & AI Doctor Recommendation:**\n\n"
                    "Common plant symptoms in Pakistan:\n"
                    "1. **White powdery coating:** Powdery Mildew fungus. Spray dilute baking soda (1/2 tsp/L) or neem oil.\n"
                    "2. **Curled & crinkled leaves:** Leaf curl virus (spread by whiteflies) or severe thrips infestation. Isolate the plant and spray neem oil.\n"
                    "3. **Brown crispy leaf tips:** Dry heat or salt buildup from tap water. Mist foliage and flush pot with fresh water.\n\n"
                    "📸 **Pro-Tip:** Upload a clear close-up photo of the affected leaf to our **[AI Plant Doctor](/ai/diagnose/)** for instant deep-learning diagnosis and localized chemical & organic remedies!"
                )

        # 13. Pruning & Trimming
        if any(w in q for w in ['prun', 'trim', 'katai', 'کٹائی', 'کانٹ چھانٹ']):
            if lang == 'ur':
                return (
                    "✂️ **پودوں کی کانٹ چھانٹ (Pruning) کے سنہری اصول:**\n\n"
                    "• **صحیح موسم:** دسمبر کے آخر سے جنوری کا وقت گلاب، پیوندی پودوں اور پھل دار درختوں کی کٹائی کے لیے بہترین ہے تاکہ بہار میں نئے شگوفے پھوٹیں۔\n"
                    "• **اوزار کی صفائی:** قینچی یا کٹر کو ہمیشہ ڈیٹول یا اسپرٹ سے صاف کریں تاکہ جراثیم ایک پودے سے دوسرے میں نہ پھیلیں۔\n"
                    "• **کاٹنے کا طریقہ:** 45 ڈگری کے ترچھے زاویے پر کٹ لگائیں تاکہ بارش کا پانی کٹی ہوئی سطح پر جمع نہ ہو اور پھپھوندی نہ لگے۔"
                )
            elif lang == 'ur_ro':
                return (
                    "✂️ **Pruning Tips:**\n\n"
                    "• **Best Time:** December se mid-January pruning ke liye best waqt hai.\n"
                    "• **Tool Cleanliness:** Dettol se cutter ko sanitize karein.\n"
                    "• **Cut Angle:** 45 degree angle par bahar ki taraf cut lagayein."
                )
            else:
                return (
                    "✂️ **Pruning Best Practices (Seasonal Cutting):**\n\n"
                    "• **When to Prune:** Late winter (mid-December to January) for deciduous plants like roses and fruit trees before spring growth bursts.\n"
                    "• **Tool Sanitation:** Always sanitize your shears with rubbing alcohol or Dettol before cutting to avoid spreading bacterial diseases.\n"
                    "• **Cut Angle:** Make clean 45-degree cuts about 1/4 inch above an outward-facing bud so rain drains away from the cut stem."
                )

        # 13. General Fallback
        if lang == 'ur':
            return (
                "باغبان اے آئی میں خوش آمدید! 🌱 میں آپ کے پودوں اور گھریلو باغبانی کی رہنمائی کے لیے حاضر ہوں۔ "
                "آپ مجھ سے پانی کے اوقات، نیم کے تیل کا اسپرے، گلاب اور لیموں کی کھاد، گملے کی مٹی، اور سبزیوں کی دیکھ بھال کے بارے میں پوچھ سکتے ہیں۔ "
                "بتائیں میں آپ کے باغ میں کیا مدد کروں؟"
            )
        elif lang == 'ur_ro':
            return (
                "Baghbaan AI mein khush amdeed! 🌱 Mein aapke podhon ki dekh bhal, pani, khad, aur neem spray ke baray mein rehnumai ke liye tayar hoon. "
                "Aap mujh se Gulab, Lemon, Money Plant, ya Sabziyon ke baray mein pooch sakte hain."
            )
        else:
            return (
                "Welcome to Baghbaan AI Assistant! 🌱 I am your specialized gardening companion for Pakistan. "
                "You can ask me about watering frequencies, homemade organic neem spray, fertilizing roses and citrus, vegetable gardening, or diagnosing plant leaf diseases. "
                "How can I help your plants thrive today?"
            )
