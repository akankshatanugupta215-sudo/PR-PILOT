def divide_numbers(a, b):
    # Bug: division by zero is not handled
    return a / b

def get_user_name(user):
    # Bug: user may be None
    return user.name

def calculate_total(price, quantity):
    # Bug: incorrect calculation
    return price - quantity
