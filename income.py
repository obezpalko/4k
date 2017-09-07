#!/usr/local/bin/python3
"""
income class
"""
from datetime import datetime, date, time, timedelta
from calendar import monthrange
from pprint import pprint
from uuid import uuid4
import yaml

#pp = pprint.PrettyPrinter(indent=2)

def add_months(sourcedate, months):
    month = sourcedate.month - 1 + months
    year = int(sourcedate.year + month / 12)
    month = month % 12 + 1
    day = min(sourcedate.day, monthrange(year, month)[1])
    return sourcedate.replace(year, month, day)


intervals = {
    'daily': 1,
    'weekly': 7,
    'biweekly': 14,
    'monthly': 1,
    'bimonthly': 2,
    'quaterly': 3,
    'half-year': 6,
    'yearly': 12
}


def next_date(current_date, period, count=1):
    if period in ['daily', 'weekly', 'biweekly']:
        return current_date + timedelta(intervals[period] * count)
    else:
        return add_months(current_date, intervals[period] * count)


class Income(object):
    """ """

    def __init__(self, summ, start_date, end_date=None, period='monthly', id=str(uuid4()), name=None):
        object.__init__(self)
        self.summ = summ
        self.start_date = datetime.strptime(start_date, "%Y-%m-%d")
        if end_date:
            self.end_date = datetime.strptime(end_date, "%Y-%m-%d")
        else:
            self.end_date = end_date
        self.period = period
        self.id = id
        self.name = name

    def __repr__(self):
        return "from {} sum {} {} till {}".format(
            self.start_date,
            self.summ,
            self.period,
            self.end_date
        )

    def get_dates(self, end_date):
        list_dates = []
        s = self.summ
        if self.start_date <= end_date:
            list_dates.append((self.name, self.start_date, s))
            nd = next_date(self.start_date, self.period)
            while nd <= end_date and ( self.end_date == None or nd <= self.end_date ) :
                s += self.summ
                list_dates.append((self.name, nd, s))
                nd = next_date(nd, self.period)
        return list_dates
    
    def get_sum(self, end_date):
        try:
            return self.get_dates(end_date)[-1]
        except IndexError:
            return (self.name, None, 0)
  

if __name__ == '__main__':
    list_incomes = yaml.load(open('i.yml'))
    for l in list_incomes:
        pprint(l.get_sum(datetime.strptime("2018-01-01", "%Y-%m-%d")))

    yaml.dump(list_incomes, open('i.yml','w'), explicit_start=True, explicit_end=True)