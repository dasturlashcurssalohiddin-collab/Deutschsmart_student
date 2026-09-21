from django.contrib import admin
from django.utils.html import format_html
from .models import CustomUser, Subject, ClassRoom, TeacherProfile, StudentProfile, Attendance, Grade, TelegramSubscriber

admin.site.site_header = "Deutschsmart Student — Elektron Maktab Boshqaruvi"
admin.site.site_title = "Deutschsmart Admin"
admin.site.index_title = "Elektron Kundalik va Boshqaruv Tizimi"


# 1. CustomUser Admin
@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('phone', 'email', 'role', 'status_badge', 'date_joined')
    list_filter = ('role', 'is_active', 'date_joined')
    search_fields = ('phone', 'email', 'username')
    actions = ['expel_users', 'activate_users']

    def status_badge(self, obj):
        if obj.is_active:
            return format_html('<span style="color:green; font-weight:bold;">Faol</span>')
        return format_html('<span style="color:red; font-weight:bold;">Chiqarib yuborilgan (Bloklangan)</span>')
    status_badge.short_description = "Holati"

    @admin.action(description="🚫 Tanlanganlarni chiqarib yuborish (Faolsizlantirish)")
    def expel_users(self, request, queryset):
        count = queryset.update(is_active=False)
        self.message_user(request, f"{count} ta foydalanuvchi muvaffaqiyatli chiqarib yuborildi.")

    @admin.action(description="✅ Tanlanganlarni qayta faollashtirish")
    def activate_users(self, request, queryset):
        count = queryset.update(is_active=True)
        self.message_user(request, f"{count} ta foydalanuvchi qayta faollashtirildi.")


# 2. Sinflar Arxivi va O'quvchilar Profili Admin
@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'grade_class', 'birth_date', 'parent_name', 'parent_phone', 'student_phone', 'status_badge', 'created_at')
    list_filter = ('grade_class', 'is_active', 'is_approved', 'created_at')
    search_fields = ('full_name', 'parent_name', 'parent_phone', 'student_phone')
    actions = ['expel_student', 'restore_student']

    def status_badge(self, obj):
        if obj.is_active and obj.user.is_active:
            return format_html('<span style="background:#dcfce7; color:#15803d; padding:3px 8px; border-radius:4px; font-weight:bold;">Sinfda o\'qiydi</span>')
        return format_html('<span style="background:#fee2e2; color:#b91c1c; padding:3px 8px; border-radius:4px; font-weight:bold;">Chiqarib yuborilgan</span>')
    status_badge.short_description = "Arxivdagi holati"

    @admin.action(description="🚫 O'quvchini maktabdan chiqarib yuborish (Expel)")
    def expel_student(self, request, queryset):
        for student in queryset:
            student.is_active = False
            student.save()
            # Bog'langan user hisobini ham bloklash
            student.user.is_active = False
            student.user.save()
        self.message_user(request, f"{queryset.count()} ta o'quvchi chiqarib yuborildi.")

    @admin.action(description="✅ O'quvchini qayta tiklash")
    def restore_student(self, request, queryset):
        for student in queryset:
            student.is_active = True
            student.save()
            student.user.is_active = True
            student.user.save()
        self.message_user(request, f"{queryset.count()} ta o'quvchi tiklandi.")


# 3. Ustozlar Admin
@admin.register(TeacherProfile)
class TeacherProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'birth_date', 'get_subjects', 'get_classes', 'status_badge', 'created_at')
    list_filter = ('is_approved', 'created_at')
    search_fields = ('full_name', 'user__phone', 'user__email')
    actions = ['expel_teacher', 'restore_teacher']

    def get_subjects(self, obj):
        return ", ".join([s.name for s in obj.subjects.all()])
    get_subjects.short_description = "Fanlari"

    def get_classes(self, obj):
        return ", ".join([c.name for c in obj.classes.all()]) or "Biriktirilmagan"
    get_classes.short_description = "Biriktirilgan Sinflar"

    def status_badge(self, obj):
        if obj.user.is_active:
            return format_html('<span style="color:green; font-weight:bold;">Faol Ustoz</span>')
        return format_html('<span style="color:red; font-weight:bold;">Chiqarib yuborilgan</span>')
    status_badge.short_description = "Holati"

    @admin.action(description="🚫 Ustozni chiqarib yuborish (Ishdan bo'shatish/Bloklash)")
    def expel_teacher(self, request, queryset):
        for teacher in queryset:
            teacher.user.is_active = False
            teacher.user.save()
        self.message_user(request, f"{queryset.count()} ta ustoz chiqarib yuborildi.")

    @admin.action(description="✅ Ustozni qayta faollashtirish")
    def restore_teacher(self, request, queryset):
        for teacher in queryset:
            teacher.user.is_active = True
            teacher.user.save()
        self.message_user(request, f"{queryset.count()} ta ustoz qayta faollashtirildi.")


# 4. Sinflar
@admin.register(ClassRoom)
class ClassRoomAdmin(admin.ModelAdmin):
    list_display = ('name', 'academic_year', 'student_count')
    search_fields = ('name',)

    def student_count(self, obj):
        return obj.students.filter(is_active=True).count()
    student_count.short_description = "Faol o'quvchilar soni"


# 5. Fanlar
@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


# 6. Davomat Admin
@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('date', 'class_room', 'student', 'status_badge', 'teacher')
    list_filter = ('class_room', 'status', 'date')
    search_fields = ('student__full_name',)

    def status_badge(self, obj):
        colors = {
            'present': '#16a34a',
            'absent': '#dc2626',
            'sick': '#d97706'
        }
        return format_html(
            f'<span style="color:{colors.get(obj.status, "black")}; font-weight:bold;">{obj.get_status_display()}</span>'
        )
    status_badge.short_description = "Davomat"


# 7. Baholar Admin (Kundalik.com)
@admin.register(Grade)
class GradeAdmin(admin.ModelAdmin):
    list_display = ('date', 'student', 'subject', 'score_badge', 'comment', 'teacher')
    list_filter = ('subject', 'score', 'date')
    search_fields = ('student__full_name', 'comment')

    def score_badge(self, obj):
        return format_html(
            f'<span style="background:#e0e7ff; color:#1e3a8a; padding:4px 10px; border-radius:6px; font-weight:bold; font-size:1.1rem;">{obj.score}</span>'
        )
    score_badge.short_description = "Baho"


# 8. Telegram Obunachilari
@admin.register(TelegramSubscriber)
class TelegramSubscriberAdmin(admin.ModelAdmin):
    list_display = ('chat_id', 'phone', 'role', 'student', 'is_active', 'created_at')
    search_fields = ('chat_id', 'phone', 'student__full_name')
