from rest_framework import serializers
from .models import CustomUser, Course, Enrollment, Feedback, StatusUpdate

# Custom User Serializer
class CustomUserSerializer(serializers.ModelSerializer):
    """
    Serializer for CustomUser model to handle user data in the API.
    """
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_student', 'is_teacher', 'bio', 'profile_photo']
        read_only_fields = ['id', 'is_student', 'is_teacher']  # Prevents changes to these fields via the API


# Course Serializer
class CourseSerializer(serializers.ModelSerializer):
    """
    Serializer for Course model to handle course data in the API.
    Includes nested serializer to provide detailed teacher information.
    """
    teacher = CustomUserSerializer(read_only=True)  # Nested serializer for teacher details

    class Meta:
        model = Course
        fields = ['id', 'title', 'description', 'teacher']
        read_only_fields = ['id', 'teacher']  # Ensures teacher is set automatically based on the authenticated user


# Enrollment Serializer
class EnrollmentSerializer(serializers.ModelSerializer):
    """
    Serializer for Enrollment model to handle enrollment data in the API.
    Includes nested serializers to provide detailed student and course information.
    """
    student = CustomUserSerializer(read_only=True)  # Nested serializer for student details
    course = CourseSerializer(read_only=True)  # Nested serializer for course details

    class Meta:
        model = Enrollment
        fields = ['id', 'student', 'course', 'enrolled_on']
        read_only_fields = ['id', 'student', 'enrolled_on']  # Prevents changes to these fields via the API


# Feedback Serializer
class FeedbackSerializer(serializers.ModelSerializer):
    """
    Serializer for Feedback model to handle feedback data in the API.
    Includes nested serializers to provide detailed course and student information.
    """
    course = CourseSerializer(read_only=True)  # Nested serializer for course details
    student = CustomUserSerializer(read_only=True)  # Nested serializer for student details

    class Meta:
        model = Feedback
        fields = ['id', 'course', 'student', 'content', 'created_at']
        read_only_fields = ['id', 'course', 'student', 'created_at']  # Prevents changes to these fields via the API


# Status Update Serializer
class StatusUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for StatusUpdate model to handle status update data in the API.
    Includes a nested serializer to provide detailed user information.
    """
    user = CustomUserSerializer(read_only=True)  # Nested serializer for user details

    class Meta:
        model = StatusUpdate
        fields = ['id', 'user', 'content', 'timestamp']
        read_only_fields = ['id', 'user', 'timestamp']  # Ensures the user and timestamp are read-only
