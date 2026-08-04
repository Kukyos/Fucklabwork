-- setup (schema/data, not itself a graded question)
CREATE TABLE URK24CS1021_users (
    id numeric(10) PRIMARY KEY CHECK (id BETWEEN 101 AND 105),
    name varchar(255), email varchar(255) UNIQUE,
    password varchar(255), phone varchar(20) UNIQUE
);
CREATE TABLE URK24CS1021_location (
    venueid numeric(10) PRIMARY KEY, name varchar(300),
    address varchar(255), city varchar(255),
    state varchar(255), country varchar(255)
);
CREATE TABLE URK24CS1021_event (
    eventid numeric(10) PRIMARY KEY, name varchar(255),
    eventdate date, eventtime timestamp,
    venueid numeric(10) REFERENCES URK24CS1021_location(venueid),
    description varchar(1000)
);
CREATE TABLE URK24CS1021_ticket (
    ticketid numeric(10) PRIMARY KEY,
    eventid numeric(10) REFERENCES URK24CS1021_event(eventid),
    userid numeric(10), price numeric(10,2),
    status varchar(50), barcode varchar(50)
);
INSERT INTO URK24CS1021_users (id, name, email, password, phone) VALUES
    (101, 'John Carter', 'john.c@mail.com', 'pass1', '9000000010'),
    (102, 'Mary Ann', 'mary.ann@mail.com', 'pass2', '9000000011');
INSERT INTO URK24CS1021_location (venueid, name, address, city, state, country) VALUES
    (1, 'City Arena', '1 Main St', 'Chicago', 'IL', 'USA');
INSERT INTO URK24CS1021_event (eventid, name, eventdate, eventtime, venueid, description) VALUES
    (401, 'Comic Con', '2023-10-01', '2023-10-01 10:00:00', 1, 'Annual comic convention');
INSERT INTO URK24CS1021_ticket (ticketid, eventid, userid, price, status, barcode) VALUES
    (901, 401, 101, 100.00, 'confirmed', 'BCX001');

-- 1
INSERT INTO URK24CS1021_users (id, name, email, password, phone)
VALUES (103, 'Nina Patel', 'nina@mail.com', 'pass3', '9000000012');

-- 2
UPDATE URK24CS1021_users SET email = 'mary.ann.new@mail.com' WHERE id = 102;

-- 3
INSERT INTO URK24CS1021_users (id, name, email, password, phone)
VALUES (104, 'Temp User', 'example@example.com', 'pass4', '9000000013');
DELETE FROM URK24CS1021_users WHERE email = 'example@example.com';

-- 4
INSERT INTO URK24CS1021_event (eventid, name, eventdate, eventtime, venueid, description)
VALUES (402, 'Food Festival', '2023-11-05', '2023-11-05 12:00:00', 1, 'Street food festival');

-- 5
UPDATE URK24CS1021_event SET description = 'Annual comic convention, now with a cosplay contest'
WHERE eventid = 401;

-- 6
CREATE ROLE john LOGIN;
GRANT SELECT ON URK24CS1021_users TO john;

-- 7
CREATE ROLE mary LOGIN;
GRANT INSERT ON URK24CS1021_event TO mary;
REVOKE INSERT ON URK24CS1021_event FROM mary;

-- 8
CREATE ROLE jane LOGIN;
GRANT ALL PRIVILEGES ON URK24CS1021_ticket TO jane;

-- 9
CREATE ROLE admin;
CREATE OR REPLACE PROCEDURE URK24CS1021_ticket_count() LANGUAGE sql AS $$ SELECT 1; $$;
GRANT EXECUTE ON PROCEDURE URK24CS1021_ticket_count() TO admin;

-- 10
CREATE ROLE guest LOGIN;
REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM guest;

-- 11
BEGIN;
INSERT INTO URK24CS1021_ticket (ticketid, eventid, userid, price, status, barcode)
VALUES (902, 401, 102, 80.00, 'confirmed', 'BCX002');
COMMIT;

-- 12
BEGIN;
INSERT INTO URK24CS1021_ticket (ticketid, eventid, userid, price, status, barcode)
VALUES (903, 401, 103, 95.00, 'confirmed', 'BCX003');
SAVEPOINT sp1;
INSERT INTO URK24CS1021_ticket (ticketid, eventid, userid, price, status, barcode)
VALUES (904, 401, 104, 95.00, 'confirmed', 'BCX004');
ROLLBACK TO SAVEPOINT sp1;
COMMIT;
SELECT ticketid FROM URK24CS1021_ticket WHERE ticketid IN (903, 904);

-- 13
BEGIN;
INSERT INTO URK24CS1021_ticket (ticketid, eventid, userid, price, status, barcode)
VALUES (905, 401, 105, 70.00, 'confirmed', 'BCX005');
SAVEPOINT sp2;
SELECT COUNT(*) AS tickets_so_far FROM URK24CS1021_ticket;
COMMIT;

-- 14
\set AUTOCOMMIT on

-- 15
\set AUTOCOMMIT off