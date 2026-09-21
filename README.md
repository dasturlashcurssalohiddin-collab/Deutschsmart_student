# 🇩🇪 Deutsch_smart_schule — 24/7 Elektron Kundalik & Telegram Bot

Ushbu loyiha **GitHub + Vercel** orqali 24/7 kompyutersiz, mutlaqo bepul ishlash uchun to'liq sozlangan.

---

## 📁 GitHub'ga Yuklanadigan Asosiy Fayllar:

| Fayl | Vazifasi |
|---|---|
| **`index.html`** | Kirish va Ro'yxatdan o'tish (Telefon, Email, Parol, Ustoz minimal 20 yosh va fanlar, O'quvchi ma'lumotlari). Barcha CSS/JS o'z ichida. |
| **`student.html`** | O'quvchilar haqida ma'lumot beruvchi Asosiy Oyna (O'quvchi va Ota-ona uchun 1 ta oyna, Davomat: Bor/Yo'q/Kasal, Kundalik baholari). |
| **`teacher.html`** | Ustoz Paneli (Kundalik.com jurnali, katakchalarda davomat va baho qo'yish, o'z sinflari arxivi). |
| **`api/bot.py`** | **24/7 Telegram Serverless Webhook Bot** — Ism yozilganda saytdan qidiradi, topilsa ma'lumotlarini chiqaradi, topilmasa *"❌ Bunday o'quvchi yo'q"* deydi. |
| **`vercel.json`** | Vercel'da sayt, API va botni 24/7 doimiy ishlatish konfiguratsiyasi. |
| **`requirements.txt`** | Vercel uchun kerakli kutubxonalar ro'yxati. |
| **`django_admin.py`** | Django Admin panel modellar va sozlamalari (chiqarib yuborish va sinflar arxivi). |

---

## 🚀 1. GitHub'ga Yuklash

Ushbu papkani GitHub'ga yuklang:
```bash
git init
git add .
git commit -m "Deutsch smart schule loyihasi"
git branch -M main
git remote add origin https://github.com/SIZNING_USERNAME/SIZNING_REPO.git
git push -u origin main
```

---

## ⚡️ 2. Vercel'ga Ulash va O'zgaruvchilarni Kiritish

1. [Vercel.com](https://vercel.com) ga kiring va **"Add New Project"** tugmasini bosing.
2. GitHub repozitoriyangizni tanlang.
3. **"Environment Variables"** (Muhit o'zgaruvchilari) bo'limida quyidagilarni kiriting:
   - `TELEGRAM_BOT_TOKEN`: `8842438171:AAHEzdaxD5HmITPhsdO1DFzTNrVlzg8nhq4`
   - `ADMIN_CHAT_ID`: `6283517295`
   - `FIREBASE_PROJECT_ID`: `deutschsmart-72eb9`
4. **Deploy** tugmasini bosing!

---

## 🤖 3. Telegram Botni 24/7 Ishga Tushirish (1 bosishda!)

Saytingiz Vercel'da ochilgach (masalan: `https://deutsch-smart.vercel.app`), brauzeringizda quyidagi manzilni oching:

👉 `https://SIZNING-DOMEN.vercel.app/api/bot?set_webhook=1`

Ekranda:
```json
{
  "success": true,
  "webhook_url": "https://SIZNING-DOMEN.vercel.app/api/bot",
  "telegram_response": { "ok": true, "result": true, "description": "Webhook was set" }
}
```
yozuvi chiqadi. 

**Bo'ldi!** Endi botingiz [@deutschsmart_student_bot](https://t.me/deutschsmart_student_bot) 24/7 Vercel'da ishlaydi:
- Telegramda istalgan ismni yozsangiz (masalan: `Jasur`, `Madina` yoki yangi ro'yxatdan o'tgan o'quvchi ismi):
  - Agar saytda bo'lsa ➔ Uning sinfi, ota-onasi, davomati (Bor/Yo'q/Kasal) va baholarini chiqaradi!
  - Agar saytda bo'lmasa ➔ **"❌ Bunday o'quvchi yo'q"** degan xabar beradi!
