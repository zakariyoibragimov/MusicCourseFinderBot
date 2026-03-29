"""
Инициализация пакета handlers.
"""

from app.handlers.commands import start_handler, help_handler
from app.handlers.search import search_command

__all__ = ["start_handler", "help_handler", "search_command"]
