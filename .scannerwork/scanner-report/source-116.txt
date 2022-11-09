import random
import string


def generate_password(length: int):
    random_char = string.digits + string.ascii_uppercase + string.digits + string.ascii_lowercase
    return ''.join(random.choice(random_char) for i in range(length))
