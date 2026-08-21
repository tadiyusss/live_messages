from core.utils.registry.context_processors import register_context_processor
from extensions.live_messages.forms.start_live_chat import StartLiveChatForm
import re
from flask import request

def inject_live_messages_form():
    if not re.match(r'^/dashboard', request.path):
        return dict(live_messages_form=StartLiveChatForm())
    else:
        return dict(live_messages_form=None)

context_processors = [inject_live_messages_form]

def initialize_context_processors():
    """
    Register all context processors in the system.
    """
    for processor in context_processors:
        register_context_processor(processor)