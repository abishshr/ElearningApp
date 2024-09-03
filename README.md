# E-Learning Platform

This is a Django-based e-learning platform that allows teachers to create courses, manage materials, and communicate with students. The platform also supports real-time chat using WebSockets.

## Features

- **User Management**: Supports different types of users (students and teachers) with separate permissions.
- **Course Management**: Teachers can create courses, upload materials, and view enrolled students. Students can browse and enroll in courses.
- **Real-Time Communication**: Integrated chat functionality using WebSockets for real-time communication between users.
- **REST API**: Provides REST API endpoints for user and course data.
- **Responsive Design**: Frontend designed using Bootstrap 5 for a modern and responsive user interface.
- **Password Reset Functionality**: Allows users to reset their passwords securely.

## Requirements

- Python 3.8+
- Django 5.1
- Redis for WebSocket functionality
- Heroku CLI (for deployment)

## Installation

1. **Clone the repository:**

    ```bash
    git clone https://github.com/yourusername/elearning_project.git
    cd elearning_project
    ```

2. **Create a virtual environment:**

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`
    ```

3. **Install the dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

4. **Set up environment variables:**

   Create a `.env` file in the project root directory with the following variables:

    ```env
    SECRET_KEY='your-django-secret-key'
    EMAIL_HOST_USER='your-email@example.com'
    EMAIL_HOST_PASSWORD='your-email-password'
    ```

5. **Set up the database:**

    ```bash
    python manage.py migrate
    ```

6. **Run the server:**

    ```bash
    python manage.py runserver
    ```

## Usage

- **Teacher Functionality:**
  - Create courses and manage course content.
  - View enrolled students and interact with them.
- **Student Functionality:**
  - Enroll in courses and view course content.
  - Participate in real-time chat and leave feedback.

## Deployment

To deploy the application to Heroku:

1. **Install Heroku CLI**: [Heroku CLI](https://devcenter.heroku.com/articles/heroku-cli)

2. **Log in to Heroku:**

    ```bash
    heroku login
    ```

3. **Create a new Heroku app:**

    ```bash
    heroku create your-app-name
    ```

4. **Add Heroku Redis:**

    ```bash
    heroku addons:create heroku-redis:hobby-dev
    ```

5. **Push your code to Heroku:**

    ```bash
    git push heroku main
    ```

6. **Run migrations and create a superuser:**

    ```bash
    heroku run python manage.py migrate
    heroku run python manage.py createsuperuser
    ```

7. **Set environment variables in Heroku:**
   Go to your Heroku app dashboard > Settings > Reveal Config Vars, and add your environment variables (`SECRET_KEY`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, etc.).

## Testing

1. **Run Unit Tests:**

    ```bash
    python manage.py test
    ```

2. **Run Integration Tests:**
   Ensure all components are working together as expected.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request to improve the project.

## License

This project is licensed under the MIT License.

## Acknowledgements

- Django for the web framework.
- Bootstrap 5 for the responsive frontend.
- Heroku for hosting and deployment.

