from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Course, Feedback


# Customize the display and editing options for the CustomUser model in the admin
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    # Display these fields in the list view
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_student', 'is_teacher', 'is_staff')
    # Add the fields to the fieldsets to appear in the admin form
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('is_student', 'is_teacher')}),
    )
    # Make sure these fields are available when adding a new user
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('is_student', 'is_teacher')}),
    )


# Register the CustomUser model with the customized UserAdmin
admin.site.register(CustomUser, CustomUserAdmin)


# Customize the display for the Course model in the admin
class CourseAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'teacher')
    search_fields = ('title', 'description')
    list_filter = ('teacher',)


# Register the Course model with the customized CourseAdmin
admin.site.register(Course, CourseAdmin)


# Customize the display for the Feedback model in the admin
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('course', 'student', 'content', 'created_at')
    search_fields = ('course__title', 'student__username', 'content')
    list_filter = ('course', 'student', 'created_at')


# Register the Feedback model with the customized FeedbackAdmin
admin.site.register(Feedback, FeedbackAdmin)
