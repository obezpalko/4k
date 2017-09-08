drop table if exists intervals;
create table intervals (
  id integer primary key autoincrement,
  title text not null,
  item char default 'd',
  value tinyint not null default 1
);
insert into intervals values(1, 'daily', 'd', 1);
insert into intervals values(2, 'weekly', 'd', 7);
insert into intervals values(3, 'biweekly', 'd', 14);
insert into intervals values(4, 'monthly', 'm', 1);
insert into intervals values(5, 'bimonthly', 'm', 2);
insert into intervals values(6, 'quaterly', 'm', 3);
insert into intervals values(7, 'half-year', 'm', 6);
insert into intervals values(8, 'yearly', 'm', 12);


drop table if exists incomes;
create table incomes (
   id integer primary key autoincrement,
   title text not null,
   currency integer,
  end_date DATETIME ,
  period REFERENCES intervals(id) ,
  start_date DATETIME,
  FOREIGN KEY(period) REFERENCES intervals(id)
);

PRAGMA foreign_keys = ON;