from django.urls import path, re_path, include
from django.contrib import admin
from rest_framework import permissions
from rest_framework.routers import DefaultRouter
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

from .views import (
    HomeView, enroll, search_users, post_status, room, LoginView, LogoutView, chat_home,
    user_type_check, leave_feedback, view_feedback, register, edit_course, delete_course, create_course,
    course_detail, course_list, create_room, user_profile,
    CustomUserViewSet, CourseViewSet, EnrollmentViewSet, FeedbackViewSet, StatusUpdateViewSet, add_material,
    notifications, mark_notification_read, edit_material, remove_student, block_student, unblock_student,
    teacher_courses
)

# Set up Swagger schema view for API documentation
schema_view = get_schema_view(
    openapi.Info(
        title="ELearning API",
        default_version='v1',
        description="API documentation for ELearning project",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="abishs@me.com"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

# Set up DRF Router for API ViewSets
router = DefaultRouter()
router.register(r'users', CustomUserViewSet, basename='user')
router.register(r'courses', CourseViewSet, basename='course')
router.register(r'enrollments', EnrollmentViewSet, basename='enrollment')
router.register(r'feedback', FeedbackViewSet, basename='feedback')
router.register(r'status-updates', StatusUpdateViewSet, basename='status-update')

# URL patterns for the application
urlpatterns = [
    # Authentication URLs
    path('accounts/login/', LoginView.as_view(), name='login'),
    path('accounts/logout/', LogoutView.as_view(), name='logout'),
    path('register/', register, name='register'),

    # Home and Course Management URLs
    path('', HomeView.as_view(), name='home'),
    path('courses/', course_list, name='course_list'),
    path('courses/create/', create_course, name='create_course'),
    path('courses/<int:course_id>/', course_detail, name='course_detail'),
    path('courses/<int:course_id>/enroll/', enroll, name='enroll'),
    path('courses/<int:course_id>/add_material/', add_material, name='add_material'),
    path('courses/<int:course_id>/materials/<int:material_id>/edit/', edit_material, name='edit_material'),
    path('courses/<int:course_id>/edit/', edit_course, name='edit_course'),
    path('courses/<int:course_id>/delete/', delete_course, name='delete_course'),
    path('courses/<int:course_id>/students/<int:student_id>/remove/', remove_student, name='remove_student'),
    path('courses/<int:course_id>/students/<int:student_id>/block/', block_student, name='block_student'),
    path('courses/<int:course_id>/students/<int:student_id>/unblock/', unblock_student, name='unblock_student'),

    # User Profile URL
    path('profile/', user_profile, name='user_profile'),

    # Feedback and User Management URLs
    path('search_users/', search_users, name='search_users'),
    path('post_status/', post_status, name='post_status'),
    path('user_type_check/', user_type_check, name='user_type_check'),
    path('courses/<int:course_id>/feedback/', leave_feedback, name='leave_feedback'),
    path('courses/<int:course_id>/view_feedback/', view_feedback, name='view_feedback'),

    path('teacher/courses/', teacher_courses, name='teacher_courses'),
    # Chat URLs
    path('chat/', chat_home, name='chat_home'),
    path('chat/create/', create_room, name='create_room'),
    path('chat/<str:room_name>/', room, name='room'),

    # Password reset URLs
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html'),
         name='password_reset'),
    path('password_reset/done/',
         auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'),
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'),
         name='password_reset_confirm'),
    path('reset/done/',
         auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'),
         name='password_reset_complete'),

    # Notifications URLs
    path('notifications/', notifications, name='notifications'),
    path('notifications/<int:notification_id>/read/', mark_notification_read, name='mark_notification_read'),

    # API URLs
    path('api/', include(router.urls)),  # Include the router URLs for the REST API

    # Swagger and API Documentation URLs
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),


    # Admin URL
    path('admin/', admin.site.urls),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
