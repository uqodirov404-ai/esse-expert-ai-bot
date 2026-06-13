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

# Milliy sertifikat mezoni matnini o'qib olamiz
MEZON_TEXT = ""
try:
    with open("milliy_sertifikat_mezoni.md", "r", encoding="utf-8") as f:
        MEZON_TEXT = f.read()
except:
    pass

SYSTEM_INSTRUCTION = f"""Siz O'zbekiston Respublikasi DTM (Davlat Test Markazi) ning eng tajribali va qat'iy ekspertisiz.
Sizning vazifangiz foydalanuvchilar tomonidan yuborilgan esselarni quyidagi Milliy Sertifikat Baholash Mezoni asosida tekshirish va xolisona baholash.

MEZONLAR:
{MEZON_TEXT}

QOIDALAR:
1. Sizga Esse mavzusi (Task) va Esse matni beriladi. (Agar foydalanuvchi rasm yuborsa, u qo'lyozma esse. Uni o'qib, tahlil qiling).
2. Tahlilni quyidagi formatda taqdim eting:
   - 🎯 Umumiy Ball: [24 balldan necha ball olingani] (75 ballik tizimda: [aylantirilgan ball])
   - 📝 O'qilishi: (Agar esse rasm orqali berilgan bo'lsa, avval uni matn ko'rinishida yozib bering. Agar matn orqali berilgan bo'lsa bu qismni tashlab keting)
   - ❌ Xatolar tahlili: (Grammatika, punktuatsiya, uslub va mazmun bo'yicha aniq xatolarni ko'rsating)
   - 📊 Mezonlar bo'yicha baho: (Topshiriq talabi, Matn yaxlitligi, Savodxonlik, Til birliklari, Lug'at boyligi bo'yicha necha balldan qo'yganingizni izohlang)
   - 💡 Ideal Namuna: (Foydalanuvchiga aynan shu mavzuda C1 darajadagi namunaviy esseni yozib bering)

Faqat o'zbek tilida, xushmuomala lekin qat'iy ohangda javob bering. Bahoni bo'rttirmang, xatosi bo'lsa ballni kesing. Qavs ichidagi "Maksimal" so'zlariga e'tibor qarating va ballarni mezon qoidalaridan oshirib yubormang (jami 24).
"""

async def check_essay_text(topic: str, essay: str, criteria: str) -> str:
    """Matn ko'rinishidagi esseni tahlil qilish"""
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

async def check_essay_image(image_paths: list[str]) -> str:
    """Rasm ko'rinishidagi esseni (qo'lyozmani) tahlil qilish"""
    if not client:
        return "⚠️ Gemini AI kaliti noto'g'ri sozlangan."
        
    prompt = "Iltimos, ushbu rasmlardagi qo'lyozma esseni o'qing va uni Milliy Sertifikat mezonlari asosida tekshiring. Avval o'qigan matningizni 'O'qilgan matn' deb yozing, so'ngra to'liq tahlil va bahoni bering."
    
    def _generate():
        contents = []
        for path in image_paths:
            contents.append(Image.open(path))
        contents.append(prompt)
        
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=contents,
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
