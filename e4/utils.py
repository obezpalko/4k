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