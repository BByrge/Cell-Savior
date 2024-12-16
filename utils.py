import random

def generate_state():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=16))
