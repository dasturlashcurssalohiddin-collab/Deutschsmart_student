from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from datetime import date

class CustomUser(AbstractUser):
    ROLE_CHOICES = (
        ('teacher', 'Ustoz (O\'qituvchi)'),
        ('student', 'O\'quvchi'),
        ('parent', 'Ota-ona'),
        ('admin', 'Administrator'),
    )
    
    phone = models.CharField(max_length=20, unique=True, verbose_name="Telefon raqam")
    email = models.EmailField(blank=True, null=True, verbose_name="Email")
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student', verbose_name="Rol")
    is_active = models.BooleanField(default=True, verbose_name="Faollik holati (Chiqarib yuborish uchun o'chiring)")

    # Django username sifatida telefon raqam yoki email ishlatish
    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return f"{self.phone} ({self.get_role_display()})"


class Subject(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Fan nomi")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Fan"
        verbose_name_plural = "Fanlar"


class ClassRoom(models.Model):
    name = models.CharField(max_length=20, unique=True, verbose_name="Sinf nomi (Masalan: 7-G)")
    academic_year = models.CharField(max_length=20, default="2026-2027", verbose_name="O'quv yili")

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Sinf"
        verbose_name_plural = "Sinflar"


class TeacherProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='teacher_profile')
    full_name = models.CharField(max_length=150, verbose_name="Ustoz F.I.SH")
    birth_date = models.DateField(verbose_name="Tug'ilgan sana")
    subjects = models.ManyToManyField(Subject, related_name='teachers', verbose_name="O'tadigan fanlari")
    classes = models.ManyToManyField(ClassRoom, related_name='teachers', blank=True, verbose_name="Biriktirilgan sinflar")
    is_approved = models.BooleanField(default=True, verbose_name="Admin tomonidan tasdiqlangan")
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        # Minimal 20 yosh bo'lishini tekshirish
        if self.birth_date:
            today = date.today()
            age = today.year - self.birth_date.year - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
            if age < 20:
                raise ValidationError("Ustoz yoshi minimal 20 yosh bo'lishi shart!")

    def __str__(self):
        return f"Ustoz: {self.full_name}"

    class Meta:
        verbose_name = "Ustoz Profili"
        verbose_name_plural = "Ustozlar Profillari"


class StudentProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='student_profile')
    full_name = models.CharField(max_length=150, verbose_name="O'quvchi F.I.SH")
    birth_date = models.CharField(max_length=50, verbose_name="Tug'ilgan sana / Yoshi")
    parent_name = models.CharField(max_length=150, verbose_name="Ota-onasi F.I.SH")
    parent_phone = models.CharField(max_length=20, verbose_name="Ota-ona telefon raqami")
    student_phone = models.CharField(max_length=20, verbose_name="O'quvchi telefon raqami")
    grade_class = models.ForeignKey(ClassRoom, on_delete=models.CASCADE, related_name='students', verbose_name="Sinfi")
    is_approved = models.BooleanField(default=True, verbose_name="Tasdiqlangan")
    is_active = models.BooleanField(default=True, verbose_name="Sinfda o'qiyaptimi (Faol)")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ro'yxatdan o'tgan vaqt")

    def __str__(self):
        return f"{self.full_name} ({self.grade_class.name})"

    class Meta:
        verbose_name = "O'quvchi Profili"
        verbose_name_plural = "O'quvchilar Profillari (Sinflar Arxivi)"


class Attendance(models.Model):
    STATUS_CHOICES = (
        ('present', 'Bor (Kelgan)'),
        ('absent', 'Yo\'q (Sababsiz)'),
        ('sick', 'Kasal (Sababli)'),
    )

    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='attendances', verbose_name="O'quvchi")
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Belgilagan ustoz")
    class_room = models.ForeignKey(ClassRoom, on_delete=models.CASCADE, verbose_name="Sinf")
    date = models.DateField(verbose_name="Sana")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, verbose_name="Davomat holati")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('student', 'date')
        verbose_name = "Davomat Yozuvi"
        verbose_name_plural = "Davomat Yozuvlari"

    def __str__(self):
        return f"{self.student.full_name} - {self.date}: {self.get_status_display()}"


class Grade(models.Model):
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='grades', verbose_name="O'quvchi")
    teacher = models.ForeignKey(TeacherProfile, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="Baho qo'ygan ustoz")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, verbose_name="Fan")
    date = models.DateField(verbose_name="Sana")
    score = models.IntegerField(verbose_name="Baho (1 dan 5 gacha)")
    comment = models.TextField(blank=True, null=True, verbose_name="Izoh / Uy vazifasi")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Baho Yozuvi"
        verbose_name_plural = "Baholar (Kundalik.com)"

    def __str__(self):
        return f"{self.student.full_name} | {self.subject.name} | Baho: {self.score} ({self.date})"


class TelegramSubscriber(models.Model):
    chat_id = models.BigIntegerField(unique=True, verbose_name="Telegram Chat ID")
    phone = models.CharField(max_length=20, verbose_name="Bog'langan telefon raqam")
    role = models.CharField(max_length=20, default='parent', verbose_name="Rol")
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, null=True, blank=True, related_name='telegram_subscribers')
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"TG: {self.chat_id} ({self.phone})"

    class Meta:
        verbose_name = "Telegram Obunachi"
        verbose_name_plural = "Telegram Obunachilar"
