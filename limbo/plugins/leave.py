"""Command to make Rosencrantz leave a channel"""
import re


def on_message(msg, server):
    text = msg.get("text", "")
    match = re.findall(r"(\w+\s+|\b)(rs|rosencrantz) leave(\b)", text)
    if not match:
        return

    return '/leave'
