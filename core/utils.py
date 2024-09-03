from django.contrib.auth import get_user_model
from .models import Notification, Course


def notify_teacher_on_enrollment(student, course):
    # Notify the teacher of the course that a student has enrolled
    content = f"{student.username} has enrolled in your course: {course.title}."
    Notification.objects.create(user=course.teacher, content=content)


def notify_student_on_new_material(student, course, material):
    # Notify the student that new material has been added to the course
    content = f"New material '{material.title}' has been added to the course: {course.title}."
    Notification.objects.create(user=student, content=content)


def notify_all_students(message):
    """
    Sends a notification to all students in the system.
    """
    # Get the CustomUser model
    CustomUser = get_user_model()

    # Filter all students
    students = CustomUser.objects.filter(is_student=True)

    # Create a notification for each student
    for student in students:
        Notification.objects.create(user=student, content=message)