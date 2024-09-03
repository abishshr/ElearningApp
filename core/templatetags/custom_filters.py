# core/templatetags/custom_filters.py

from django import template

register = template.Library()


@register.filter(name='add_class')
def add_class(field, css_class):
    """
    Adds a CSS class to a form field in a template.
    """
    try:
        # Ensure the object has the as_widget method
        return field.as_widget(attrs={'class': css_class})
    except AttributeError:
        # If not, return the field as is
        return field


@register.filter(name='dict_key')
def dict_key(value, key):
    """
    Retrieves a value from a dictionary using the specified key.

    Args:
        value (dict): The dictionary to look up.
        key: The key to find in the dictionary.

    Returns:
        The value associated with the key if it exists; otherwise, None.
    """
    try:
        return value.get(key)
    except (TypeError, AttributeError):
        # Return None if value is not a dictionary or if key is not found
        return None


@register.filter(name='get_item')
def get_item(dictionary, key):
    """
    Custom filter to get a value from a dictionary.
    """
    return dictionary.get(key)
