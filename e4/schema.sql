--
-- PostgreSQL database dump
--

-- Dumped from database version 10.1
-- Dumped by pg_dump version 10.1

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SET check_function_bodies = false;
SET client_min_messages = warning;
SET row_security = off;

SET search_path = public, pg_catalog;

-- ALTER TABLE IF EXISTS ONLY public.transactions DROP CONSTRAINT IF EXISTS transactions_transfer_fkey;
-- ALTER TABLE IF EXISTS ONLY public.transactions DROP CONSTRAINT IF EXISTS transactions_income_id_fkey;
-- ALTER TABLE IF EXISTS ONLY public.transactions DROP CONSTRAINT IF EXISTS transactions_account_id_fkey;
-- ALTER TABLE IF EXISTS ONLY public.rates DROP CONSTRAINT IF EXISTS rates_currency_b_fkey;
-- ALTER TABLE IF EXISTS ONLY public.rates DROP CONSTRAINT IF EXISTS rates_currency_a_fkey;
-- ALTER TABLE IF EXISTS ONLY public.payforwards DROP CONSTRAINT IF EXISTS payforwards_transaction_id_fkey;
-- ALTER TABLE IF EXISTS ONLY public.payforwards DROP CONSTRAINT IF EXISTS payforwards_income_id_fkey;
-- ALTER TABLE IF EXISTS ONLY public.incomes DROP CONSTRAINT IF EXISTS incomes_currency_id_fkey;
-- ALTER TABLE IF EXISTS ONLY public.accounts DROP CONSTRAINT IF EXISTS accounts_currency_id_fkey;
-- ALTER TABLE IF EXISTS ONLY public.users DROP CONSTRAINT IF EXISTS users_pkey;
-- ALTER TABLE IF EXISTS ONLY public.transactions DROP CONSTRAINT IF EXISTS transactions_pkey;
-- ALTER TABLE IF EXISTS ONLY public.rates DROP CONSTRAINT IF EXISTS rates_pkey;
-- ALTER TABLE IF EXISTS ONLY public.payforwards DROP CONSTRAINT IF EXISTS payforwards_pkey;
-- ALTER TABLE IF EXISTS ONLY public.intervals DROP CONSTRAINT IF EXISTS intervals_pkey;
-- ALTER TABLE IF EXISTS ONLY public.incomes DROP CONSTRAINT IF EXISTS incomes_pkey;
-- ALTER TABLE IF EXISTS ONLY public.currency DROP CONSTRAINT IF EXISTS currency_pkey;
-- ALTER TABLE IF EXISTS ONLY public.accounts DROP CONSTRAINT IF EXISTS accounts_pkey;
-- ALTER TABLE IF EXISTS public.users ALTER COLUMN id DROP DEFAULT;
-- ALTER TABLE IF EXISTS public.transactions ALTER COLUMN id DROP DEFAULT;
-- ALTER TABLE IF EXISTS public.rates ALTER COLUMN id DROP DEFAULT;
-- ALTER TABLE IF EXISTS public.payforwards ALTER COLUMN id DROP DEFAULT;
-- ALTER TABLE IF EXISTS public.intervals ALTER COLUMN id DROP DEFAULT;
-- ALTER TABLE IF EXISTS public.incomes ALTER COLUMN id DROP DEFAULT;
-- ALTER TABLE IF EXISTS public.currency ALTER COLUMN id DROP DEFAULT;
-- ALTER TABLE IF EXISTS public.accounts ALTER COLUMN id DROP DEFAULT;
-- DROP SEQUENCE IF EXISTS public.users_id_seq;
-- DROP TABLE IF EXISTS public.users;
-- DROP SEQUENCE IF EXISTS public.transactions_id_seq;
-- DROP TABLE IF EXISTS public.transactions;
-- DROP SEQUENCE IF EXISTS public.rates_id_seq;
-- DROP TABLE IF EXISTS public.rates;
-- DROP SEQUENCE IF EXISTS public.payforwards_id_seq;
-- DROP TABLE IF EXISTS public.payforwards;
-- DROP SEQUENCE IF EXISTS public.intervals_id_seq;
-- DROP TABLE IF EXISTS public.intervals;
-- DROP SEQUENCE IF EXISTS public.incomes_id_seq;
-- DROP TABLE IF EXISTS public.incomes;
-- DROP SEQUENCE IF EXISTS public.currency_id_seq;
-- DROP TABLE IF EXISTS public.currency;
-- DROP SEQUENCE IF EXISTS public.accounts_id_seq;
-- DROP TABLE IF EXISTS public.accounts;
-- DROP TYPE IF EXISTS public.is_account_shown_enum;
-- DROP TYPE IF EXISTS public.is_accound_deleted_enum;
-- DROP TYPE IF EXISTS public.intervals_enum;
-- DROP EXTENSION IF EXISTS plpgsql;
-- DROP SCHEMA IF EXISTS public;
--
-- Name: public; Type: SCHEMA; Schema: -; Owner: -
--

CREATE SCHEMA public;


--
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON SCHEMA public IS 'standard public schema';


--
-- Name: plpgsql; Type: EXTENSION; Schema: -; Owner: -
--

CREATE EXTENSION IF NOT EXISTS plpgsql WITH SCHEMA pg_catalog;


--
-- Name: EXTENSION plpgsql; Type: COMMENT; Schema: -; Owner: -
--

COMMENT ON EXTENSION plpgsql IS 'PL/pgSQL procedural language';


SET search_path = public, pg_catalog;

--
-- Name: intervals_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE intervals_enum AS ENUM (
    'd',
    'm'
);


--
-- Name: is_accound_deleted_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE is_accound_deleted_enum AS ENUM (
    'y',
    'n'
);


--
-- Name: is_account_shown_enum; Type: TYPE; Schema: public; Owner: -
--

CREATE TYPE is_account_shown_enum AS ENUM (
    'y',
    'n'
);


SET default_with_oids = false;

--
-- Name: accounts; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE accounts (
    id integer NOT NULL,
    title character varying,
    currency_id integer,
    deleted is_accound_deleted_enum,
    show is_account_shown_enum
);


--
-- Name: accounts_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE accounts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: accounts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE accounts_id_seq OWNED BY accounts.id;


--
-- Name: currency; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE currency (
    id integer NOT NULL,
    title character varying,
    name character varying,
    "default" integer
);


--
-- Name: currency_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE currency_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: currency_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE currency_id_seq OWNED BY currency.id;


--
-- Name: incomes; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE incomes (
    id integer NOT NULL,
    title character varying,
    currency_id integer,
    sum numeric(12,2),
    start_date date,
    end_date date,
    period_id integer
);


--
-- Name: incomes_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE incomes_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: incomes_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE incomes_id_seq OWNED BY incomes.id;


--
-- Name: intervals; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE intervals (
    id integer NOT NULL,
    title character varying NOT NULL,
    item intervals_enum,
    value integer NOT NULL
);


--
-- Name: intervals_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE intervals_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: intervals_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE intervals_id_seq OWNED BY intervals.id;


--
-- Name: payforwards; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE payforwards (
    id integer NOT NULL,
    income_id integer,
    income_date date NOT NULL,
    payment_date date NOT NULL,
    transaction_id integer NOT NULL
);


--
-- Name: payforwards_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE payforwards_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: payforwards_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE payforwards_id_seq OWNED BY payforwards.id;


--
-- Name: rates; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE rates (
    id integer NOT NULL,
    rate_date timestamp without time zone,
    currency_a integer,
    currency_b integer,
    rate numeric(15,6) NOT NULL
);


--
-- Name: rates_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE rates_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: rates_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE rates_id_seq OWNED BY rates.id;


--
-- Name: transactions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE transactions (
    id integer NOT NULL,
    "time" date NOT NULL,
    account_id integer,
    sum numeric(12,2) NOT NULL,
    transfer integer,
    income_id integer,
    comment text
);


--
-- Name: transactions_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE transactions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: transactions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE transactions_id_seq OWNED BY transactions.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE users (
    id integer NOT NULL,
    email character varying NOT NULL,
    name character varying,
    gender character varying,
    link character varying,
    picture character varying
);


--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

CREATE SEQUENCE users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: -
--

ALTER SEQUENCE users_id_seq OWNED BY users.id;


--
-- Name: accounts id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY accounts ALTER COLUMN id SET DEFAULT nextval('accounts_id_seq'::regclass);


--
-- Name: currency id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY currency ALTER COLUMN id SET DEFAULT nextval('currency_id_seq'::regclass);


--
-- Name: incomes id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY incomes ALTER COLUMN id SET DEFAULT nextval('incomes_id_seq'::regclass);


--
-- Name: intervals id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY intervals ALTER COLUMN id SET DEFAULT nextval('intervals_id_seq'::regclass);


--
-- Name: payforwards id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY payforwards ALTER COLUMN id SET DEFAULT nextval('payforwards_id_seq'::regclass);


--
-- Name: rates id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY rates ALTER COLUMN id SET DEFAULT nextval('rates_id_seq'::regclass);


--
-- Name: transactions id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY transactions ALTER COLUMN id SET DEFAULT nextval('transactions_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: -
--

ALTER TABLE ONLY users ALTER COLUMN id SET DEFAULT nextval('users_id_seq'::regclass);


--
-- Data for Name: accounts; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: currency; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO currency VALUES (1, 'ILS', 'Israeli new shekel', 1);
INSERT INTO currency VALUES (2, 'UAH', 'Ukrainian hryvnia', 0);
INSERT INTO currency VALUES (3, 'USD', 'United States dollar', 0);
INSERT INTO currency VALUES (4, 'EUR', 'Euro', 0);
INSERT INTO currency VALUES (5, 'GBP', 'Pound sterling', 0);


--
-- Data for Name: incomes; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: intervals; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO intervals VALUES (1, 'daily', 'd', 1);
INSERT INTO intervals VALUES (2, 'weekly', 'd', 7);
INSERT INTO intervals VALUES (3, 'biweekly', 'd', 14);
INSERT INTO intervals VALUES (4, 'monthly', 'm', 1);
INSERT INTO intervals VALUES (5, 'bimonthly', 'm', 2);
INSERT INTO intervals VALUES (6, 'quaterly', 'm', 3);
INSERT INTO intervals VALUES (7, 'half-year', 'm', 6);
INSERT INTO intervals VALUES (8, 'yearly', 'm', 12);
INSERT INTO intervals VALUES (9, 'onetime', 'd', 0);


--
-- Data for Name: payforwards; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: rates; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: transactions; Type: TABLE DATA; Schema: public; Owner: -
--



--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: -
--

INSERT INTO users VALUES (1, 'obezpalko@gmail.com', 'Oleksandr Bezpalko', 'male', NULL, NULL);


--
-- Name: accounts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('accounts_id_seq', 1, false);


--
-- Name: currency_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('currency_id_seq', 1, false);


--
-- Name: incomes_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('incomes_id_seq', 1, false);


--
-- Name: intervals_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('intervals_id_seq', 1, false);


--
-- Name: payforwards_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('payforwards_id_seq', 1, false);


--
-- Name: rates_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('rates_id_seq', 1, false);


--
-- Name: transactions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('transactions_id_seq', 1, false);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: -
--

SELECT pg_catalog.setval('users_id_seq', 1, true);


--
-- Name: accounts accounts_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY accounts
    ADD CONSTRAINT accounts_pkey PRIMARY KEY (id);


--
-- Name: currency currency_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY currency
    ADD CONSTRAINT currency_pkey PRIMARY KEY (id);


--
-- Name: incomes incomes_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY incomes
    ADD CONSTRAINT incomes_pkey PRIMARY KEY (id);


--
-- Name: intervals intervals_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY intervals
    ADD CONSTRAINT intervals_pkey PRIMARY KEY (id);


--
-- Name: payforwards payforwards_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY payforwards
    ADD CONSTRAINT payforwards_pkey PRIMARY KEY (id);


--
-- Name: rates rates_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY rates
    ADD CONSTRAINT rates_pkey PRIMARY KEY (id);


--
-- Name: transactions transactions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY transactions
    ADD CONSTRAINT transactions_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: accounts accounts_currency_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY accounts
    ADD CONSTRAINT accounts_currency_id_fkey FOREIGN KEY (currency_id) REFERENCES currency(id);


--
-- Name: incomes incomes_currency_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY incomes
    ADD CONSTRAINT incomes_currency_id_fkey FOREIGN KEY (currency_id) REFERENCES currency(id);


--
-- Name: payforwards payforwards_income_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY payforwards
    ADD CONSTRAINT payforwards_income_id_fkey FOREIGN KEY (income_id) REFERENCES incomes(id);


--
-- Name: payforwards payforwards_transaction_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY payforwards
    ADD CONSTRAINT payforwards_transaction_id_fkey FOREIGN KEY (transaction_id) REFERENCES transactions(id);


--
-- Name: rates rates_currency_a_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY rates
    ADD CONSTRAINT rates_currency_a_fkey FOREIGN KEY (currency_a) REFERENCES currency(id);


--
-- Name: rates rates_currency_b_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY rates
    ADD CONSTRAINT rates_currency_b_fkey FOREIGN KEY (currency_b) REFERENCES currency(id);


--
-- Name: transactions transactions_account_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY transactions
    ADD CONSTRAINT transactions_account_id_fkey FOREIGN KEY (account_id) REFERENCES accounts(id);


--
-- Name: transactions transactions_income_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY transactions
    ADD CONSTRAINT transactions_income_id_fkey FOREIGN KEY (income_id) REFERENCES incomes(id);


--
-- Name: transactions transactions_transfer_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY transactions
    ADD CONSTRAINT transactions_transfer_fkey FOREIGN KEY (transfer) REFERENCES transactions(id);


--
-- Name: public; Type: ACL; Schema: -; Owner: -
--

GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- PostgreSQL database dump complete
--

