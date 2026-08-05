"""AutoLAB DBMS pipeline — run real SQL, capture real output, render clean
screenshots, drop a complete per-experiment output folder + filled record.

No pixel surgery, no hallucinated output: every screenshot is a real psql
session against the local PostgreSQL. Adding experiments 2..10 = append an
entry to EXPERIMENTS (a list of (question_no, [psql commands])).

    python Subjects/DBMS/dbms_lab.py 1a

Produces  Subjects/DBMS/output/Ex1A/
    ├─ ex1a.sql            (the script, as run)
    ├─ screenshots/q01.png … qNN.png   (real captures)
    └─ Ex1A_URK24CS1021.docx           (mam's template, filled)
"""
from __future__ import annotations

import io, os, subprocess, sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))
from docx import Document
from docx.enum.table import WD_ALIGN_VERTICAL, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_TAB_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Inches, Pt
from assemble import add_code_block
import labshot

HERE = Path(__file__).parent
MATERIALS = HERE / "materials"  # teacher-provided originals: templates, question PDFs/PPTX
URK = "URK24CS1021"
PSQL = r"C:\Program Files\PostgreSQL\17\bin\psql.exe"
DB, USER, HOST = "labdb", "postgres", "127.0.0.1"
PROMPT, CONT = f"{DB}=#", f"{DB}(#"
IMG_W = 6.4
COURSE = "23CS2014 Database Systems Lab"
FONT = "Times New Roman"

# --- experiment specs: (question_no, [command strings]) -------------------
# commands are exactly what a student types at psql (SQL or \d meta). Multi-
# line SQL keeps its line breaks so the render shows continuation prompts.
P = URK  # table-name prefix

EX1A = {
    "title": "Ex1A", "name": "CREATING AND MANAGING TABLES", "date": "08/07/2026",
    "aim": "To execute DDL commands and get the desired output.",
    "desc": ('DDL refers to "Data Definition Language", a subset of SQL statements '
             "that change the structure of the database schema in some way, "
             "typically by creating, deleting, or modifying schema objects such as "
             "databases, tables, and views. Most DDL statements start with the "
             "keywords CREATE, DROP, or ALTER."),
    # question text lives in the teacher's template (List Paragraph runs), not in
    # the (question_no, [commands]) tuples below -- copied out here so the record
    # builder has it without re-parsing the template.
    "qtext": [
        "Create User, Event, Venue, and ticket tables based on the given schema.",
        "Describe the tables.",
        "Alter the User table to add a new column Age.",
        "Drop the newly added column Age.",
        "Rename the Venue table to Location.",
        "Modify the size of the Event table's Description column to 1000.",
        "Drop the SeatNumber column from the Ticket table.",
        "Add a unique constraint on the Email column in the User table.",
        "Rename the UserID column in the User table to ID.",
        'Modify the Ticket table to add a column named "Barcode" with a data type of VARCHAR(50).',
        "Modify the Name column in the Venue table to increase its maximum length to VARCHAR(300).",
        "Add a foreign key constraint on the VenueID column in the Event table, referencing the Venue table.",
        "Add a CHECK constraint to check whether the UserID is between 101 and 105.",
        "Add a unique constraint to Phone column of the User table.",
        "Truncate the user table.",
    ],
    "reset": [f"{P}_users", f"{P}_venue", f"{P}_event", f"{P}_ticket", f"{P}_location"],
    "questions": [
        (1, [
            f"CREATE TABLE {P}_users (\n    userid numeric(10) PRIMARY KEY,\n    name varchar(255),\n    email varchar(255),\n    password varchar(255),\n    phone varchar(20)\n);",
            f"CREATE TABLE {P}_venue (\n    venueid numeric(10) PRIMARY KEY,\n    name varchar(255),\n    address varchar(255),\n    city varchar(255),\n    state varchar(255),\n    country varchar(255)\n);",
            f"CREATE TABLE {P}_event (\n    eventid numeric(10) PRIMARY KEY,\n    name varchar(255),\n    eventdate date,\n    eventtime timestamp,\n    venueid numeric(10),\n    description varchar(500)\n);",
            f"CREATE TABLE {P}_ticket (\n    ticketid numeric(10) PRIMARY KEY,\n    eventid numeric(10) REFERENCES {P}_event(eventid),\n    userid numeric(10),\n    seatnumber varchar(20),\n    price numeric(10,2),\n    status varchar(50)\n);",
        ]),
        (2, [f"\\d {P}_users", f"\\d {P}_event", f"\\d {P}_venue", f"\\d {P}_ticket"]),
        (3, [f"ALTER TABLE {P}_users ADD COLUMN age numeric(3);"]),
        (4, [f"ALTER TABLE {P}_users DROP COLUMN age;"]),
        (5, [f"ALTER TABLE {P}_venue RENAME TO {P}_location;"]),
        (6, [f"ALTER TABLE {P}_event ALTER COLUMN description TYPE varchar(1000);"]),
        (7, [f"ALTER TABLE {P}_ticket DROP COLUMN seatnumber;"]),
        (8, [f"ALTER TABLE {P}_users ADD CONSTRAINT users_email_uq UNIQUE (email);"]),
        (9, [f"ALTER TABLE {P}_users RENAME COLUMN userid TO id;"]),
        (10, [f"ALTER TABLE {P}_ticket ADD COLUMN barcode varchar(50);"]),
        (11, [f"ALTER TABLE {P}_location ALTER COLUMN name TYPE varchar(300);"]),
        (12, [f"ALTER TABLE {P}_event ADD CONSTRAINT event_venue_fk\n    FOREIGN KEY (venueid) REFERENCES {P}_location(venueid);"]),
        (13, [f"ALTER TABLE {P}_users ADD CONSTRAINT users_id_chk CHECK (id BETWEEN 101 AND 105);"]),
        (14, [f"ALTER TABLE {P}_users ADD CONSTRAINT users_phone_uq UNIQUE (phone);"]),
        (15, [f"TRUNCATE TABLE {P}_users;"]),
    ],
    "template_glob": "Ex. No. 1A*Creating and Managing Tables.docx",
}

# Ex1A leaves the schema mutated (venue->location, userid->id, seatnumber
# dropped, barcode added, + constraints). Later experiments need real rows to
# work with, so each recreates the 4 tables directly in that same final shape
# via TABLE_DDL (self-contained: doesn't depend on Ex1A having just been
# run); "reset" drops them first so reruns are clean.
TABLE_DDL = [
    f"CREATE TABLE {P}_users (\n"
    f"    id numeric(10) PRIMARY KEY CHECK (id BETWEEN 101 AND 105),\n"
    f"    name varchar(255), email varchar(255) UNIQUE,\n"
    f"    password varchar(255), phone varchar(20) UNIQUE\n);",
    f"CREATE TABLE {P}_location (\n"
    f"    venueid numeric(10) PRIMARY KEY, name varchar(300),\n"
    f"    address varchar(255), city varchar(255),\n"
    f"    state varchar(255), country varchar(255)\n);",
    f"CREATE TABLE {P}_event (\n"
    f"    eventid numeric(10) PRIMARY KEY, name varchar(255),\n"
    f"    eventdate date, eventtime timestamp,\n"
    f"    venueid numeric(10) REFERENCES {P}_location(venueid),\n"
    f"    description varchar(1000)\n);",
    f"CREATE TABLE {P}_ticket (\n"
    f"    ticketid numeric(10) PRIMARY KEY,\n"
    f"    eventid numeric(10) REFERENCES {P}_event(eventid),\n"
    f"    userid numeric(10), price numeric(10,2),\n"
    f"    status varchar(50), barcode varchar(50)\n);",
]

EX2 = {
    "title": "Ex2", "name": "BASIC SQL", "date": "24/07/2026",
    "reset": [f"{P}_users", f"{P}_location", f"{P}_event", f"{P}_ticket"],
    "setup": list(TABLE_DDL),
    "aim": "To execute the given basic SQL queries.",
    "desc": ("DML (Data Manipulation Language) statements manipulate the data held "
             "within tables: INSERT adds rows, UPDATE changes existing rows, DELETE "
             "removes rows, and SELECT retrieves rows, optionally filtered with a "
             "WHERE clause (comparison, AND/OR, IS NULL, IN, LIKE, BETWEEN), grouped "
             "with GROUP BY, and ordered with ORDER BY."),
    "questions": [
        (1, "Insert all the fields given in the ticket reservation schema.", [
            f"INSERT INTO {P}_users (id, name, email, password, phone) VALUES\n"
            f"    (101, 'Alice Johnson', 'alice@mail.com', 'pass1', '9000000001'),\n"
            f"    (102, 'Bob Smith', 'bob@mail.com', 'pass2', '9000000002'),\n"
            f"    (103, 'Carol Lee', 'carol@mail.com', 'pass3', '9000000003'),\n"
            f"    (104, 'David Kim', 'david@mail.com', 'pass4', '9000000004'),\n"
            f"    (105, 'Emma Watson', 'emma@mail.com', 'pass5', '9000000005');",
            f"INSERT INTO {P}_location (venueid, name, address, city, state, country) VALUES\n"
            f"    (1, 'Madison Square Garden', '4 Pennsylvania Plaza', 'New York', 'NY', 'USA'),\n"
            f"    (2, 'Wembley Stadium', 'Wembley', 'London', 'England', 'UK'),\n"
            f"    (3, 'Marina Bay Sands', '10 Bayfront Ave', 'Singapore', 'Singapore', 'Singapore');",
            f"INSERT INTO {P}_event (eventid, name, eventdate, eventtime, venueid, description) VALUES\n"
            f"    (1, 'Rock Fest', '2023-08-15', '2023-08-15 19:00:00', 1, 'Outdoor rock concert'),\n"
            f"    (2, 'Tech Conference', '2023-07-20', '2023-07-20 09:00:00', 2, 'Annual tech meetup'),\n"
            f"    (3, 'Jazz Night', '2023-09-05', '2023-09-05 20:00:00', 3, 'Live jazz performance'),\n"
            f"    (4, 'Startup Summit', '2023-06-10', '2023-06-10 10:00:00', 1, 'Startup pitch day');",
            f"INSERT INTO {P}_ticket (ticketid, eventid, userid, price, status, barcode) VALUES\n"
            f"    (1, 1, 101, 150.00, 'confirmed', 'BC1001'),\n"
            f"    (2, 1, 102, 150.00, 'confirmed', 'BC1002'),\n"
            f"    (3, 2, 103, 200.00, 'cancelled', 'BC1003'),\n"
            f"    (4, 3, 104, 120.00, 'confirmed', 'BC1004'),\n"
            f"    (5, 3, 105, 120.00, 'confirmed', 'BC1005'),\n"
            f"    (6, 4, 101, 90.00, 'cancelled', 'BC1006'),\n"
            f"    (7, 2, 102, 200.00, 'confirmed', 'BC1007');",
        ]),
        (2, "Display all the fields in User, Events, Venue and Ticket tables.", [
            f"SELECT * FROM {P}_users;", f"SELECT * FROM {P}_event;",
            f"SELECT * FROM {P}_location;", f"SELECT * FROM {P}_ticket;",
        ]),
        (3, "Retrieve all venues ordered by city and then by country.",
         [f"SELECT * FROM {P}_location ORDER BY city, country;"]),
        (4, "Retrieve total number of users.",
         [f"SELECT COUNT(*) AS total_users FROM {P}_users;"]),
        (5, "Retrieve all events ordered by date and time in descending order.",
         [f"SELECT * FROM {P}_event ORDER BY eventdate DESC, eventtime DESC;"]),
        (6, "Get the average price of tickets for each event.",
         [f"SELECT eventid, AVG(price) AS avg_price\nFROM {P}_ticket GROUP BY eventid;"]),
        (7, "Get the total price and count of tickets for each event.",
         [f"SELECT eventid, SUM(price) AS total_price, COUNT(*) AS ticket_count\n"
          f"FROM {P}_ticket GROUP BY eventid;"]),
        (8, "Count the number of tickets for each event.",
         [f"SELECT eventid, COUNT(*) AS ticket_count\nFROM {P}_ticket GROUP BY eventid;"]),
        (9, "Retrieve a distinct number of users.",
         [f"SELECT COUNT(DISTINCT id) AS distinct_users FROM {P}_users;"]),
        (10, "Retrieve the events conducted after 30/07/2023.",
         [f"SELECT * FROM {P}_event WHERE eventdate > '2023-07-30';"]),
        (11, "Calculate the sum of prices for all confirmed tickets.",
         [f"SELECT SUM(price) AS confirmed_total\nFROM {P}_ticket WHERE status = 'confirmed';"]),
        (12, "Concatenate the user's name and email for display.",
         [f"SELECT name || ' <' || email || '>' AS display FROM {P}_users;"]),
        (13, "Retrieve the venue from the city New York and country USA.",
         [f"SELECT * FROM {P}_location\nWHERE city = 'New York' AND country = 'USA';"]),
        (14, "Retrieve all cities ordered by Country in ascending order.",
         [f"SELECT city, country FROM {P}_location ORDER BY country ASC;"]),
        (15, "Delete the cancelled ticket in the ticket table.",
         [f"DELETE FROM {P}_ticket WHERE status = 'cancelled';"]),
    ],
}

# Ex1B: no docx/PDF template was ever given for this one (materials/ only has
# reference PPTX slides) and Cleo confirmed the teacher never handed out a
# fixed record format for it either -- she mainly wants clean, real
# screenshots. So: from-scratch record like Exp2, but kept minimal; the
# effort goes into correct SQL, not record polish.
#
# The guideline's own placeholder values ("UserID 123", "EventID 456") don't
# fit our schema (users.id is CHECK'd to 101-105) -- adapted to real seeded
# ids instead of forcing 123/456 to exist. TCL questions (11-13) need
# transaction state (BEGIN/SAVEPOINT/COMMIT) to survive across statements,
# which only holds within one psql connection -- so each of those is passed
# as ONE multi-statement command string (one psql() call = one session),
# not a list of separate commands like everywhere else.
EX1B = {
    "title": "Ex1B", "name": "MANAGING TABLES USING DML, DCL AND TCL COMMANDS",
    "date": "24/07/2026",
    "reset": [f"{P}_users", f"{P}_location", f"{P}_event", f"{P}_ticket"],
    "setup": TABLE_DDL + [
        f"INSERT INTO {P}_users (id, name, email, password, phone) VALUES\n"
        f"    (101, 'John Carter', 'john.c@mail.com', 'pass1', '9000000010'),\n"
        f"    (102, 'Mary Ann', 'mary.ann@mail.com', 'pass2', '9000000011');",
        f"INSERT INTO {P}_location (venueid, name, address, city, state, country) VALUES\n"
        f"    (1, 'City Arena', '1 Main St', 'Chicago', 'IL', 'USA');",
        f"INSERT INTO {P}_event (eventid, name, eventdate, eventtime, venueid, description) VALUES\n"
        f"    (401, 'Comic Con', '2023-10-01', '2023-10-01 10:00:00', 1, 'Annual comic convention');",
        f"INSERT INTO {P}_ticket (ticketid, eventid, userid, price, status, barcode) VALUES\n"
        f"    (901, 401, 101, 100.00, 'confirmed', 'BCX001');",
    ],
    "aim": "To execute all commands of Data Manipulation Language, Data Control "
           "Language, and Transaction Control Language to get the desired output.",
    "desc": ("DML statements (INSERT/UPDATE/DELETE) manipulate row data. DCL "
             "statements (GRANT/REVOKE) control access privileges on database "
             "objects for specific roles. TCL statements (COMMIT/ROLLBACK/"
             "SAVEPOINT) control transaction boundaries — COMMIT makes changes "
             "permanent, SAVEPOINT marks a point to roll back to within an open "
             "transaction, and ROLLBACK TO undoes work back to that point without "
             "discarding the whole transaction."),
    "questions": [
        (1, 'Insert a new user into the "User" table.',
         [f"INSERT INTO {P}_users (id, name, email, password, phone)\n"
          f"VALUES (103, 'Nina Patel', 'nina@mail.com', 'pass3', '9000000012');"]),
        (2, "Update the email address of a user with UserID 102.",
         [f"UPDATE {P}_users SET email = 'mary.ann.new@mail.com' WHERE id = 102;"]),
        (3, 'Delete a user with the email "example@example.com".',
         [f"INSERT INTO {P}_users (id, name, email, password, phone)\n"
          f"VALUES (104, 'Temp User', 'example@example.com', 'pass4', '9000000013');",
          f"DELETE FROM {P}_users WHERE email = 'example@example.com';"]),
        (4, 'Insert a new event into the "Event" table.',
         [f"INSERT INTO {P}_event (eventid, name, eventdate, eventtime, venueid, description)\n"
          f"VALUES (402, 'Food Festival', '2023-11-05', '2023-11-05 12:00:00', 1, 'Street food festival');"]),
        (5, "Update the description of an event with EventID 401.",
         [f"UPDATE {P}_event SET description = 'Annual comic convention, now with a cosplay contest'\n"
          f"WHERE eventid = 401;"]),
        (6, 'Grant SELECT privileges on the "User" table to a user named "john".',
         [f"CREATE ROLE john LOGIN;", f"GRANT SELECT ON {P}_users TO john;"]),
        (7, 'Revoke INSERT privileges on the "Event" table from a user named "mary".',
         [f"CREATE ROLE mary LOGIN;", f"GRANT INSERT ON {P}_event TO mary;",
          f"REVOKE INSERT ON {P}_event FROM mary;"]),
        (8, 'Create a new user with the username "jane" and grant them all '
            'privileges on the "Ticket" table.',
         [f"CREATE ROLE jane LOGIN;", f"GRANT ALL PRIVILEGES ON {P}_ticket TO jane;"]),
        (9, "Grant EXECUTE privileges on a stored procedure to a role named \"admin\".",
         [f"CREATE ROLE admin;",
          f"CREATE OR REPLACE PROCEDURE {P}_ticket_count() LANGUAGE sql AS $$ SELECT 1; $$;",
          f"GRANT EXECUTE ON PROCEDURE {P}_ticket_count() TO admin;"]),
        (10, "Revoke all privileges from a user named \"guest\" on all tables in the schema.",
         [f"CREATE ROLE guest LOGIN;",
          f"REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM guest;"]),
        (11, "Perform commit a transaction in the database.",
         [f"BEGIN;\n"
          f"INSERT INTO {P}_ticket (ticketid, eventid, userid, price, status, barcode)\n"
          f"VALUES (902, 401, 102, 80.00, 'confirmed', 'BCX002');\n"
          f"COMMIT;"]),
        (12, "Perform roll back a transaction to a specific savepoint.",
         [f"BEGIN;\n"
          f"INSERT INTO {P}_ticket (ticketid, eventid, userid, price, status, barcode)\n"
          f"VALUES (903, 401, 103, 95.00, 'confirmed', 'BCX003');\n"
          f"SAVEPOINT sp1;\n"
          f"INSERT INTO {P}_ticket (ticketid, eventid, userid, price, status, barcode)\n"
          f"VALUES (904, 401, 104, 95.00, 'confirmed', 'BCX004');\n"
          f"ROLLBACK TO SAVEPOINT sp1;\n"
          f"COMMIT;\n"
          f"SELECT ticketid FROM {P}_ticket WHERE ticketid IN (903, 904);"]),
        (13, "Perform set a savepoint within a transaction.",
         [f"BEGIN;\n"
          f"INSERT INTO {P}_ticket (ticketid, eventid, userid, price, status, barcode)\n"
          f"VALUES (905, 401, 105, 70.00, 'confirmed', 'BCX005');\n"
          f"SAVEPOINT sp2;\n"
          f"SELECT COUNT(*) AS tickets_so_far FROM {P}_ticket;\n"
          f"COMMIT;"]),
        (14, "Enable autocommit mode in the database.", ["\\set AUTOCOMMIT on"]),
        (15, "Disable autocommit mode in the database.", ["\\set AUTOCOMMIT off"]),
    ],
}

# Exp3: the question set assumes two columns Ex1A had removed/never added --
# ticket.seatnumber (Q7; Ex1A Q7 dropped it) and an event end time (Q4/Q6 ask
# for "time taken" and events "more than 10 hours", which the base schema
# cannot express). Setup restores them with visible ALTERs rather than
# fudging the questions. The seed is chosen so each query actually
# discriminates: one 2024 event (so Q2's 2023 count means something), three
# 'reserved' tickets (Q8), and three tickets priced <= 30 (so Q10's 4% branch
# fires alongside the 2% one).
EX3 = {
    "title": "Ex3", "name": "ADVANCED SQL", "date": "05/08/2026", "strict": True,
    "reset": [f"{P}_users", f"{P}_location", f"{P}_event", f"{P}_ticket"],
    "setup": TABLE_DDL + [
        f"ALTER TABLE {P}_event ADD COLUMN endtime timestamp;",
        f"ALTER TABLE {P}_ticket ADD COLUMN seatnumber varchar(20);",
        f"INSERT INTO {P}_users (id, name, email, password, phone) VALUES\n"
        f"    (101, 'Alice Johnson', 'alice@mail.com', 'pass1', '9000000001'),\n"
        f"    (102, 'Bob Smith', 'bob@mail.com', 'pass2', '9000000002'),\n"
        f"    (103, 'Carol Lee', 'carol@mail.com', 'pass3', '9000000003'),\n"
        f"    (104, 'David Kim', 'david@mail.com', 'pass4', '9000000004'),\n"
        f"    (105, 'Emma Watson', 'emma@mail.com', 'pass5', '9000000005');",
        f"INSERT INTO {P}_location (venueid, name, address, city, state, country) VALUES\n"
        f"    (1, 'Madison Square Garden', '4 Pennsylvania Plaza', 'New York', 'NY', 'USA'),\n"
        f"    (2, 'Wembley Stadium', 'Wembley', 'London', 'England', 'UK'),\n"
        f"    (3, 'Marina Bay Sands', '10 Bayfront Ave', 'Singapore', 'Singapore', 'Singapore'),\n"
        f"    (4, 'Chennai Trade Centre', 'Mount Poonamallee Rd', 'Chennai', 'Tamil Nadu', 'India');",
        f"INSERT INTO {P}_event (eventid, name, eventdate, eventtime, endtime, venueid, description) VALUES\n"
        f"    (1, 'Rock Fest', '2023-08-15', '2023-08-15 19:00:00', '2023-08-15 23:00:00', 1, 'Outdoor rock concert'),\n"
        f"    (2, 'Tech Conference', '2023-07-20', '2023-07-20 09:00:00', '2023-07-20 21:00:00', 2, 'Annual tech meetup'),\n"
        f"    (3, 'Jazz Night', '2023-09-05', '2023-09-05 20:00:00', '2023-09-05 23:30:00', 3, 'Live jazz performance'),\n"
        f"    (4, 'Startup Summit', '2023-06-10', '2023-06-10 10:00:00', '2023-06-10 18:30:00', 1, 'Startup pitch day'),\n"
        f"    (5, 'Book Fair', '2024-01-12', '2024-01-12 10:00:00', '2024-01-12 22:00:00', 4, 'National book fair');",
        f"INSERT INTO {P}_ticket (ticketid, eventid, userid, price, status, barcode, seatnumber) VALUES\n"
        f"    (1, 1, 101, 150.00, 'confirmed', 'BC1001', 'A12'),\n"
        f"    (2, 1, 102, 150.00, 'reserved',  'BC1002', 'A13'),\n"
        f"    (3, 2, 103, 200.00, 'cancelled', 'BC1003', 'B05'),\n"
        f"    (4, 3, 104, 120.00, 'confirmed', 'BC1004', 'C21'),\n"
        f"    (5, 3, 105,  25.00, 'confirmed', 'BC1005', 'C22'),\n"
        f"    (6, 4, 101,  90.00, 'reserved',  'BC1006', 'D07'),\n"
        f"    (7, 2, 102,  28.50, 'confirmed', 'BC1007', 'B06'),\n"
        f"    (8, 5, 103,  30.00, 'reserved',  'BC1008', 'E01');",
    ],
    "aim": "To execute the given commands making use of aggregate functions, "
           "group by clause and order by clause.",
    "desc": ("Aggregate functions take a collection of values and return a single "
             "value as the result: SUM returns the total, AVG the average, COUNT "
             "the number of tuples, and MIN and MAX the smallest and largest value "
             "in the collection. SUM and AVG need numeric input, while COUNT, MIN "
             "and MAX also work on non-numeric types. The DISTINCT keyword inside "
             "an aggregate expression eliminates duplicates before the function is "
             "applied. The GROUP BY clause applies an aggregate function to groups "
             "of tuples — tuples sharing the same value on every attribute named in "
             "the clause are placed in one group — and the ORDER BY clause returns "
             "the result of a query in sorted order, ASC for ascending and DESC for "
             "descending."),
    "questions": [
        (1, "List the number of users in the user table.",
         [f"SELECT COUNT(*) AS total_users FROM {P}_users;"]),
        (2, "List the number of events conducted during 2023.",
         [f"SELECT COUNT(*) AS events_2023 FROM {P}_event\n"
          f"WHERE eventdate BETWEEN '2023-01-01' AND '2023-12-31';"]),
        (3, "Calculate the total price for the confirmed tickets.",
         [f"SELECT SUM(price) AS confirmed_total FROM {P}_ticket\n"
          f"WHERE status = 'confirmed';"]),
        (4, "Find the minimum, maximum and average time taken for the given events.",
         [f"SELECT MIN(endtime - eventtime) AS min_duration,\n"
          f"       MAX(endtime - eventtime) AS max_duration,\n"
          f"       AVG(endtime - eventtime) AS avg_duration\n"
          f"FROM {P}_event;"]),
        (5, "Retrieve distinct number of users.",
         [f"SELECT COUNT(DISTINCT userid) AS distinct_users FROM {P}_ticket;"]),
        (6, "List names of events was more than 10 hours.",
         [f"SELECT name, endtime - eventtime AS duration FROM {P}_event\n"
          f"WHERE endtime - eventtime > INTERVAL '10 hours';"]),
        (7, "List the seat numbers of the users those whose tickets are confirmed.",
         [f"SELECT userid, seatnumber FROM {P}_ticket\n"
          f"WHERE status = 'confirmed' ORDER BY seatnumber;"]),
        (8, "List user name and phone numbers those whose tickets reserved.",
         [f"SELECT u.name, u.phone FROM {P}_users u, {P}_ticket t\n"
          f"WHERE u.id = t.userid AND t.status = 'reserved';"]),
        (9, "List the user details in the ascending order of their ticket price.",
         [f"SELECT u.id, u.name, u.email, u.phone, t.price\n"
          f"FROM {P}_users u, {P}_ticket t\n"
          f"WHERE u.id = t.userid ORDER BY t.price ASC;"]),
        (10, "Modify the ticket price of the user based on the following: "
             "(a) if the price is greater than 30, give a concession of 2%; "
             "(b) if the price is lesser than or equal to 30, give a concession of 4%.",
         [f"SELECT ticketid, price FROM {P}_ticket ORDER BY ticketid;",
          f"UPDATE {P}_ticket SET price = CASE\n"
          f"    WHEN price > 30 THEN price * 0.98\n"
          f"    ELSE price * 0.96\n"
          f"END;",
          f"SELECT ticketid, price FROM {P}_ticket ORDER BY ticketid;"]),
        (11, "List the Venue name and address in each country.",
         [f"SELECT country, name, address FROM {P}_location\n"
          f"ORDER BY country, name;"]),
        (12, "List all the city name in Alphabetical order.",
         [f"SELECT city FROM {P}_location ORDER BY city ASC;"]),
    ],
}

EXPERIMENTS = {"1a": EX1A, "2": EX2, "1b": EX1B, "3": EX3}


def psql(cmd: str) -> str:
    env = {**os.environ, "PGPASSWORD": "postgres"}
    r = subprocess.run([PSQL, "-U", USER, "-h", HOST, "-d", DB, "-c", cmd],
                       capture_output=True, text=True, env=env)
    return (r.stdout + r.stderr).rstrip("\n")


def format_cmd(cmd: str, out: str) -> list[str]:
    cl = cmd.strip("\n").split("\n")
    lines = [f"{PROMPT} {cl[0]}"] + [f"{CONT} {c}" for c in cl[1:]]
    if out:
        lines += out.split("\n")
    return lines


def code_text(commands: list[str]) -> str:
    """The queries of one question as they belong in a record, not a transcript."""
    return "\n".join(c.rstrip(";") + (";" if not c.startswith("\\") else "")
                     for c in commands)


def run_question(commands: list[str]) -> tuple[str, bytes, str]:
    """Execute all commands of one question; return (code, screenshot, output)."""
    transcript: list[str] = []
    outputs: list[str] = []
    for c in commands:
        out = psql(c)
        outputs.append(out)
        transcript += format_cmd(c, out)
        transcript.append("")
    transcript.append(PROMPT)                       # trailing cursor prompt
    png = labshot.render_console_text("\n".join(transcript),
                                      title=f"psql — {DB}")
    return code_text(commands), png, "\n".join(outputs)


def fill_docx(spec: dict, results: list[tuple[str, bytes]], out_path: Path) -> None:
    tmpl = next(MATERIALS.glob(spec["template_glob"]))
    doc = Document(str(tmpl))
    hp = doc.sections[0].header.paragraphs[0]
    hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    hp.add_run(URK).bold = True
    title = next(p for p in doc.paragraphs if p.style.name == "Heading 1")
    dp = title.insert_paragraph_before(); title._p.addnext(dp._p)
    dp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r = dp.add_run(f"Date: {spec['date']}"); r.bold = True; r.font.size = Pt(12)
    for p in list(doc.paragraphs):
        t = p.text.strip()
        if t in ("<Query>", "<Output screenshot>"):
            p._p.getparent().remove(p._p)
        elif p.style.name in ("List Paragraph", "Body Text") and not t:
            p._p.getparent().remove(p._p)
    qs = [p for p in doc.paragraphs if p.style.name == "List Paragraph" and p.text.strip()]
    assert len(qs) == len(results), (len(qs), len(results))
    for q, (code, png) in zip(qs, results):
        q.paragraph_format.keep_with_next = True
        marker = len(doc.paragraphs)
        add_code_block(doc, code)
        ip = doc.add_paragraph(); ip.alignment = WD_ALIGN_PARAGRAPH.CENTER
        ip.paragraph_format.space_after = Pt(10)
        ip.add_run().add_picture(io.BytesIO(png), width=Inches(IMG_W))
        cp = doc.paragraphs[marker]
        q._p.addnext(ip._p); q._p.addnext(cp._p)
    res = next((p for p in doc.paragraphs if p.text.strip().startswith("Result")), None)
    if res:
        res.runs[0].bold = True
        s = res.insert_paragraph_before(); res._p.addnext(s._p)
        s.add_run("The DDL commands were executed and the desired output was obtained.")
    doc.save(str(out_path))


# ---- from-scratch docx (used when there's no editable teacher template,
# e.g. Exp2 only has a question-set PDF) — same layout conventions as the
# DSE from-scratch builders: header/footer, Ex.No/title table, Aim/
# Description/Question, then one code+screenshot pair per question.
def _rfonts(el, name=FONT):
    rpr = el.get_or_add_rPr()
    rf = rpr.find(qn("w:rFonts"))
    if rf is None:
        rf = OxmlElement("w:rFonts"); rpr.insert(0, rf)
    for a in ("w:ascii", "w:hAnsi", "w:cs"):
        rf.set(qn(a), name)


def _cell_border(cell):
    pr = cell._tc.get_or_add_tcPr()
    b = OxmlElement("w:tcBorders")
    for s in ("top", "left", "bottom", "right"):
        e = OxmlElement(f"w:{s}")
        e.set(qn("w:val"), "single"); e.set(qn("w:sz"), "6")
        e.set(qn("w:space"), "0"); e.set(qn("w:color"), "000000")
        b.append(e)
    pr.append(b)


def _label(doc, text, size=12, space_before=8):
    p = doc.add_paragraph()
    r = p.add_run(text); r.bold = True; r.font.name = FONT; r.font.size = Pt(size)
    p.paragraph_format.space_before = Pt(space_before)
    p.paragraph_format.space_after = Pt(3)
    return p


def _body(doc, text, italic=False):
    p = doc.add_paragraph()
    r = p.add_run(text); r.font.name = FONT; r.font.size = Pt(12); r.italic = italic
    p.paragraph_format.space_after = Pt(4)
    return p


def build_docx_scratch(spec: dict, results: list[tuple[str, str, bytes]], out_path: Path) -> None:
    title = spec["title"].upper()
    doc = Document()
    normal = doc.styles["Normal"]; normal.font.name = FONT; normal.font.size = Pt(12)
    _rfonts(normal.element)
    sec = doc.sections[0]
    sec.page_height, sec.page_width = Cm(29.7), Cm(21.0)
    for m in ("top_margin", "bottom_margin", "left_margin", "right_margin"):
        setattr(sec, m, Inches(1.0))

    h = sec.header.paragraphs[0]
    h.paragraph_format.tab_stops.add_tab_stop(Cm(15.9), WD_TAB_ALIGNMENT.RIGHT)
    r = h.add_run(COURSE); r.bold = True
    h.add_run("\t"); r2 = h.add_run(URK); r2.bold = True
    pbdr = h._p.get_or_add_pPr()
    bd = OxmlElement("w:pBdr"); bot = OxmlElement("w:bottom")
    bot.set(qn("w:val"), "single"); bot.set(qn("w:sz"), "12")
    bot.set(qn("w:space"), "1"); bot.set(qn("w:color"), "000000")
    bd.append(bot); pbdr.append(bd)
    f = sec.footer.paragraphs[0]; f.alignment = WD_ALIGN_PARAGRAPH.CENTER
    fr = f.add_run(f"{title}: {spec['name']}"); fr.bold = True

    t = doc.add_table(rows=2, cols=2); t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    rows = [(f"Ex. No. {spec['title'][2:]}", spec["name"]), ("Date of Exercise", spec["date"])]
    widths = (Inches(1.9), Inches(4.35))
    for ri, (a, b) in enumerate(rows):
        for ci, txt in enumerate((a, b)):
            c = t.rows[ri].cells[ci]; c.width = widths[ci]
            c.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            p = c.paragraphs[0]
            if ri == 0:
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            cr = p.add_run(txt); cr.font.name = FONT; cr.font.size = Pt(12)
            cr.bold = (ci == 0 or ri == 0)
            _cell_border(c)
    doc.add_paragraph()

    _label(doc, "Aim"); _body(doc, spec["aim"])
    _label(doc, "Description"); _body(doc, spec["desc"])

    for n, qtext, code, png in results:
        _label(doc, f"{n}. {qtext}")
        _label(doc, "Sample Code:", size=12, space_before=2)
        add_code_block(doc, code)
        _label(doc, "Sample Output:", size=12, space_before=2)
        p = doc.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(8)
        p.add_run().add_picture(io.BytesIO(png), width=Inches(IMG_W))

    _label(doc, "RESULT")
    _body(doc, "The SQL queries were executed and the desired output was obtained.")
    doc.save(str(out_path))


# ---- record (mam's "dbms Record Template.docx") --------------------------
# A different artefact from the output docx above: one 2x3 table, header row
# = Ex No/Date | Title | Register Number, and a single merged body cell that
# holds Aim / Description / Questions / Result. Everything below the header
# goes INSIDE that one cell -- python-docx cells duck-type as documents for
# add_paragraph, so assemble.add_code_block works on them unchanged.
RECORD_GLOB = "*Record Template.docx"   # NB: the shipped filename has a double space
REC_IMG_W = 6.3                         # body cell is 9776-216 twips = 6.64" wide


def _clear_cell(cell):
    for p in list(cell.paragraphs):
        p._p.getparent().remove(p._p)
    return cell


def _cell_para(cell, text, *, bold=False, size=12, center=False, space_after=4):
    p = cell.add_paragraph()
    if center:
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(space_after)
    r = p.add_run(text); r.bold = bold
    r.font.name = FONT; r.font.size = Pt(size)
    return p


def build_record(spec: dict, results: list[tuple], out_path: Path) -> None:
    """results: [(n, question_text, code, png_bytes)]"""
    doc = Document(str(next(MATERIALS.glob(RECORD_GLOB))))
    t = doc.tables[0]
    head = t.rows[0].cells
    for cell, lines in zip(head, (
            [f"Ex. No. {spec['title'][2:]}", f"Date: {spec['date']}"],
            [spec["name"]],          # kept upper-case: .title() mangles SQL/DML/DCL
            [URK])):
        _clear_cell(cell)
        cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
        for line in lines:
            _cell_para(cell, line, bold=True, size=14 if cell is head[1] else 12,
                       center=True, space_after=2)

    body = _clear_cell(t.rows[1].cells[0])
    _cell_para(body, "Aim", bold=True, size=14, space_after=2)
    _cell_para(body, spec["aim"], space_after=10)
    _cell_para(body, "Description", bold=True, size=14, space_after=2)
    _cell_para(body, spec["desc"], space_after=10)
    _cell_para(body, "Questions", bold=True, size=14, space_after=6)
    for n, qtext, code, png in results:
        q = _cell_para(body, f"{n}. {qtext}", bold=True, space_after=3)
        q.paragraph_format.keep_with_next = True
        add_code_block(body, code)
        p = body.add_paragraph(); p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(10)
        p.add_run().add_picture(io.BytesIO(png), width=Inches(REC_IMG_W))
    _cell_para(body, "Result", bold=True, size=14, space_after=2)
    _cell_para(body, "The queries were executed and the desired output was obtained.")
    doc.save(str(out_path))


def to_pdf(paths: list[Path]) -> None:
    """docx -> pdf through the installed Word. One instance for the whole batch."""
    import win32com.client as win32
    word = win32.DispatchEx("Word.Application")   # DispatchEx: own instance, so an
    word.Visible = False                          # already-open Word isn't hijacked
    word.DisplayAlerts = 0
    try:
        for p in paths:
            src = p.resolve()                     # COM needs absolute paths
            d = word.Documents.Open(str(src), ReadOnly=True, AddToRecentFiles=False)
            d.SaveAs2(str(src.with_suffix(".pdf")), FileFormat=17)  # 17 = wdFormatPDF
            d.Close(False)
    finally:
        word.Quit()


def results_from_disk(spec: dict) -> list[tuple]:
    """Rebuild (n, qtext, code, png) from the spec + already-captured shots, so a
    record can be made without re-running (and re-dropping) the database."""
    shots = HERE / "output" / spec["title"] / "screenshots"
    qtext = spec.get("qtext")
    out = []
    for i, entry in enumerate(spec["questions"]):
        n, text, cmds = entry if len(entry) == 3 else (entry[0], qtext[i], entry[1])
        out.append((n, text, code_text(cmds), (shots / f"q{n:02d}.png").read_bytes()))
    return out


def write_commands(spec: dict, out_path: Path) -> None:
    """Plain-text log of what was typed at the prompt, question text included."""
    lines = [f"-- {spec['title']}: {spec['name']} — {URK}",
             f"-- {COURSE} — {spec['date']}",
             f"-- commands typed at the psql prompt ({DB}), in order", ""]
    if spec.get("setup"):
        lines += ["-- setup: schema and seed data (not one of the graded questions)"]
        lines += spec["setup"] + [""]
    qtext = spec.get("qtext")
    for i, entry in enumerate(spec["questions"]):
        n, text, cmds = entry if len(entry) == 3 else (entry[0], qtext[i], entry[1])
        lines += [f"-- Q{n}. {text}"] + list(cmds) + [""]
    out_path.write_text("\n".join(lines), encoding="utf8")


def build(exp_key: str) -> Path:
    spec = EXPERIMENTS[exp_key]
    for t in spec["reset"]:
        psql(f"DROP TABLE IF EXISTS {t} CASCADE;")
    for cmd in spec.get("setup", []):
        psql(cmd)  # silent schema/data setup, not one of the graded questions

    outdir = HERE / "output" / spec["title"]
    shots = outdir / "screenshots"; shots.mkdir(parents=True, exist_ok=True)
    results, sql_lines = [], []
    if spec.get("setup"):
        sql_lines.append("-- setup (schema/data, not itself a graded question)\n"
                          + "\n".join(spec["setup"]))
    has_qtext = len(spec["questions"][0]) == 3
    for entry in spec["questions"]:
        n, qtext, cmds = entry if has_qtext else (entry[0], None, entry[1])
        code, png, out = run_question(cmds)
        # cheap guard against the silent all-or-nothing INSERT failure that bit
        # Exp2 -- a query answering nothing is as wrong as one that errors.
        if spec.get("strict"):
            assert "ERROR" not in out, f"Q{n} errored:\n{out}"
            assert "(0 rows)" not in out, f"Q{n} returned no rows:\n{out}"
        (shots / f"q{n:02d}.png").write_bytes(png)
        results.append((n, qtext, code, png) if has_qtext else (code, png))
        sql_lines.append(f"-- {n}\n" + "\n".join(cmds))
    (outdir / f"{spec['title'].lower()}.sql").write_text(
        "\n\n".join(sql_lines), encoding="utf8")
    write_commands(spec, outdir / f"{spec['title'].lower()}_commands.txt")

    docx_path = outdir / f"{spec['title']}_{URK}.docx"
    if "template_glob" in spec:
        fill_docx(spec, results, docx_path)
    else:
        build_docx_scratch(spec, results, docx_path)
    rec_path = build_record_for(spec)
    to_pdf([docx_path, rec_path])
    print("wrote", outdir)
    print("  screenshots:", len(results), "| docx+pdf:", docx_path.name)
    print("  record:", rec_path)
    return outdir


def build_record_for(spec: dict) -> Path:
    """Record only -- reuses the screenshots already on disk, touches no DB."""
    recdir = HERE / "records" / spec["title"]; recdir.mkdir(parents=True, exist_ok=True)
    path = recdir / f"{spec['title']}_Record_{URK}.docx"
    build_record(spec, results_from_disk(spec), path)
    return path


if __name__ == "__main__":
    a = sys.argv[1:] or ["1a"]
    if a[0] == "docs":
        # dbms_lab.py docs 1a 1b 2 -- record, commands.txt and both PDFs from the
        # screenshots already on disk. Touches no database, so an experiment built
        # earlier isn't re-run (build() drops its tables).
        paths = []
        for k in a[1:]:
            spec = EXPERIMENTS[k]
            outdir = HERE / "output" / spec["title"]
            write_commands(spec, outdir / f"{spec['title'].lower()}_commands.txt")
            paths += [outdir / f"{spec['title']}_{URK}.docx", build_record_for(spec)]
        to_pdf(paths)
        for p in paths:
            print("wrote", p.with_suffix(".pdf"))
    else:
        build(a[0])
