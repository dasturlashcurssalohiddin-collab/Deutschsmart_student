import logging
import requests
from django.conf import settings
from .models import TelegramSubscriber

logger = logging.getLogger(__name__)

def send_telegram_message(chat_id, text):
    """
    Telegram Bot API orqali xabar yuborish
    """
    token = getattr(settings, 'TELEGRAM_BOT_TOKEN', None)
    if not token or token == 'YOUR_TELEGRAM_BOT_TOKEN_HERE':
        logger.info(f"[TG MOCK] -> ChatID {chat_id}: {text}")
        print(f"\n[TELEGRAM BOT LOG] ChatID {chat_id}:\n{text}\n")
        return True

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        'chat_id': chat_id,
        'text': text,
        'parse_mode': 'HTML'
    }
    try:
        response = requests.post(url, json=payload, timeout=5)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Telegram yuborishda xatolik: {e}")
        return False


def notify_parent_grade(grade):
    """
    Ustoz baho qo'yganda ota-onaga bildirishnoma jo'natish
    """
    student = grade.student
    subscribers = TelegramSubscriber.objects.filter(
        student=student, 
        is_active=True
    )

    msg = (
        f"🇩🇪 <b>Deutschsmart Student — Yangi Baho!</b>\n\n"
        f"👤 <b>O'quvchi:</b> {student.full_name} ({student.grade_class.name})\n"
        f"📚 <b>Fan:</b> {grade.subject.name}\n"
        f"⭐️ <b>Baho:</b> {grade.score}\n"
        f"📅 <b>Sana:</b> {grade.date}\n"
    )
    if grade.comment:
        msg += f"💬 <b>Ustoz izohi:</b> <i>{grade.comment}</i>\n"

    msg += f"\n🌐 <i>Batafsil kundalikda ko'rish uchun saytga kiring.</i>"

    for sub in subscribers:
        send_telegram_message(sub.chat_id, msg)


def notify_parent_attendance(attendance):
    """
    O'quvchi darsda yo'q yoki kasal bo'lsa ota-onaga ogohlantirish
    """
    if attendance.status not in ['absent', 'sick']:
        return

    student = attendance.student
    subscribers = TelegramSubscriber.objects.filter(
        student=student, 
        is_active=True
    )

    status_text = "Darsda YO'Q (Sababsiz)" if attendance.status == 'absent' else "KASAL (Sababli)"
    status_emoji = "🔴" if attendance.status == 'absent' else "🟡"

    msg = (
        f"⚠️ <b>Deutschsmart Student — Davomat Ogohlantirishi</b>\n\n"
        f"👤 <b>O'quvchi:</b> {student.full_name} ({student.grade_class.name})\n"
        f"📅 <b>Sana:</b> {attendance.date}\n"
        f"{status_emoji} <b>Holati:</b> <b>{status_text}</b>\n\n"
        f"Iltimos, dars qoldirilishi sababini aniqlashtiring."
    )

    for sub in subscribers:
        send_telegram_message(sub.chat_id, msg)
