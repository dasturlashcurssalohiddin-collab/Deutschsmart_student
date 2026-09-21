"""
Deutschsmart Student - Django Admin Panel & Modellar To'plami

Foydalanish:
Ushbu kodni Django loyihangizdagi `admin.py` va `models.py` ga qo'shasiz.
Undagi asosiy imkoniyatlar:
1. Ustozni yoki O'quvchini chiqarib yuborish (Kick / Expel / Deactivate).
2. Sinflar arxivi (Har bir sinf kesimida o'quvchilar, ota-onalari va telefonlari).
3. Davomat (Bor / Yo'q / Kasal) va Kundalik baholarini nazorat qilish.
4. Firebase bilan sinxronizatsiya qilish (ixtiyoriy Firebase Admin SDK).
"""

from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib import admin
from django.utils.html import format_html
from django.core.exceptions import ValidationError
from datetime import date

# ==========================================
# 1. DJANGO MODELLARI (models.py uchun)
# ==========================================

class User(AbstractUser):
    ROLE_CHOICES = (
        ('teacher', 'Ustoz'),
        ('student', 'O\'quvchi'),
        ('parent', 'Ota-ona'),
        ('admin', 'Admin'),
    )
    phone = models.CharField(max_length=20, unique=True, verbose_name="Telefon")
    email = models.EmailField(blank=True, null=True, verbose_name="Email")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    is_active = models.BooleanField(default=True, verbose_name="Faollik (Chiqarib yuborilgan bo'lsa False bo'ladi)")

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = "Foydalanuvchi"
        verbose_name_plural = "Foydalanuvchilar"


class ClassRoom(models.Model):
    name = models.CharField(max_length=20, unique=True, verbose_name="Sinf (Masalan: 7-G)")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Sinf"
        verbose_name_plural = "Sinflar"


class Subject(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Fan nomi")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Fan"
        verbose_name_plural = "Fanlar"


class TeacherProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    full_name = models.CharField(max_length=150, verbose_name="Ustoz F.I.SH")
    birth_date = models.DateField(verbose_name="Tug'ilgan sana")
    subjects = models.ManyToManyField(Subject, verbose_name="O'tadigan fanlari")
    classes = models.ManyToManyField(ClassRoom, blank=True, verbose_name="Sinflari")

    def clean(self):
        # Minimal 20 yosh tekshiruvi
        if self.birth_date:
            today = date.today()
            age = today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
            if age < 20:
                raise ValidationError("Ustoz yoshi kamida 20 yosh bo'lishi shart!")

    def __str__(self):
        return self.full_name

    class Meta:
        verbose_name = "Ustoz Profili"
        verbose_name_plural = "Ustozlar"


class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    full_name = models.CharField(max_length=150, verbose_name="O'quvchi F.I.SH")
    birth_date = models.CharField(max_length=50, verbose_name="Tug'ilgan sana / Yoshi")
    parent_name = models.CharField(max_length=150, verbose_name="Ota-onasi F.I.SH")
    parent_phone = models.CharField(max_length=20, verbose_name="Ota-ona telefoni")
    student_phone = models.CharField(max_length=20, verbose_name="O'quvchi telefoni")
    grade_class = models.ForeignKey(ClassRoom, on_delete=models.CASCADE, related_name='students', verbose_name="Sinfi")
    is_active = models.BooleanField(default=True, verbose_name="Sinfda faolmi")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} ({self.grade_class.name})"

    class Meta:
        verbose_name = "O'quvchi (Sinflar Arxivi)"
        verbose_name_plural = "O'quvchilar (Sinflar Arxivi)"


class Attendance(models.Model):
    STATUS_CHOICES = (
        ('present', 'Bor'),
        ('absent', 'Yo\'q'),
        ('sick', 'Kasal'),
    )
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField(verbose_name="Sana")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, verbose_name="Davomat")

    class Meta:
        unique_together = ('student', 'date')
        verbose_name = "Davomat"
        verbose_name_plural = "Davomatlar"


class Grade(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='grades')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    date = models.DateField(verbose_name="Sana")
    score = models.IntegerField(verbose_name="Baho (1-5)")
    comment = models.TextField(blank=True, null=True, verbose_name="Ustoz izohi")

    class Meta:
        verbose_name = "Baho"
        verbose_name_plural = "Baholar (Kundalik)"


# ==========================================
# 2. DJANGO ADMIN SOZLAMALARI (admin.py uchun)
# ==========================================

admin.site.site_header = "Deutschsmart Student — Admin Paneli"
admin.site.site_title = "Deutschsmart Admin"
admin.site.index_title = "Elektron Kundalik va Maktab Boshqaruvi"


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'grade_class', 'parent_name', 'parent_phone', 'student_phone', 'status_badge', 'created_at')
    list_filter = ('grade_class', 'is_active', 'created_at')
    search_fields = ('full_name', 'parent_name', 'parent_phone', 'student_phone')
    actions = ['expel_student', 'restore_student']

    def status_badge(self, obj):
        if obj.is_active and obj.user.is_active:
            return format_html('<span style="background:#dcfce7; color:#15803d; padding:3px 8px; border-radius:4px; font-weight:bold;">Sinfda o\'qiydi</span>')
        return format_html('<span style="background:#fee2e2; color:#b91c1c; padding:3px 8px; border-radius:4px; font-weight:bold;">Chiqarib yuborilgan</span>')
    status_badge.short_description = "Holati"

    # TALAB: Admin panelda o'quvchini chiqarib yuborish imkoni
    @admin.action(description="🚫 Tanlangan o'quvchilarni chiqarib yuborish (Expel / Bloklash)")
    def expel_student(self, request, queryset):
        for st in queryset:
            st.is_active = False
            st.save()
            st.user.is_active = False
            st.user.save()
        self.message_user(request, f"{queryset.count()} ta o'quvchi maktabdan chiqarib yuborildi.")

    @admin.action(description="✅ O'quvchini qayta tiklash")
    def restore_student(self, request, queryset):
        for st in queryset:
            st.is_active = True
            st.save()
            st.user.is_active = True
            st.user.save()
        self.message_user(request, f"{queryset.count()} ta o'quvchi tiklandi.")


@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'birth_date', 'get_subjects', 'status_badge')
    search_fields = ('full_name', 'user__phone')
    actions = ['expel_teacher', 'restore_teacher']

    def get_subjects(self, obj):
        return ", ".join([s.name for s in obj.subjects.all()])
    get_subjects.short_description = "Fanlari"

    def status_badge(self, obj):
        if obj.user.is_active:
            return format_html('<span style="color:green; font-weight:bold;">Faol Ustoz</span>')
        return format_html('<span style="color:red; font-weight:bold;">Chiqarib yuborilgan</span>')
    status_badge.short_description = "Holati"

    # TALAB: Admin panelda ustozni chiqarib yuborish imkoni
    @admin.action(description="🚫 Tanlangan ustozlarni chiqarib yuborish (Bloklash)")
    def expel_teacher(self, request, queryset):
        for t in queryset:
            t.user.is_active = False
            t.user.save()
        self.message_user(request, f"{queryset.count()} ta ustoz chiqarib yuborildi.")

    @admin.action(description="✅ Ustozni qayta tiklash")
    def restore_teacher(self, request, queryset):
        for t in queryset:
            t.user.is_active = True
            t.user.save()
        self.message_user(request, f"{queryset.count()} ta ustoz qayta faollashtirildi.")


@admin.register(ClassRoom)
class ClassRoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'student_count')
    def student_count(self, obj):
        return obj.students.filter(is_active=True).count()
    student_count.short_description = "Faol o'quvchilar soni"


@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('date', 'student', 'status')
    list_filter = ('status', 'date')


@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ('date', 'student', 'subject', 'score', 'comment')
    list_filter = ('subject', 'score', 'date')
