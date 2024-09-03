from django.db import models
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.utils import timezone
from django.conf import settings


# Custom User Model
class CustomUser(AbstractUser):
    """
    Extends the default Django user model to include custom fields and permissions.
    """
    is_student = models.BooleanField(default=False)
    is_teacher = models.BooleanField(default=False)
    profile_photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True)
    bio = models.TextField(blank=True, null=True)

    # Avoid clashes with default user model relations
    groups = models.ManyToManyField(
        Group,
        related_name='customuser_set',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='customuser_permissions_set',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    def is_student_user(self):
        """
        Checks if the user is a student.
        """
        return self.is_student

    def is_teacher_user(self):
        """
        Checks if the user is a teacher.
        """
        return self.is_teacher

    def __str__(self):
        return self.username


# Course Model
class Course(models.Model):
    """
    Represents a course created by a teacher.
    """
    title = models.CharField(max_length=200)
    description = models.TextField()
    teacher = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='courses')

    def __str__(self):
        return self.title


# Feedback Model
class Feedback(models.Model):
    """
    Represents feedback given by a student on a course.
    """
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='feedbacks')
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='feedbacks')
    content = models.TextField()
    rating = models.IntegerField(default=5)  # Feedback rating field
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Feedback by {self.student.username} for {self.course.title}'


# Enrollment Model
class Enrollment(models.Model):
    """
    Represents the enrollment of a student in a course.
    """
    student = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_on = models.DateTimeField(default=timezone.now)
    blocked = models.BooleanField(default=False)  # Indicates if the student is blocked

    class Meta:
        unique_together = ('student', 'course')  # Ensures unique enrollment per student and course

    def __str__(self):
        return f"{self.student.username} enrolled in {self.course.title}"


# Status Update Model
class StatusUpdate(models.Model):
    """
    Represents a status update posted by a user.
    """
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}: {self.content} ({self.timestamp})"


# Chat Room Model
class ChatRoom(models.Model):
    """
    Represents a chat room for group conversations.
    """
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


# Chat Message Model
class ChatMessage(models.Model):
    """
    Represents a message sent in a chat room.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    room = models.ForeignKey('ChatRoom', on_delete=models.CASCADE, null=True, blank=True)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}: {self.message} ({self.timestamp})"


# Notification Model
class Notification(models.Model):
    """
    Represents a notification for a user.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
        null=True,
        blank=True
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    read = models.BooleanField(default=False)

    class Meta:
        ordering = ['-created_at']  # Orders notifications by most recent first
        indexes = [
            models.Index(fields=['user', 'read']),  # Adds an index for faster lookup by user and read status
        ]

    def __str__(self):
        return f"Notification for {self.user.username if self.user else 'Unknown'}: {self.content}"

    def mark_as_read(self):
        """
        Marks the notification as read.
        """
        self.read = True
        self.save(update_fields=['read'])

    def mark_as_unread(self):
        """
        Marks the notification as unread.
        """
        self.read = False
        self.save(update_fields=['read'])


# Material Model
class Material(models.Model):
    """
    Represents a material (like PDFs, videos, etc.) for a course.
    """
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    course = models.ForeignKey('Course', on_delete=models.CASCADE, related_name='materials')
    created_at = models.DateTimeField(auto_now_add=True)
    file = models.FileField(upload_to='course_materials/', blank=True, null=True)

    def __str__(self):
        return f"{self.title} for {self.course.title}"
