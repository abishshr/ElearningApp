# signals.py

from django.apps import AppConfig
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from .models import ChatRoom


@receiver(post_migrate)
def create_default_chatrooms(sender, **kwargs):
    """
    Signal handler to create default chat rooms after a migration.

    This function is triggered by the 'post_migrate' signal to ensure
    that the default chat rooms ('general', 'math', 'science') exist
    after migrations are applied to the 'core' app.

    Args:
        sender (django.apps.AppConfig): The application configuration class that sent the signal.
        **kwargs: Additional keyword arguments.
    """
    # Check if the sender is the 'core' app
    if sender.name == 'core':  # Replace 'core' with your app name if different
        # List of default chat rooms to be created
        default_rooms = ['general', 'math', 'science']

        # Iterate over the list and create each chat room if it does not exist
        for room_name in default_rooms:
            ChatRoom.objects.get_or_create(name=room_name)
