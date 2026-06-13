import os
from google import genai
from google.genai import types
from PIL import Image
import asyncio
from config import GEMINI_API_KEY

try:
    client = genai.Client(api_key=GEMINI_API_KEY)
except Exception as e:
    client = None
    print(f"Gemini Client xatosi: {e}")

MEZON_TEXT = ""
try:
    with open("milliy_sertifikat_mezoni.md", "r", encoding="utf-8") as f:
        MEZON_TEXT = f.read()
except:
    pass

IMLO_RULES = ""
try:
    with open("uzbek_imlo_qoidalari.md", "r", encoding="utf-8") as f:
        IMLO_RULES = f.read()
except:
    pass

PUNCTUATION_RULES = ""
try:
    with open("uzbek_punktuatsiya_qoidalari.md", "r", encoding="utf-8") as f:
        PUNCTUATION_RULES = f.read()
except:
    pass

SYSTEM_INSTRUCTION = f"""Siz O'zbekiston Respublikasi DTM (Davlat Test Markazi) ning eng tajribali va qat'iy ekspertisiz.
Sizning vazifangiz foydalanuvchilar tomonidan yuborilgan esselarni Milliy Sertifikat Baholash Mezoni, rasmiy O'zbek Tili Imlo Qoidalari va Tinish belgilari qoidalari asosida tekshirish va xolisona baholash.

MATNLAR (QONUN HJJATLAR):
1. MILLIY SERTIFIKAT BAHOLASH MEZONI:
{MEZON_TEXT}

2. O'ZBEK TILI IMLO QOIDALARI:
{IMLO_RULES}

3. O'ZBEK TILI TINISH BELGILARI (PUNKTUATSIYA) QOIDALARI:
{PUNCTUATION_RULES}

QAT'IY QOIDALAR (BU QOIDALARNI BUZISH TAQIQLANADI):
1. Essedagi har bir so'zning to'g'ri yozilishini va tinish belgilarini faqat va faqat yuqorida keltirilgan "O'ZBEK TILI IMLO QOIDALARI" va "O'ZBEK TILI TINISH BELGILARI QOIDALARI" matnlari asosida tekshiring. 
2. O'ZINGIZNING OLDINGI (TASHQI) BILIMLARINGIZDAN FOYDALANMANG! Agar taqdim etilgan kitob qoidasiga ko'ra biron bir ibora ajratib yozilishi kerak bo'lsa (Masalan, "kundan kunga", "yildan yilga", "tomdan tomga" kabi birinchi qismi chiqish kelishigida -dan, ikkinchi qismi jo'nalish kelishigida -ga bo'lgan birikmalar, Imlo qoidasining 63-bandiga muvofiq ajratib yoziladi), ularni chiziqcha bilan yozishni aslo to'g'ri deb hisoblamang va foydalanuvchiga noto'g'ri tuzatish tavsiya qilmang. Agar foydalanuvchi ularni to'g'ri (ajratib) yozgan bo'lsa, uni xato demang.
3. ESSENI TEKSHIRGANDA TO'G'RI YOZILGAN TARKIBLARNI, TINISH BELGILARINI YOKI GAPLARNI ASLO IZOHLAMANG VA MAQTAMANG. FAQAT XATOLARNI ANIQLAB, ULARNI IZOHLANG.
4. Xatolarga uzun va chigal izohlar bermang. Har bir xato tahlili o'ta qisqa, tushunarli va lo'nda bo'lishi shart.
5. Tahlilni quyidagi formatda taqdim eting:
   - 💯 Umumiy Ball: [24 balldan necha ball olingani] (75 ballik tizimda: [aylantirilgan ball])
   - 📝 O'qilishi: (Agar esse rasm orqali berilgan bo'lsa, avval uni matn ko'rinishida yozib bering. Agar matn orqali berilgan bo'lsa bu qismni tashlab keting)
   - 📉 Xatolar tahlili: (Faqat aniq grammatik, punktuatsion va uslubiy xatolarni juda qisqa va lo'nda ko'rsating. Uzun izohlar yozmang, shunchaki "xato -> to'g'ri variant" va qavs ichida juda qisqa qoida izohi bilan cheklaning. Masalan: `kundan-kunga` -> `kundan kunga` (Imlo qoidasi 63-bandga ko'ra ajratib yoziladi). To'g'ri jumlalar haqida umuman yozmang)
   - 📊 Mezonlar bo'yicha baho: (Topshiriq talabi, Matn yaxlitligi, Savodxonlik, Til birliklari, Lug'at boyligi bo'yicha necha balldan qo'yganingizni izohlang)
   - ✨ Ideal Namuna: (Foydalanuvchiga aynan shu mavzuda C1 darajadagi namunaviy esseni yozib bering)

Faqat o'zbek tilida, xushmuomala lekin qat'iy ohangda javob bering. Bahoni bo'rttirmang, xatosi bo'lsa ballni kesing. Qavs ichidagi "Maksimal" so'zlariga e'tibor qarating va ballarni mezon qoidalaridan oshirib yubormang (jami 24).
"""

async def check_essay_text(topic: str, essay: str, criteria: str) -> str:
    if not client:
        return "⚠️ Gemini AI kaliti noto'g'ri sozlangan."
        
    prompt = f"Mavzu: {topic}\n\nEsse matni:\n{essay}\n\nIltimos, ushbu esseni yuqoridagi mezonlarga asosan tekshiring."
    
    def _generate():
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.4
            )
        )
        return response.text

    try:
        result = await asyncio.to_thread(_generate)
        return result
    except Exception as e:
        return f"⚠️ Tahlil qilishda xatolik yuz berdi: {e}"

async def check_essay_image(image_paths: list) -> str:
    if not client:
        return "⚠️ Gemini AI kaliti noto'g'ri sozlangan."
        
    prompt = "Iltimos, ushbu rasmlardagi qo'lyozma esseni o'qing va uni Milliy Sertifikat mezonlari asosida tekshiring. Avval o'qigan matningizni 'O'qilgan matn' deb yozing, so'ngra to'liq tahlil va bahoni bering."
    
    def _generate():
        imgs = [Image.open(p) for p in image_paths]
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=imgs + [prompt],
            config=types.GenerateContentConfig(
                system_instruction=SYSTEM_INSTRUCTION,
                temperature=0.4
            )
        )
        return response.text

    try:
        result = await asyncio.to_thread(_generate)
        return result
    except Exception as e:
        return f"⚠️ Rasmni tahlil qilishda xatolik yuz berdi: {e}"
