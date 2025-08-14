"""
Utility functions for Email Guardian application
"""

def clean_csv_value(value):
    """
    Clean CSV values by treating '-' as null/empty values
    
    Args:
        value: The value to clean
        
    Returns:
        str: Cleaned value where '-' becomes empty string, None becomes empty string
    """
    if value is None:
        return ''
    
    # Convert to string and strip whitespace
    str_value = str(value).strip()
    
    # Treat '-' as null/empty value
    if str_value == '-':
        return ''
    
    return str_value

def is_empty_value(value):
    """
    Check if a value should be considered empty/null
    This includes None, empty strings, whitespace, and '-'
    
    Args:
        value: The value to check
        
    Returns:
        bool: True if value should be considered empty
    """
    if value is None:
        return True
    
    str_value = str(value).strip()
    return str_value == '' or str_value == '-'

def display_value(value, default='N/A'):
    """
    Format a value for display in templates
    Shows default text for empty values
    
    Args:
        value: The value to display
        default: Default text to show for empty values
        
    Returns:
        str: Formatted value for display
    """
    if is_empty_value(value):
        return default
    
    return str(value).strip()

def safe_split_csv(value, separator=','):
    """
    Safely split a CSV value, handling empty values and '-'
    
    Args:
        value: The value to split
        separator: The separator to use (default: comma)
        
    Returns:
        list: List of cleaned non-empty values
    """
    if is_empty_value(value):
        return []
    
    # Split and clean each part
    parts = str(value).split(separator)
    cleaned_parts = []
    
    for part in parts:
        cleaned = clean_csv_value(part)
        if cleaned:  # Only add non-empty values
            cleaned_parts.append(cleaned)
    
    return cleaned_parts