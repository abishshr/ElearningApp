from django.contrib import messages
from django.contrib.auth import login, get_user_model
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, redirect, get_object_or_404
from rest_framework import status, viewsets, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

# Import forms, models, and serializers
from .forms import CourseForm, CustomUserCreationForm, FeedbackForm, UserProfileForm, MaterialForm, StatusUpdateForm
from .models import Course, Enrollment, StatusUpdate, CustomUser, Feedback, ChatRoom, Material, Notification
from .serializers import CustomUserSerializer, CourseSerializer, EnrollmentSerializer, FeedbackSerializer, StatusUpdateSerializer
from .utils import notify_teacher_on_enrollment, notify_student_on_new_material, notify_all_students

import logging

# Create a logger instance
logger = logging.getLogger(__name__)

# ---------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------

def handle_feedback_submission(request, course):
    """
    Helper function to handle feedback submission.
    """
    form = FeedbackForm(request.POST)
    if form.is_valid():
        feedback = form.save(commit=False)
        feedback.course = course
        feedback.student = request.user
        feedback.save()
        messages.success(request, "Your feedback has been submitted.")
        return True
    return False

# ---------------------------------------------------------
# User Registration and Authentication Views
# ---------------------------------------------------------

@api_view(['GET', 'POST'])
def register(request):
    """
    Handles user registration. Allows creation of new accounts.
    """
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('home')
        else:
            return Response({"form_errors": form.errors}, status=status.HTTP_400_BAD_REQUEST)
    else:
        form = CustomUserCreationForm()
        return render(request, 'register.html', {'form': form})

# ---------------------------------------------------------
# Home View for Users
# ---------------------------------------------------------

class HomeView(LoginRequiredMixin, APIView):
    """
    Displays the home page for users, including relevant data like courses,
    status updates, and students (if user is a teacher).
    """
    permission_classes = [IsAuthenticated]
    login_url = '/accounts/login/'

    def get(self, request):
        if not isinstance(request.user, CustomUser):
            return render(request, 'error.html', {"message": "User is not an instance of CustomUser."})

        # Fetch user-specific data
        user_courses = Enrollment.objects.filter(student=request.user)
        status_updates = StatusUpdate.objects.filter(user=request.user).order_by('-timestamp')
        created_courses = Course.objects.filter(teacher=request.user) if request.user.is_teacher else []
        students = None  # Initialize students as None

        # If user is a teacher and search query is present, fetch student data
        if request.user.is_teacher and 'q' in request.GET:
            query = request.GET.get('q', '')
            students = CustomUser.objects.filter(is_student=True)
            if query:
                students = students.filter(
                    username__icontains=query
                ) | students.filter(
                    first_name__icontains=query
                ) | students.filter(
                    last_name__icontains=query
                )

        # Fetch unread notifications
        notification_count = request.user.notifications.filter(read=False).count()
        unread_notifications = request.user.notifications.filter(read=False)

        return render(request, 'home.html', {
            'courses': user_courses,
            'status_updates': status_updates,
            'created_courses': created_courses,
            'students': students,
            'notification_count': notification_count,
            'unread_notifications': unread_notifications,
        })
    def post(self, request):
        # Handle posting a status update
        status_update_form = StatusUpdateForm(request.POST)
        if status_update_form.is_valid():
            status_update = status_update_form.save(commit=False)
            status_update.user = request.user
            status_update.save()
            return redirect('home')  # Redirect to home after posting a status update

        # If form is invalid, render the home page with the existing form data
        return self.get(request)

# ---------------------------------------------------------
# API Views using Django REST Framework
# ---------------------------------------------------------

class CustomUserViewSet(viewsets.ModelViewSet):
    """
    API view for managing users.
    """
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [permissions.IsAuthenticated]

class CourseViewSet(viewsets.ModelViewSet):
    """
    API view for managing courses.
    """
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(teacher=self.request.user)

class EnrollmentViewSet(viewsets.ModelViewSet):
    """
    API view for managing enrollments.
    """
    queryset = Enrollment.objects.all()
    serializer_class = EnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(student=self.request.user)

class FeedbackViewSet(viewsets.ModelViewSet):
    """
    API view for managing feedbacks.
    """
    queryset = Feedback.objects.all()
    serializer_class = FeedbackSerializer
    permission_classes = [permissions.IsAuthenticated]

class StatusUpdateViewSet(viewsets.ModelViewSet):
    """
    API view for managing status updates.
    """
    queryset = StatusUpdate.objects.all()
    serializer_class = StatusUpdateSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

# ---------------------------------------------------------
# Course Management Views
# ---------------------------------------------------------

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def create_course(request):
    """
    View to create a new course. Only accessible to teachers.
    """
    if not request.user.is_teacher:
        messages.error(request, "Only teachers can create courses.")
        return redirect('home')

    if request.method == 'GET':
        form = CourseForm()
        return render(request, 'create_course.html', {'form': form})

    elif request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            course = form.save(commit=False)
            course.teacher = request.user
            course.save()

            # Notify all students about the new course
            notify_all_students(
                f"A new course '{course.title}' has been created by {request.user.username}. Enroll now!"
            )

            messages.success(request, "Course created successfully and all students have been notified.")
            return redirect('course_detail', course_id=course.id)
        else:
            messages.error(request, "There was an error creating the course.")
            return render(request, 'create_course.html', {'form': form})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def course_list(request):
    """
    Lists all available courses.
    """
    courses = Course.objects.all()
    return render(request, 'course_list.html', {'courses': courses})

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def course_detail(request, course_id):
    """
    Displays details of a specific course.
    """
    course = get_object_or_404(Course, id=course_id)
    feedbacks = Feedback.objects.filter(course=course).order_by('-created_at')
    materials = Material.objects.filter(course=course).order_by('-created_at')  # Fetch materials

    # Check if the user is a student
    is_student = getattr(request.user, 'is_student', False)
    # Check if the user is enrolled in the course
    is_enrolled = Enrollment.objects.filter(student=request.user, course=course).exists()
    feedback_form = FeedbackForm() if is_enrolled else None  # Show feedback form only if enrolled

    # Fetch unread notifications for this user
    user_notifications = Notification.objects.filter(user=request.user, read=False)

    if request.method == 'POST':
        if is_student:
            if 'submit_feedback' in request.POST and is_enrolled:
                feedback_form = FeedbackForm(request.POST)
                if feedback_form.is_valid():
                    feedback = feedback_form.save(commit=False)
                    feedback.course = course
                    feedback.student = request.user
                    feedback.save()
                    messages.success(request, "Your feedback has been submitted.")
                    return redirect('course_detail', course_id=course.id)
            elif 'unenroll' in request.POST and is_enrolled:
                Enrollment.objects.filter(student=request.user, course=course).delete()
                messages.success(request, f'You have been unenrolled from the course "{course.title}".')
                return redirect('course_detail', course_id=course.id)
            elif 'enroll' in request.POST and not is_enrolled:
                Enrollment.objects.create(student=request.user, course=course)
                notify_teacher_on_enrollment(request.user, course)
                messages.success(request, f'You have been enrolled in the course "{course.title}".')
                return redirect('course_detail', course_id=course.id)

        return redirect('course_detail', course_id=course.id)

    context = {
        'course': course,
        'feedbacks': feedbacks,
        'materials': materials,
        'is_student': is_student,
        'is_enrolled': is_enrolled,
        'feedback_form': feedback_form,
        'user_notifications': user_notifications,  # Pass notifications to the context
    }
    return render(request, 'course_detail.html', context)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def enroll(request, course_id):
    """
    Enrolls a student in a course.
    """
    course = get_object_or_404(Course, id=course_id)

    if request.user.is_student:
        enrollment, created = Enrollment.objects.get_or_create(student=request.user, course=course)
        if created:
            messages.success(request, f'You have been enrolled in the course "{course.title}".')
        else:
            messages.info(request, f'You are already enrolled in the course "{course.title}".')
    else:
        messages.error(request, "Only students can enroll in courses.")

    return redirect('course_detail', course_id=course.id)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def delete_course(request, course_id):
    """
    Deletes a course. Only accessible to the teacher who created the course.
    """
    course = get_object_or_404(Course, id=course_id)

    if request.user != course.teacher:
        return Response({"error": "You are not authorized to delete this course."}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        return render(request, 'confirm_delete_course.html', {'course': course})

    elif request.method == 'POST':
        course.delete()
        messages.success(request, "Course deleted successfully.")
        return redirect('home')

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def edit_course(request, course_id):
    """
    Edits a course. Only accessible to the teacher who created the course.
    """
    course = get_object_or_404(Course, id=course_id)

    if request.user != course.teacher:
        return Response({"error": "You are not authorized to edit this course."}, status=status.HTTP_403_FORBIDDEN)

    if request.method == 'GET':
        form = CourseForm(instance=course)
        return render(request, 'edit_course.html', {'form': form, 'course': course})

    elif request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            form.save()
            messages.success(request, "Course updated successfully.")
            return redirect('course_detail', course_id=course.id)
        else:
            messages.error(request, "There was an error updating the course.")
            return render(request, 'edit_course.html', {'form': form, 'course': course})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_users(request):
    """
    Allows teachers to search for students.
    """
    if not request.user.is_teacher:
        return Response({"detail": "You are not authorized to search for students."}, status=status.HTTP_403_FORBIDDEN)

    query = request.GET.get('q', '')
    students = CustomUser.objects.filter(is_student=True)

    if query:
        students = students.filter(
            username__icontains=query
        ) | students.filter(
            first_name__icontains=query
        ) | students.filter(
            last_name__icontains=query
        )

    return render(request, 'search_results.html', {'students': students, 'query': query})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def post_status(request):
    """
    Posts a status update by the user.
    """
    content = request.POST.get('content')
    if content:
        StatusUpdate.objects.create(user=request.user, content=content)
        return Response({"message": "Status update posted successfully."}, status=status.HTTP_201_CREATED)
    return Response({"error": "Content cannot be empty."}, status=status.HTTP_400_BAD_REQUEST)

@login_required
def room(request, room_name):
    """
    Renders the chat room.
    """
    return render(request, 'chat_room.html', {'room_name': room_name})

class LoginView(auth_views.LoginView):
    """
    Custom login view.
    """
    template_name = 'login.html'

class LogoutView(auth_views.LogoutView):
    """
    Custom logout view.
    """
    next_page = '/'

@login_required
def chat_home(request):
    """
    Displays the chat home page with available chat rooms.
    """
    dynamic_rooms = ChatRoom.objects.exclude(name__in=['general', 'math', 'science'])
    default_rooms = ChatRoom.objects.filter(name__in=['general', 'math', 'science'])

    return render(request, 'chat_home.html', {
        'recent_rooms': dynamic_rooms,
        'default_rooms': default_rooms,
    })

@login_required
def create_room(request):
    """
    Creates a new chat room.
    """
    if request.method == 'POST':
        room_name = request.POST.get('room_name').strip()
        if room_name:
            room, created = ChatRoom.objects.get_or_create(name=room_name)
            if created:
                messages.success(request, f"Chat room '{room_name}' created successfully.")
            else:
                messages.info(request, f"Chat room '{room_name}' already exists. Joining the room.")
            return redirect('room', room_name=room_name)
    return redirect('chat_home')

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_type_check(request):
    """
    Checks if the user is a teacher.
    """
    return Response({'is_teacher': request.user.is_teacher})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def leave_feedback(request, course_id):
    """
    Allows students to leave feedback on a course.
    """
    course = get_object_or_404(Course, id=course_id)
    if handle_feedback_submission(request, course):
        return Response({"message": "Feedback submitted successfully."}, status=status.HTTP_201_CREATED)
    return Response({"error": "Feedback submission failed."}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
@user_passes_test(lambda u: u.is_teacher)
def view_feedback(request, course_id):
    """
    Allows teachers to view feedback for their courses.
    """
    course = get_object_or_404(Course, id=course_id)

    if course.teacher != request.user:
        return Response({"error": "You are not authorized to view this feedback."}, status=status.HTTP_403_FORBIDDEN)

    feedbacks = Feedback.objects.filter(course=course).order_by('-created_at')

    return Response({"feedbacks": list(feedbacks.values('student__username', 'content', 'created_at'))}, status=status.HTTP_200_OK)

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@login_required
def user_profile(request):
    """
    Displays and allows editing of the user's profile.
    """
    user = request.user
    edit_mode = request.GET.get('edit') == '1'

    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Your profile has been updated successfully.")
            return redirect('user_profile')
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = UserProfileForm(instance=user)

    return render(request, 'user_profile.html', {'form': form, 'edit_mode': edit_mode})

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def add_material(request, course_id):
    """
    Allows teachers to add new material to a course.
    """
    course = get_object_or_404(Course, id=course_id)

    if not request.user.is_teacher:
        return redirect('course_detail', course_id=course.id)

    if request.method == 'POST':
        form = MaterialForm(request.POST, request.FILES)
        if form.is_valid():
            material = form.save(commit=False)
            material.course = course
            material.save()

            # Notify all enrolled students about the new material
            enrolled_students = Enrollment.objects.filter(course=course).values_list('student', flat=True)
            for student_id in enrolled_students:
                student = get_user_model().objects.get(id=student_id)
                notify_student_on_new_material(student, course, material)

            messages.success(request, "New material has been added to the course.")
            return redirect('course_detail', course_id=course.id)
    else:
        form = MaterialForm()

    return render(request, 'add_material.html', {'course': course, 'form': form})

@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
@login_required
def edit_material(request, course_id, material_id):
    """
    Allows teachers to edit existing material in a course.
    """
    course = get_object_or_404(Course, id=course_id)
    material = get_object_or_404(Material, id=material_id, course=course)

    # Only allow the teacher to edit their materials
    if request.user != course.teacher:
        messages.error(request, "You are not authorized to edit this material.")
        return redirect('course_detail', course_id=course.id)

    if request.method == 'POST':
        form = MaterialForm(request.POST, request.FILES, instance=material)
        if form.is_valid():
            form.save()
            messages.success(request, "Material has been updated successfully.")
            return redirect('course_detail', course_id=course.id)
    else:
        form = MaterialForm(instance=material)

    return render(request, 'edit_material.html', {'form': form, 'course': course, 'material': material})


@login_required
def notifications(request):
    """
    Displays notifications for the logged-in user.
    """
    # Log the request to view notifications
    logger.debug(f"User {request.user.username} requested to view notifications.")

    user_notifications = Notification.objects.filter(user=request.user, read=False)

    # Log the count of notifications retrieved
    logger.debug(f"Retrieved {len(user_notifications)} unread notifications for user {request.user.username}")

    return render(request, 'notifications.html', {'notifications': user_notifications})


@api_view(['POST'])
@login_required
def mark_notification_read(request, notification_id):
    """
    Marks a notification as read.
    """
    # Log the request to mark a notification as read
    logger.debug(f"User {request.user.username} requested to mark notification {notification_id} as read.")

    notification = get_object_or_404(Notification, id=notification_id, user=request.user)
    notification.read = True
    notification.save()

    # Log the successful marking of the notification as read
    logger.debug(f"Notification {notification_id} marked as read for user {request.user.username}")

    return redirect('notifications')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@login_required
def remove_student(request, course_id, student_id):
    """
    Allows teachers to remove a student from their course.
    """
    course = get_object_or_404(Course, id=course_id)

    if request.user != course.teacher:
        messages.error(request, "You are not authorized to remove students from this course.")
        return redirect('course_detail', course_id=course.id)

    enrollment = get_object_or_404(Enrollment, course=course, student_id=student_id)
    enrollment.delete()
    messages.success(request, "Student has been removed from the course.")
    return redirect('course_detail', course_id=course.id)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@login_required
def block_student(request, course_id, student_id):
    """
    Allows teachers to block a student from their course.
    """
    course = get_object_or_404(Course, id=course_id)

    if request.user != course.teacher:
        messages.error(request, "You are not authorized to block students from this course.")
        return redirect('course_detail', course_id=course.id)

    enrollment = get_object_or_404(Enrollment, course=course, student_id=student_id)
    enrollment.blocked = True
    enrollment.save()
    messages.success(request, "Student has been blocked from the course.")
    return redirect('course_detail', course_id=course.id)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
@login_required
def unblock_student(request, course_id, student_id):
    """
    Allows teachers to unblock a student from their course.
    """
    course = get_object_or_404(Course, id=course_id)

    if request.user != course.teacher:
        messages.error(request, "You are not authorized to unblock students from this course.")
        return redirect('course_detail', course_id=course.id)

    enrollment = get_object_or_404(Enrollment, course=course, student_id=student_id)
    enrollment.blocked = False
    enrollment.save()
    messages.success(request, "Student has been unblocked from the course.")
    return redirect('course_detail', course_id=course.id)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def teacher_courses(request):
    """
    View for teachers to see their courses and the list of students enrolled in each course.
    """
    # Ensure the user is a teacher
    if not request.user.is_teacher:
        messages.error(request, "Only teachers can access this page.")
        return redirect('home')

    # Get all courses created by the teacher
    teacher_courses = Course.objects.filter(teacher=request.user)

    # Prepare the context with courses and students
    course_students = {}
    for course in teacher_courses:
        students_enrolled = Enrollment.objects.filter(course=course).select_related('student')
        course_students[course.id] = students_enrolled  # Store enrollments by course ID

    # Debugging: Print course_students to check its contents
    print(f"Courses: {teacher_courses}")
    print(f"Course Students: {course_students}")

    # Render the template with the course and student data
    return render(request, 'teacher_courses.html', {
        'teacher_courses': teacher_courses,
        'course_students': course_students,
    })

