from django.test import TestCase, Client, TransactionTestCase
from django.urls import reverse
from channels.testing import WebsocketCommunicator
from .models import CustomUser, Course, Enrollment, Notification
from .consumers import EchoConsumer
from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import re_path
from django.contrib.auth import get_user_model


class WebSocketTests(TransactionTestCase):
    async def test_websocket_communication(self):
        # Set up WebSocket routing for the test
        application = ProtocolTypeRouter({
            'websocket': URLRouter([
                re_path(r'ws/chat/(?P<room_name>\w+)/$', EchoConsumer.as_asgi()),
            ])
        })

        # Set up WebSocket communicator with the correct path
        communicator = WebsocketCommunicator(application, "/ws/chat/sample_room/")
        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        # Send a message through the WebSocket
        await communicator.send_json_to({"message": "Hello"})
        response = await communicator.receive_json_from()

        # Check if the response matches the sent message
        self.assertEqual(response['message'], 'Hello')

        # Close the WebSocket connection
        await communicator.disconnect()


class UserTests(TestCase):

    def setUp(self):
        # Create a test client
        self.client = Client()

        # Create a teacher user
        self.teacher = CustomUser.objects.create_user(
            username='teacher1', password='password123', is_teacher=True
        )

        # Create a student user
        self.student = CustomUser.objects.create_user(
            username='student1', password='password123', is_student=True
        )

    def test_user_registration(self):
        # Test user registration functionality
        response = self.client.post(reverse('register'), {
            'username': 'newuser',
            'email': 'newuser@example.com',
            'password1': 'strongpassword123',
            'password2': 'strongpassword123',
            'is_student': True
        })
        self.assertEqual(response.status_code, 302)  # Check if redirect occurred
        self.assertTrue(CustomUser.objects.filter(username='newuser').exists())

    def test_teacher_login(self):
        # Test teacher login functionality
        response = self.client.post(reverse('login'), {'username': 'teacher1', 'password': 'password123'})
        self.assertEqual(response.status_code, 302)  # Check if redirect occurred

    def test_student_login(self):
        # Test student login functionality
        response = self.client.post(reverse('login'), {'username': 'student1', 'password': 'password123'})
        self.assertEqual(response.status_code, 302)  # Check if redirect occurred


class CourseTests(TestCase):

    def setUp(self):
        self.client = Client()
        self.teacher = CustomUser.objects.create_user(
            username='teacher2', password='password123', is_teacher=True
        )
        self.client.login(username='teacher2', password='password123')

    def test_course_creation(self):
        # Test course creation by a teacher
        response = self.client.post(reverse('create_course'), {
            'title': 'New Course',
            'description': 'Course Description'
        })
        self.assertEqual(response.status_code, 302)  # Check if redirect occurred
        self.assertTrue(Course.objects.filter(title='New Course').exists())

    def test_enroll_student(self):
        # Create a student and login
        student = CustomUser.objects.create_user(username='student2', password='password123', is_student=True)
        course = Course.objects.create(title='Sample Course', description='Sample Description', teacher=self.teacher)

        # Log in as the student
        self.client.login(username='student2', password='password123')

        # Send POST request to enroll in the course
        response = self.client.post(reverse('enroll', args=[course.id]))

        # Check if the enrollment was successful (status code should be 302 for redirect after enrollment)
        self.assertEqual(response.status_code, 302)

        # Verify that the enrollment was created
        self.assertTrue(Enrollment.objects.filter(student=student, course=course).exists())



class NotificationTestCase(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='testuser', password='password')
        Notification.objects.create(user=self.user, content="New course available.")

    def test_notification_creation(self):
        self.assertEqual(Notification.objects.count(), 1)
        self.assertEqual(Notification.objects.first().content, "New course available.")

    def test_notification_retrieval(self):
        response = self.client.login(username='testuser', password='password')
        response = self.client.get('/notifications/')
        self.assertContains(response, "New course available.")
