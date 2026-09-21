from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from datetime import datetime, date
import json
import logging

from .models import CustomUser, Subject, ClassRoom, TeacherProfile, StudentProfile, Attendance, Grade
from .serializers import (
    UserSerializer, TeacherProfileSerializer, StudentProfileSerializer,
    AttendanceSerializer, GradeSerializer
)
from .telegram_service import notify_parent_attendance, notify_parent_grade, send_telegram_message

logger = logging.getLogger(__name__)

# Foydalanuvchilarning Telegram sessiyalari (xotirada)
TG_USER_STATES = {}


class CheckUserView(APIView):
    """
    Telefon YOKI Email orqali foydalanuvchini aniqlash.
    Mavjud bo'lsa parolni tekshiradi, bo'lmasa YANGI hisob deb qabul qiladi.
    """
    def post(self, request):
        phone = request.data.get('phone', '').strip().replace(' ', '')
        email = request.data.get('email', '').strip().lower()
        password = request.data.get('password', '')

        if not phone or not email or not password:
            return Response(
                {'success': False, 'error': 'Telefon, email va parolni to\'liq kiriting!'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Telefon YOKI Email bo'yicha qidiruv
        user = CustomUser.objects.filter(phone=phone).first() or CustomUser.objects.filter(email=email).first()

        if user:
            # Mavjud foydalanuvchi -> Parol tekshiruvi
            if not user.check_password(password):
                return Response({
                    'success': False,
                    'status': 'WRONG_PASSWORD',
                    'error': 'Parol noto\'g\'ri kiritildi!'
                }, status=status.HTTP_401_UNAUTHORIZED)

            if not user.is_active:
                return Response({
                    'success': False,
                    'status': 'BLOCKED',
                    'error': 'Ushbu hisob admin tomonidan chiqarib yuborilgan (bloklangan)!'
                }, status=status.HTTP_403_FORBIDDEN)

            profile_id = None
            if user.role == 'teacher' and hasattr(user, 'teacher_profile'):
                profile_id = user.teacher_profile.id
            elif user.role in ['student', 'parent'] and hasattr(user, 'student_profile'):
                profile_id = user.student_profile.id

            return Response({
                'success': True,
                'status': 'EXISTING_USER',
                'user': UserSerializer(user).data,
                'role': user.role,
                'profile_id': profile_id
            })

        # Umuman topilmadi -> Yangi hisob
        return Response({
            'success': True,
            'status': 'NEW_USER',
            'phone': phone,
            'email': email
        })


class RegisterTeacherView(APIView):
    """
    Yangi Ustoz ro'yxatdan o'tishi.
    Minimal 20 yosh tekshiruvi va bir nechta fan tanlash imkoniyati.
    """
    def post(self, request):
        phone = request.data.get('phone', '').strip().replace(' ', '')
        email = request.data.get('email', '').strip().lower()
        password = request.data.get('password', '')
        full_name = request.data.get('fullName', '').strip()
        birth_date_str = request.data.get('birthDate', '').strip()
        subject_names = request.data.get('subjects', [])

        # Yosh validatsiyasi (>= 20)
        try:
            b_date = datetime.strptime(birth_date_str, "%d.%m.%Y").date()
            today = date.today()
            age = today.year - b_date.year - ((today.month, today.day) < (b_date.month, b_date.day))
            if age < 20:
                return Response({
                    'success': False,
                    'error': f'Ustoz yoshi minimal 20 yosh bo\'lishi shart! Sizning yoshingiz: {age}'
                }, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            return Response({
                'success': False,
                'error': 'Tug\'ilgan sana formati noto\'g\'ri (DD.MM.YYYY bo\'lishi kerak)'
            }, status=status.HTTP_400_BAD_REQUEST)

        if not subject_names:
            return Response({'success': False, 'error': 'Kamida bitta fan tanlang!'}, status=status.HTTP_400_BAD_REQUEST)

        user, _ = CustomUser.objects.get_or_create(
            phone=phone,
            defaults={'username': phone, 'email': email, 'role': 'teacher'}
        )
        user.set_password(password)
        user.save()

        teacher, _ = TeacherProfile.objects.get_or_create(
            user=user,
            defaults={'full_name': full_name, 'birth_date': b_date}
        )

        for s_name in subject_names:
            sub, _ = Subject.objects.get_or_create(name=s_name.strip())
            teacher.subjects.add(sub)

        default_class, _ = ClassRoom.objects.get_or_create(name='7-G')
        teacher.classes.add(default_class)
        teacher.save()

        return Response({
            'success': True,
            'message': 'Ustoz muvaffaqiyatli ro\'yxatdan o\'tdi va Adminga yuborildi.',
            'teacher': TeacherProfileSerializer(teacher).data
        })


class RegisterStudentView(APIView):
    """
    Yangi O'quvchi ro'yxatdan o'tishi.
    Admin Sinflar Arxiviga va tegishli Ustoz arxiviga tushadi.
    """
    def post(self, request):
        student_phone = request.data.get('studentPhone', '').strip().replace(' ', '')
        parent_phone = request.data.get('parentPhone', '').strip().replace(' ', '')
        email = request.data.get('email', '').strip().lower()
        password = request.data.get('password', '')
        full_name = request.data.get('fullName', '').strip()
        birth_date = request.data.get('birthDate', '').strip()
        parent_name = request.data.get('parentName', '').strip()
        grade_class_name = request.data.get('gradeClass', '').strip().upper()

        if not full_name or not grade_class_name or not student_phone:
            return Response({'success': False, 'error': 'Barcha maydonlarni to\'ldiring!'}, status=status.HTTP_400_BAD_REQUEST)

        classroom, _ = ClassRoom.objects.get_or_create(name=grade_class_name)

        student_user, _ = CustomUser.objects.get_or_create(
            phone=student_phone,
            defaults={'username': student_phone, 'email': email, 'role': 'student'}
        )
        student_user.set_password(password)
        student_user.save()

        student_profile, _ = StudentProfile.objects.get_or_create(
            user=student_user,
            defaults={
                'full_name': full_name,
                'birth_date': birth_date,
                'parent_name': parent_name,
                'parent_phone': parent_phone or student_phone,
                'student_phone': student_phone,
                'grade_class': classroom
            }
        )

        if parent_phone and parent_phone != student_phone:
            parent_user, _ = CustomUser.objects.get_or_create(
                phone=parent_phone,
                defaults={'username': parent_phone, 'email': f'parent_{email}', 'role': 'parent'}
            )
            parent_user.set_password(password)
            parent_user.save()

        teachers = TeacherProfile.objects.all()
        for t in teachers:
            if not t.classes.filter(id=classroom.id).exists():
                t.classes.add(classroom)

        return Response({
            'success': True,
            'message': 'O\'quvchi qabul qilindi. Admin va Ustoz sinflar arxiviga qo\'shildi.',
            'student': StudentProfileSerializer(student_profile).data
        })


class TeacherJournalView(APIView):
    def get(self, request):
        class_name = request.query_params.get('class', '7-G')
        subject_name = request.query_params.get('subject', 'Nemis tili A1')

        classroom = ClassRoom.objects.filter(name=class_name).first()
        if not classroom:
            return Response({'students': [], 'attendance': {}, 'grades': {}})

        students = StudentProfile.objects.filter(grade_class=classroom, is_active=True)
        attendances = Attendance.objects.filter(class_room=classroom)
        grades = Grade.objects.filter(student__grade_class=classroom, subject__name=subject_name)

        att_dict = {f"{a.student_id}_{a.date}": a.status for a in attendances}
        grades_dict = {f"{g.student_id}_{g.subject.name}_{g.date}": {'score': g.score, 'comment': g.comment} for g in grades}

        return Response({
            'students': StudentProfileSerializer(students, many=True).data,
            'attendance': att_dict,
            'grades': grades_dict
        })


class SetAttendanceView(APIView):
    def post(self, request):
        student_id = request.data.get('studentId')
        date_str = request.data.get('date')
        status_val = request.data.get('status')

        student = StudentProfile.objects.filter(id=student_id).first()
        if not student:
            return Response({'success': False, 'error': 'O\'quvchi topilmadi'}, status=404)

        if not status_val:
            Attendance.objects.filter(student=student, date=date_str).delete()
            return Response({'success': True, 'action': 'deleted'})

        att, _ = Attendance.objects.update_or_create(
            student=student,
            date=date_str,
            defaults={'class_room': student.grade_class, 'status': status_val}
        )

        notify_parent_attendance(att)
        return Response({'success': True, 'status': status_val})


class SetGradeView(APIView):
    def post(self, request):
        student_id = request.data.get('studentId')
        subject_name = request.data.get('subject', 'Nemis tili A1')
        date_str = request.data.get('date')
        score = int(request.data.get('score', 5))
        comment = request.data.get('comment', '')

        student = StudentProfile.objects.filter(id=student_id).first()
        subject, _ = Subject.objects.get_or_create(name=subject_name)

        grade, _ = Grade.objects.update_or_create(
            student=student,
            subject=subject,
            date=date_str,
            defaults={'score': score, 'comment': comment}
        )

        notify_parent_grade(grade)
        return Response({'success': True, 'score': score, 'comment': comment})


class StudentDashboardView(APIView):
    def get(self, request, student_id):
        student = StudentProfile.objects.filter(id=student_id).first()
        if not student:
            return Response({'error': 'O\'quvchi topilmadi'}, status=404)

        grades = Grade.objects.filter(student=student).order_by('date')
        attendances = Attendance.objects.filter(student=student).order_by('date')

        present_count = attendances.filter(status='present').count()
        absent_count = attendances.filter(status='absent').count()
        sick_count = attendances.filter(status='sick').count()
        total_days = present_count + absent_count + sick_count
        rate = round((present_count / total_days * 100)) if total_days > 0 else 100

        return Response({
            'student': StudentProfileSerializer(student).data,
            'grades': GradeSerializer(grades, many=True).data,
            'attendance': AttendanceSerializer(attendances, many=True).data,
            'stats': {
                'totalDays': total_days,
                'presentCount': present_count,
                'absentCount': absent_count,
                'sickCount': sick_count,
                'rate': rate
            }
        })


class ExpelUserView(APIView):
    def post(self, request):
        user_id = request.data.get('userId')
        user = CustomUser.objects.filter(id=user_id).first()
        if user:
            user.is_active = False
            user.save()
            return Response({'success': True, 'message': 'Foydalanuvchi chiqarib yuborildi.'})
        return Response({'success': False, 'error': 'Foydalanuvchi topilmadi.'}, status=404)


class TelegramWebhookView(APIView):
    """
    Vercel uchun 24/7 Telegram Bot Webhook.
    Telegramdan kelgan yangilanishlarni qabul qiladi va to'g'ridan-to'g'ri javob beradi.
    """
    def post(self, request):
        try:
            update = request.data
            if "message" not in update:
                return Response({'ok': True})

            msg = update["message"]
            chat_id = msg["chat"]["id"]
            text = msg.get("text", "").strip()

            state = TG_USER_STATES.get(chat_id, {"step": "START"})

            if text == "/start" or state["step"] == "START":
                TG_USER_STATES[chat_id] = {"step": "WAITING_ID"}
                welcome_text = (
                    "🇩🇪 <b>Deutschsmart Student Botiga xush kelibsiz!</b>\n\n"
                    "O'quvchi haqida ma'lumot (davomat va baholar)ni olish uchun, iltimos:\n"
                    "O'quvchining <b>Telefon raqami</b>, <b>Emaili</b> yoki <b>Ism-familiyasini</b> kiriting:\n\n"
                    "<i>(Masalan: +998931112233 yoki Jasur Karimov)</i>"
                )
                send_telegram_message(chat_id, welcome_text)
                return Response({'ok': True})

            # 1-QADAM: Identifikator qabul qilindi -> Parol so'raymiz
            if state["step"] == "WAITING_ID":
                TG_USER_STATES[chat_id] = {
                    "step": "WAITING_PASSWORD",
                    "identifier": text
                }
                send_telegram_message(chat_id, f"✅ <b>Kiritildi:</b> {text}\n\n🔐 Endi hisob <b>parolini</b> kiriting:")
                return Response({'ok': True})

            # 2-QADAM: Parol qabul qilindi -> Tekshiramiz
            if state["step"] == "WAITING_PASSWORD":
                identifier_raw = state.get("identifier", "").strip()
                identifier_clean = identifier_raw.replace(" ", "").replace("+", "").lower()
                password = text

                student = None
                # DB dan qidirish
                students = StudentProfile.objects.filter(is_active=True)
                for st in students:
                    p1 = st.student_phone.replace(" ", "").replace("+", "").lower()
                    p2 = st.parent_phone.replace(" ", "").replace("+", "").lower()
                    em = (st.user.email or "").lower()
                    nm = st.full_name.lower()

                    if identifier_clean in [p1, p2] or identifier_raw.lower() in [em, nm]:
                        if st.user.check_password(password):
                            student = st
                            break

                if student:
                    attendances = Attendance.objects.filter(student=student)
                    present = attendances.filter(status='present').count()
                    absent = attendances.filter(status='absent').count()
                    sick = attendances.filter(status='sick').count()
                    total = present + absent + sick
                    rate = round((present / total * 100)) if total > 0 else 100

                    grades = Grade.objects.filter(student=student)
                    grades_by_sub = {}
                    for g in grades:
                        sub = g.subject.name
                        if sub not in grades_by_sub:
                            grades_by_sub[sub] = []
                        grades_by_sub[sub].append(g.score)

                    grades_text = ""
                    for sub, scores in grades_by_sub.items():
                        avg = round(sum(scores) / len(scores), 1)
                        grades_text += f"• <b>{sub}:</b> {', '.join(map(str, scores))} <i>(O'rtacha: {avg})</i>\n"

                    response_text = (
                        f"🎓 <b>O'quvchi ma'lumotlari:</b>\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"👤 <b>F.I.SH:</b> {student.full_name}\n"
                        f"🏫 <b>Sinf:</b> {student.grade_class.name}\n"
                        f"👨‍👩‍👧 <b>Ota-onasi:</b> {student.parent_name}\n"
                        f"📞 <b>Telefon:</b> {student.student_phone}\n\n"
                        f"📊 <b>Davomat holati:</b>\n"
                        f"🟢 Bor: <b>{present} kun</b>\n"
                        f"🔴 Dars qoldirgan: <b>{absent} kun</b>\n"
                        f"🟡 Kasallik: <b>{sick} kun</b>\n"
                        f"📈 Umumiy davomat ko'rsatkichi: <b>{rate}%</b>\n\n"
                        f"⭐️ <b>Kundalik baholari:</b>\n"
                        f"{grades_text or 'Hali baholar mavjud emas.'}\n"
                        f"━━━━━━━━━━━━━━━━━━━━\n"
                        f"🔄 Boshqa o'quvchini qidirish uchun /start ni bosing."
                    )
                    send_telegram_message(chat_id, response_text)
                    TG_USER_STATES[chat_id] = {"step": "START"}
                else:
                    send_telegram_message(chat_id, "❌ <b>Bu bola maktabdan emas</b>\n\nKiritilgan ma'lumotlar bo'yicha bola topilmadi yoki parol noto'g'ri!\nQaytadan urinish uchun /start ni bosing.")
                    TG_USER_STATES[chat_id] = {"step": "START"}

            return Response({'ok': True})
        except Exception as e:
            logger.error(f"Telegram Webhook xatosi: {e}")
            return Response({'ok': False, 'error': str(e)}, status=500)
