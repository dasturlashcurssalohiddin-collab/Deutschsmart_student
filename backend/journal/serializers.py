from rest_framework import serializers
from .models import CustomUser, Subject, ClassRoom, TeacherProfile, StudentProfile, Attendance, Grade

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'phone', 'email', 'role', 'is_active']


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ['id', 'name']


class ClassRoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = ClassRoom
        fields = ['id', 'name', 'academic_year']


class TeacherProfileSerializer(serializers.ModelSerializer):
    subjects = SubjectSerializer(many=True, read_only=True)
    classes = ClassRoomSerializer(many=True, read_only=True)

    class Meta:
        model = TeacherProfile
        fields = ['id', 'full_name', 'birth_date', 'subjects', 'classes', 'is_approved']


class StudentProfileSerializer(serializers.ModelSerializer):
    grade_class_name = serializers.CharField(source='grade_class.name', read_only=True)

    class Meta:
        model = StudentProfile
        fields = [
            'id', 'full_name', 'birth_date', 'parent_name', 
            'parent_phone', 'student_phone', 'grade_class', 
            'grade_class_name', 'is_active', 'is_approved'
        ]


class AttendanceSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)

    class Meta:
        model = Attendance
        fields = ['id', 'student', 'student_name', 'class_room', 'date', 'status']


class GradeSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student.full_name', read_only=True)
    subject_name = serializers.CharField(source='subject.name', read_only=True)

    class Meta:
        model = Grade
        fields = ['id', 'student', 'student_name', 'subject', 'subject_name', 'date', 'score', 'comment']
