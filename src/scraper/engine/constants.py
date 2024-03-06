from typing import TypeVar
from src.models.models import Base

A = TypeVar('A', bound=Base)
CLICK = "arguments[0].click();"

CHROME = "chrome"
FIREFOX = "firefox"
