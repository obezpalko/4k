drop table if exists intervals;
create table intervals (
  id integer primary key autoincrement,
  title text not null,
  item char default 'd',
  value integer not null default 1
);
insert into intervals values(1, 'daily', 'd', 1);
insert into intervals values(2, 'weekly', 'd', 7);
insert into intervals values(3, 'biweekly', 'd', 14);
insert into intervals values(4, 'monthly', 'm', 1);
insert into intervals values(5, 'bimonthly', 'm', 2);
insert into intervals values(6, 'quaterly', 'm', 3);
insert into intervals values(7, 'half-year', 'm', 6);
insert into intervals values(8, 'yearly', 'm', 12);

drop table if exists rates;

drop table if exists currency;
create table currency (
  currency_id integer primary key autoincrement,
  currency_index text primery key,
  currency_name text,
  is_default numeric default 0
);
insert into currency (currency_index, is_default) values ('ILS', 1);
insert into currency (currency_index) values ('UAH');
insert into currency (currency_index) values ('USD');
insert into currency (currency_index) values ('EUR');
insert into currency (currency_index) values ('GBP');


drop table if exists incomes;
create table incomes (
  id integer primary key autoincrement,
  title text not null,
  currency REFERENCES currency(currency_id) not null,
  sum real not null default 0.0,
  start_date numeric not null,
  end_date numeric,
  period REFERENCES intervals(id),
  FOREIGN KEY(period) REFERENCES intervals(id)
);


create table rates (
rate_date numeric not null ,
currency_a references currency(currency_id),
currency_b references currency(currency_id),
rate real not null
);

PRAGMA foreign_keys = ON;