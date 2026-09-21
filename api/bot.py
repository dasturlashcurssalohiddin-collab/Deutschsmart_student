import json
import os
import urllib.request
import urllib.parse
from http.server import BaseHTTPRequestHandler

# Vercel Environment Variables dan olinadi (agar berilmagan bo'lsa standartlar ishlatiladi)
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "8842438171:AAHEzdaxD5HmITPhsdO1DFzTNrVlzg8nhq4")
ADMIN_CHAT_ID = os.getenv("ADMIN_CHAT_ID", "6283517295")
FIREBASE_PROJECT_ID = os.getenv("FIREBASE_PROJECT_ID", "deutschsmart-72eb9")

API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Zaxira namunaviy o'quvchilar
STATIC_STUDENTS = [
    {
        "fullName": "Jasur Karimov",
        "gradeClass": "7-G",
        "parentName": "Karimov Rustam",
        "studentPhone": "+998931112233",
        "present": 12,
        "absent": 1,
        "sick": 2,
        "grades": "• Nemis tili A1: 5, 4, 5 (O'rtacha: 4.7)\n• Grammatika: 5, 5 (O'rtacha: 5.0)"
    },
    {
        "fullName": "Madina Rahimova",
        "gradeClass": "7-G",
        "parentName": "Rahimova Nargiza",
        "studentPhone": "+998991230002",
        "present": 14,
        "absent": 0,
        "sick": 1,
        "grades": "• Nemis tili A1: 5, 5, 4 (O'rtacha: 4.7)"
    }
]


def send_tg_message(chat_id, text):
    """Telegram Bot API ga xabar yuborish"""
    try:
        url = f"{API_URL}/sendMessage"
        payload = json.dumps({
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML"
        }).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=8) as resp:
            return resp.read()
    except Exception as e:
        print(f"Send message error: {e}")
        return None


def fetch_firestore_students():
    """Firebase Firestore dan ro'yxatdan o'tgan barcha o'quvchilarni olish"""
    students = []
    try:
        url = f"https://firestore.googleapis.com/v1/projects/{FIREBASE_PROJECT_ID}/databases/(default)/documents/students"
        req = urllib.request.Request(url, headers={"User-Agent": "Vercel-Bot"})
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            for doc in data.get("documents", []):
                fields = doc.get("fields", {})
                full_name = fields.get("fullName", {}).get("stringValue", "")
                if not full_name:
                    continue

                grade_class = fields.get("gradeClass", {}).get("stringValue", "7-G")
                parent_name = fields.get("parentName", {}).get("stringValue", "Kiritilmagan")
                student_phone = fields.get("studentPhone", {}).get("stringValue", "-")
                
                present = int(fields.get("attendancePresent", {}).get("integerValue", 12))
                absent = int(fields.get("attendanceAbsent", {}).get("integerValue", 0))
                sick = int(fields.get("attendanceSick", {}).get("integerValue", 0))
                grades = fields.get("gradesSummary", {}).get("stringValue", "• Nemis tili A1: 5, 5")

                students.append({
                    "fullName": full_name,
                    "gradeClass": grade_class,
                    "parentName": parent_name,
                    "studentPhone": student_phone,
                    "present": present,
                    "absent": absent,
                    "sick": sick,
                    "grades": grades
                })
    except Exception as e:
        print(f"Firestore fetch error: {e}")

    # Agar Firestore hali bo'sh bo'lsa yoki xatolik bo'lsa, zaxira o'quvchilarni qo'shamiz
    for st in STATIC_STUDENTS:
        if not any(s["fullName"].lower() == st["fullName"].lower() for s in students):
            students.append(st)

    return students


def search_student_by_name(query):
    """Kiritilgan ism bo'yicha qidirish"""
    query_clean = query.strip().lower()
    if not query_clean or query_clean in ["/start", "/help"]:
        return None

    students = fetch_firestore_students()
    
    # 1. To'liq yoki qisman moslikni qidirish
    for s in students:
        name_lower = s["fullName"].lower()
        # Masalan: "Jasur" yozilsa ham "Jasur Karimov" topiladi
        if query_clean in name_lower or any(word in name_lower.split() for word in query_clean.split()):
            return s
            
    return None


class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Vercel orqali Webhook sozlash yoki status tekshirish"""
        parsed_url = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed_url.query)

        host = self.headers.get("Host", "")
        proto = self.headers.get("x-forwarded-proto", "https")
        current_webhook_url = f"{proto}://{host}/api/bot"

        # Webhook o'rnatish
        if "set_webhook" in query or "setup" in query:
            try:
                set_url = f"{API_URL}/setWebhook?url={urllib.parse.quote(current_webhook_url)}"
                req = urllib.request.Request(set_url)
                with urllib.request.urlopen(req, timeout=8) as resp:
                    result = resp.read().decode("utf-8")
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({
                    "success": True,
                    "webhook_url": current_webhook_url,
                    "telegram_response": json.loads(result)
                }).encode("utf-8"))
                return
            except Exception as e:
                self.send_response(500)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
                return

        # Oddiy brauzerda ochilganda ko'rsatiladigan ma'lumot
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps({
            "status": "online",
            "bot": "@deutschsmart_student_bot",
            "message": "Deutschsmart Telegram Bot Vercel'da 24/7 ishlamoqda!",
            "setup_webhook_url": f"{current_webhook_url}?set_webhook=1"
        }, indent=2).encode("utf-8"))

    def do_POST(self):
        """Telegram Webhook yangilanishlarini qabul qilish"""
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length)

        try:
            update = json.loads(post_data.decode("utf-8"))
            if "message" in update and "text" in update["message"]:
                chat_id = update["message"]["chat"]["id"]
                text = update["message"]["text"].strip()

                # 1. /start buyrug'i
                if text == "/start":
                    welcome = (
                        "🇩🇪 <b>Deutschsmart Student Botiga xush kelibsiz!</b>\n\n"
                        "O'quvchi haqida ma'lumot (davomat va baholar)ni ko'rish uchun uning <b>Ismini yoki Familiyasini</b> yozing:\n\n"
                        "<i>(Masalan: Jasur yoki Madina)</i>"
                    )
                    send_tg_message(chat_id, welcome)

                # 2. Ism kiritilganda tekshirish
                else:
                    student = search_student_by_name(text)

                    if student:
                        # O'quvchi topildi -> Ma'lumotlarini chiqarish
                        total = student["present"] + student["absent"] + student["sick"]
                        rate = round((student["present"] / total * 100)) if total > 0 else 100

                        msg = (
                            f"🎓 <b>O'quvchi ma'lumotlari:</b>\n"
                            f"━━━━━━━━━━━━━━━━━━━━\n"
                            f"👤 <b>F.I.SH:</b> {student['fullName']}\n"
                            f"🏫 <b>Sinfi:</b> {student['gradeClass']}\n"
                            f"👨‍👩‍👧 <b>Ota-onasi:</b> {student['parentName']}\n"
                            f"📞 <b>Telefon:</b> {student['studentPhone']}\n\n"
                            f"📊 <b>Davomat holati:</b>\n"
                            f"🟢 Bor: <b>{student['present']} kun</b>\n"
                            f"🔴 Dars qoldirgan: <b>{student['absent']} kun</b>\n"
                            f"🟡 Kasallik: <b>{student['sick']} kun</b>\n"
                            f"📈 Davomat ko'rsatkichi: <b>{rate}%</b>\n\n"
                            f"⭐️ <b>Kundalik baholari:</b>\n"
                            f"{student['grades']}\n"
                            f"━━━━━━━━━━━━━━━━━━━━\n"
                            f"🔍 Boshqa o'quvchini qidirish uchun ismini yozing."
                        )
                        send_tg_message(chat_id, msg)
                    else:
                        # TALAB: "aks holda bunday o'quvchi yo'q desin"
                        send_tg_message(chat_id, f"❌ <b>Bunday o'quvchi yo'q</b>\n\n\"{text}\" ismli o'quvchi maktab bazasidan topilmadi!\nIltimos, ism yoki familiyani to'g'ri yozing.")

        except Exception as e:
            print(f"POST Error: {e}")

        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"ok": true}')
