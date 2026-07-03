# -*- coding: utf-8 -*-
"""
app/ocr/prompts/cin_prompts.py

Prompt d'extraction de la CIN (carte d'identite nationale tunisienne),
avec mapping explicite des mois arabes pour eviter la confusion
جانفي (janvier) / جويلية (juillet).
"""

PROMPT_CIN = (
    "هذه بطاقة تعريف وطنية تونسية.\n"
    "أعد فقط كائن JSON صالح — بدون أي نص آخر — بهذا الشكل الحرفي:\n"
    '{"doc_number":"...","last_name":"...","first_name":"...","birth_date":"DD/MM/YYYY"}\n'
    "اكتب القيم كما هي مكتوبة في البطاقة. لا تترجم الأسماء. إذا كانت القيمة غائبة اكتب null.\n\n"
    "مهم جدا لتاريخ الميلاد : الأشهر مكتوبة بأسماء تونسية/فرنسية بالعربية. "
    "استعمل هذا الجدول بدقة لتحويل اسم الشهر إلى رقم (MM)، ولا تخمن:\n"
    "جانفي=01, فيفري=02, مارس=03, أفريل=04, ماي=05, جوان=06, "
    "جويلية=07, أوت=08, سبتمبر=09, أكتوبر=10, نوفمبر=11, ديسمبر=12\n"
    "انتبه خصوصا للفرق بين جانفي (01) وجويلية (07) فهما يتشابهان أحيانا في القراءة."
)