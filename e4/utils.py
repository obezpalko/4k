#
from datetime import datetime, date, time, timedelta
from calendar import monthrange
from math import ceil

def dict_factory(cursor, row):
  d = {}
  for idx, col in enumerate(cursor.description):
    d[col[0]] = row[idx]
  return d

def to_dict(a=[], id_="id"):
  result = {}
  if type(a) == type({}):
    return a
  for row in a:
    result[row[id_]] = row
  return result

def add_months(sourcedate, months):
  month = sourcedate.month - 1 + months
  year = int(sourcedate.year + month / 12)
  month = month % 12 + 1
  day = min(sourcedate.day, monthrange(year, month)[1])
  return sourcedate.replace(year, month, day)

def next_date(current_date, period=(1, 'm'), count=1):
  if period[0] == 0: return None
  
  if period[1] == 'd': return current_date + timedelta(period[0] * count)
  return add_months(current_date, period[0] * count)

def number_of_weeks(date1, date2):
  start_date = datetime.strptime(date1, '%Y-%m-%d').date()
  start_date_monday = (start_date - timedelta(days=start_date.weekday()))
  end_date = datetime.strptime(date2, '%Y-%m-%d').date()
  return ceil((end_date - start_date_monday).days / 7.0)
