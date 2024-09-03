from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Course, Feedback, Material


class CustomUserCreationForm(UserCreationForm):
    """
    Form for creating a new user, extending the default Django UserCreationForm.
    Provides additional fields for 'is_student' and 'is_teacher' to determine the user's role.
    """
    class Meta(UserCreationForm.Meta):
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'is_student', 'is_teacher')
        widgets = {
            'username': forms.TextInput(attrs={'placeholder': 'Username'}),
            'email': forms.EmailInput(attrs={'placeholder': 'Email'}),
            'first_name': forms.TextInput(attrs={'placeholder': 'First Name'}),
            'last_name': forms.TextInput(attrs={'placeholder': 'Last Name'}),
        }

    def clean(self):
        """
        Custom validation to ensure the user is either a student or a teacher, not both or neither.
        """
        cleaned_data = super().clean()
        is_student = cleaned_data.get('is_student')
        is_teacher = cleaned_data.get('is_teacher')

        if is_student and is_teacher:
            raise forms.ValidationError("User cannot be both a student and a teacher.")
        if not is_student and not is_teacher:
            raise forms.ValidationError("User must be either a student or a teacher.")

        return cleaned_data


class CourseForm(forms.ModelForm):
    """
    Form for creating and editing a course.
    Provides fields for 'title' and 'description' with custom widgets.
    """
    class Meta:
        model = Course
        fields = ['title', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Course Title'}),
            'description': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Enter course description...'}),
        }


class FeedbackForm(forms.ModelForm):
    """
    Form for submitting feedback on a course.
    Includes fields for 'content' and 'rating', with custom widgets and validation.
    """
    class Meta:
        model = Feedback
        fields = ['content', 'rating']
        widgets = {
            'content': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Enter your feedback...'}),
            'rating': forms.NumberInput(attrs={'min': 1, 'max': 5, 'placeholder': 'Rate from 1 to 5'}),
        }

    def clean_content(self):
        """
        Custom validation for feedback content to ensure it is at least 10 characters long.
        """
        content = self.cleaned_data.get('content')
        if len(content) < 10:
            raise forms.ValidationError("Feedback must be at least 10 characters long.")
        return content


class UserProfileForm(forms.ModelForm):
    """
    Form for updating a user's profile information.
    Allows updates to fields like username, email, first name, last name, bio, and profile photo.
    """
    class Meta:
        model = CustomUser
        fields = ['username', 'email', 'first_name', 'last_name', 'bio', 'profile_photo']
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Tell us about yourself...'}),
        }

    def clean_email(self):
        """
        Custom validation to ensure the email is unique across all users.
        """
        email = self.cleaned_data.get('email')
        if CustomUser.objects.filter(email=email).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("This email is already in use.")
        return email


class MaterialForm(forms.ModelForm):
    """
    Form for adding or editing course materials.
    Includes fields for 'title', 'description', and 'file'.
    """
    class Meta:
        model = Material
        fields = ['title', 'description', 'file']
