from grafanalib.core import Panel
from .row import Row

import hashlib

def row3(*args: Panel):
    return Row(3, *args)


def row4(*args: Panel):
    return Row(4, *args)


def row5(*args: Panel):
    return Row(5, *args)


def row6(*args: Panel):
    return Row(6, *args)


def row7(*args: Panel):
    return Row(7, *args)


def row8(*args: Panel):
    return Row(8, *args)


def create_uid_from_string(input_string):
    # Convert the input string to bytes
    input_bytes = input_string.encode('utf-8')

    # Create a SHA-256 hash object
    hash_object = hashlib.sha256(input_bytes)

    # Get the hexadecimal representation of the hash
    uid = hash_object.hexdigest()

    return uid
