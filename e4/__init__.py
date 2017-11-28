"""
default imports
"""
from .k4 import app, __version__
from .database import Base
from .utils import next_date
from .oauth import google, REDIRECT_URI, get_user_info

# from .plot import plot_weekly_plan
