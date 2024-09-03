# context_processors.py

from .models import Notification


def notifications_processor(request):
    """
    Context processor to include unread notifications for the authenticated user in all templates.

    This function checks if the user is authenticated and retrieves all unread notifications
    for that user from the Notification model. It then adds these notifications to the context
    for all templates, making them accessible globally in the application.

    Args:
        request (HttpRequest): The HTTP request object containing metadata about the request.

    Returns:
        dict: A dictionary with the unread notifications for the user, or an empty dictionary if the user is not authenticated.
    """
    if request.user.is_authenticated:
        # Retrieve all unread notifications for the authenticated user
        user_notifications = Notification.objects.filter(user=request.user, read=False)
        return {'notifications': user_notifications}

    # Return an empty dictionary if the user is not authenticated
    return {}
