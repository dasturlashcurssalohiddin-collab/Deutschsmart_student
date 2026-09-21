#!/usr/bin/env python3
"""
Deutschsmart Student - Telegram Bot
Loyihasi uchun maxsus sozlangan Telegram Bot

Rejimlar:
1. Oddiy rejim (Polling):
   python3 bot.py
2. Vercel'ga 24/7 ulash rejimi (Webhook):
   python3 bot.py --set-webhook https://sizning-domen.vercel.app
"""

import os
import sys
import time
import json
import logging
import requests

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Haqiqiy ma'lumotlar
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8842438171:AAHEzdaxD5HmITPhsdO1DFzTNrVlzg8nhq4")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "6283517295")

API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Standart o'quvchilar bazasi (namuna)
DEFAULT_STUDENTS = [
    {
        "id": "s1",
        "fullName": "Jasur Karimov",
        "email": "student@deutschsmart.uz",
        "phone": "+998931112233",
        "parentPhone": "+998979998877",
        "password": "123",
        "gradeClass": "7-G",
        "parentName": "Karimov Rustam",
        "attendance": { "present": 12, "absent": 1, "sick": 2 },
        "grades": [
            {"subject": "Nemis tili A1", "scores": [5, 4, 5]},
            {"subject": "Grammatika", "scores": [5, 5]}
        ]
    },
    {
        "id": "s2",
        "fullName": "Madina Rahimova",
        "email": "madina@deutschsmart.uz",
        "phone": "+998991230002",
        "parentPhone": "+998991230001",
        "password": "123",
        "gradeClass": "7-G",
        "parentName": "Rahimova Nargiza",
        "attendance": { "present": 14, "absent": 0, "sick": 1 },
        "grades": [
            {"subject": "Nemis tili A1", "scores": [5, 5, 4]}
        ]
    }
]

user_states = {}


def send_message(chat_id, text, reply_markup=None):
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    if reply_markup:
        payload["reply_markup"] = json.dumps(reply_markup)
    try:
        res = requests.post(f"{API_URL}/sendMessage", json=payload, timeout=10)
        return res.json()
    except Exception as e:
        logging.error(f"Xabar yuborishda xatolik: {e}")
        return None


def handle_message(message):
    chat_id = message["chat"]["id"]
    text = message.get("text", "").strip()

    state = user_states.get(chat_id, {"step": "START"})

    if text == "/start" or state["step"] == "START":
        user_states[chat_id] = {"step": "WAITING_ID"}
        welcome_text = (
            "🇩🇪 <b>Deutschsmart Student Botiga xush kelibsiz!</b>\n\n"
            "O'quvchi haqida ma'lumot (davomat va baholar)ni olish uchun, iltimos:\n"
            "O'quvchining <b>Telefon raqami</b>, <b>Emaili</b> yoki <b>Ism-familiyasini</b> kiriting:\n\n"
            "<i>(Masalan: +998931112233 yoki Jasur Karimov)</i>"
        )
        send_message(chat_id, welcome_text)
        return

    # 1-QADAM: Identifikator kiritildi -> Parol so'raymiz
    if state["step"] == "WAITING_ID":
        user_states[chat_id] = {
            "step": "WAITING_PASSWORD",
            "identifier": text
        }
        send_message(chat_id, f"✅ <b>Kiritildi:</b> {text}\n\n🔐 Endi hisob <b>parolini</b> kiriting:")
        return

    # 2-QADAM: Parol kiritildi -> Tekshiramiz
    if state["step"] == "WAITING_PASSWORD":
        raw_input = state.get("identifier", "").strip()
        identifier_clean = raw_input.lower().replace(" ", "").replace("+", "")
        password = text

        found_student = None

        for st in DEFAULT_STUDENTS:
            p1 = st["phone"].replace(" ", "").replace("+", "").lower()
            p2 = st["parentPhone"].replace(" ", "").replace("+", "").lower()
            email = st["email"].lower()
            name = st["fullName"].lower()

            if (identifier_clean in [p1, p2] or 
                raw_input.lower() == email or 
                raw_input.lower() == name):
                if st["password"] == password:
                    found_student = st
                    break

        if found_student:
            att = found_student["attendance"]
            total_days = att["present"] + att["absent"] + att["sick"]
            rate = round((att["present"] / total_days * 100)) if total_days > 0 else 100

            grades_text = ""
            for g in found_student["grades"]:
                scores_str = ", ".join(map(str, g["scores"]))
                avg = round(sum(g["scores"]) / len(g["scores"]), 1)
                grades_text += f"• <b>{g['subject']}:</b> {scores_str} <i>(O'rtacha: {avg})</i>\n"

            msg = (
                f"🎓 <b>O'quvchi ma'lumotlari:</b>\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"👤 <b>F.I.SH:</b> {found_student['fullName']}\n"
                f"🏫 <b>Sinf:</b> {found_student['gradeClass']}\n"
                f"👨‍👩‍👧 <b>Ota-onasi:</b> {found_student['parentName']}\n"
                f"📞 <b>Telefon:</b> {found_student['phone']}\n\n"
                f"📊 <b>Davomat holati:</b>\n"
                f"🟢 Bor: <b>{att['present']} kun</b>\n"
                f"🔴 Dars qoldirgan: <b>{att['absent']} kun</b>\n"
                f"🟡 Kasallik: <b>{att['sick']} kun</b>\n"
                f"📈 Umumiy davomat ko'rsatkichi: <b>{rate}%</b>\n\n"
                f"⭐️ <b>Kundalik baholari:</b>\n"
                f"{grades_text}\n"
                f"━━━━━━━━━━━━━━━━━━━━\n"
                f"🌐 <i>Sayt: deutschsmart_student</i>\n\n"
                f"🔄 Yangi so'rov uchun /start ni bosing."
            )
            send_message(chat_id, msg)
            user_states[chat_id] = {"step": "START"}
        else:
            err_msg = (
                "❌ <b>Bu bola maktabdan emas</b>\n\n"
                "Kiritilgan telefon, email yoki ism-familiya bo'yicha bola topilmadi yoki parol xato kiritildi!\n\n"
                "Qaytadan urinish uchun /start ni bosing."
            )
            send_message(chat_id, err_msg)
            user_states[chat_id] = {"step": "START"}


def set_webhook(domain):
    webhook_url = f"{domain.rstrip('/')}/api/telegram/webhook/"
    res = requests.post(f"{API_URL}/setWebhook", json={"url": webhook_url})
    print(f"Webhook o'rnatildi -> {webhook_url}: {res.json()}")


def main():
    if len(sys.argv) > 2 and sys.argv[1] == "--set-webhook":
        set_webhook(sys.argv[2])
        return

    logging.info("Deutschsmart Student Telegram Bot ishga tushmoqda...")
    offset = None
    while True:
        try:
            url = f"{API_URL}/getUpdates?timeout=20"
            if offset:
                url += f"&offset={offset}"
            res = requests.get(url, timeout=25)
            if res.status_code == 200:
                data = res.json()
                for update in data.get("result", []):
                    offset = update["update_id"] + 1
                    if "message" in update:
                        handle_message(update["message"])
            elif res.status_code == 401:
                logging.warning("Bot tokeni noto'g'ri. Iltimos tekshiring.")
                time.sleep(15)
        except Exception as e:
            logging.error(f"Polling xatosi: {e}")
            time.sleep(3)


if __name__ == "__main__":
    main()
