-- PRAGMA foreign_keys=OFF;
drop table if exists intervals;
create table intervals (
  id integer primary key,
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
insert into intervals values(9, 'onetime', 'd', 0);

drop table if exists currency;
create table currency (
  id integer primary key,
  "index" text not null,
  name text,
  "default" numeric default 0
);
insert into currency ("index", "default") values ('ILS', 1);
insert into currency ("index") values ('UAH');
insert into currency ("index") values ('USD');
insert into currency ("index") values ('EUR');
insert into currency ("index") values ('GBP');




-- PRAGMA foreign_keys=ON;
