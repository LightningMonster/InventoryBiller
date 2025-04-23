def convert_to_words(num):
    """
    Convert a number to words representation
    Example: 1234.56 -> "One Thousand Two Hundred Thirty Four Rupees and Fifty Six Paise"
    
    Args:
        num (float): The number to convert
    
    Returns:
        str: The number in words
    """
    # Lists for number words
    ones = ['', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine']
    teens = ['Ten', 'Eleven', 'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen', 'Seventeen', 'Eighteen', 'Nineteen']
    tens = ['', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety']
    
    def number_to_words(n):
        if n < 10:
            return ones[n]
        elif n < 20:
            return teens[n - 10]
        elif n < 100:
            return tens[n // 10] + (' ' + ones[n % 10] if n % 10 != 0 else '')
        elif n < 1000:
            return ones[n // 100] + ' Hundred' + (' and ' + number_to_words(n % 100) if n % 100 != 0 else '')
        elif n < 100000:
            return number_to_words(n // 1000) + ' Thousand' + (' ' + number_to_words(n % 1000) if n % 1000 != 0 else '')
        elif n < 10000000:
            return number_to_words(n // 100000) + ' Lakh' + (' ' + number_to_words(n % 100000) if n % 100000 != 0 else '')
        return number_to_words(n // 10000000) + ' Crore' + (' ' + number_to_words(n % 10000000) if n % 10000000 != 0 else '')
    
    # Split the number into rupees and paise
    rupees = int(num)
    paise = int(round((num - rupees) * 100))
    
    # Convert rupees to words
    if rupees == 0:
        rupees_in_words = 'Zero Rupees'
    else:
        rupees_in_words = number_to_words(rupees) + ' Rupees'
    
    # Convert paise to words
    if paise == 0:
        return rupees_in_words
    else:
        return rupees_in_words + ' and ' + number_to_words(paise) + ' Paise'

def validate_gst_number(gst_number):
    """
    Validate if a GST number is in the correct format
    
    Args:
        gst_number (str): The GST number to validate
    
    Returns:
        bool: True if valid, False otherwise
    """
    import re
    
    # GST format: 2 chars for state code, 10 chars PAN, 1 char entity number, 
    # 1 char Z by default, 1 char checksum
    pattern = r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$'
    
    return bool(re.match(pattern, gst_number))

def validate_numeric_input(value, min_value=None, max_value=None):
    """
    Validate if a string is a valid numeric input within a range
    
    Args:
        value (str): The value to validate
        min_value (float, optional): Minimum allowed value
        max_value (float, optional): Maximum allowed value
    
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        num = float(value)
        
        if min_value is not None and num < min_value:
            return False
        
        if max_value is not None and num > max_value:
            return False
        
        return True
    except ValueError:
        return False
