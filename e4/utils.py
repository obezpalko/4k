"""
 useful functions to work with objects
"""

from datetime import datetime, timedelta
from calendar import monthrange
from math import ceil
# from .database import Currency, Income, Rate, Interval, Transaction, Account


def dict_factory(cursor, row):
    """ convert sursor into dict """
    result = {}
    for idx, col in enumerate(cursor.description):
        result[col[0]] = row[idx]
    return result


def to_dict(arr, id_='id'):
    """ convert array to dict """
    result = {}
    if isinstance(arr, dict):
        return arr
    for row in arr:
        result[row[id_]] = row
    return result


def add_months(sourcedate, months):
    """ add number of months to date """
    month = sourcedate.month - 1 + months
    year = int(sourcedate.year + month / 12)
    month = month % 12 + 1
    day = min(sourcedate.day, monthrange(year, month)[1])
    return sourcedate.replace(year, month, day)


def next_date(current_date, period=(1, 'm'), count=1):
    """ show next date(s) for periodic event """
    if period[0] == 0:
        return None
    if period[1] == 'd':
        return current_date + timedelta(period[0] * count)
    return add_months(current_date, period[0] * count)


def number_of_weeks(date1, date2):
    """ get number fo weeks between dates """
    start_date = datetime.strptime(date1, '%Y-%m-%d').date()
    start_date_monday = (start_date - timedelta(days=start_date.weekday()))
    end_date = datetime.strptime(date2, '%Y-%m-%d').date()
    return ceil((end_date - start_date_monday).days / 7.0)


def strip_numbers(number):
    """ replace accidentally entered instead decimal dot chars """
    return number.replace(
            'ю', '.').replace('ץ', '.').replace(',', '.').replace(' ', '')
