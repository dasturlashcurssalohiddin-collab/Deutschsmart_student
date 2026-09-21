from django.urls import path
from .views import (
    CheckUserView, RegisterTeacherView, RegisterStudentView,
    TeacherJournalView, SetAttendanceView, SetGradeView,
    StudentDashboardView, ExpelUserView, TelegramWebhookView
)

urlpatterns = [
    path('auth/check/', CheckUserView.as_view(), name='api-check-user'),
    path('auth/register-teacher/', RegisterTeacherView.as_view(), name='api-register-teacher'),
    path('auth/register-student/', RegisterStudentView.as_view(), name='api-register-student'),
    path('teacher/journal/', TeacherJournalView.as_view(), name='api-teacher-journal'),
    path('teacher/attendance/', SetAttendanceView.as_view(), name='api-set-attendance'),
    path('teacher/grade/', SetGradeView.as_view(), name='api-set-grade'),
    path('student/dashboard/<int:student_id>/', StudentDashboardView.as_view(), name='api-student-dashboard'),
    path('admin/expel/', ExpelUserView.as_view(), name='api-expel-user'),
    # 24/7 Vercel Telegram Webhook
    path('telegram/webhook/', TelegramWebhookView.as_view(), name='api-telegram-webhook'),
]
