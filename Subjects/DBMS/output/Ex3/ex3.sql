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
ALTER TABLE URK24CS1021_event ADD COLUMN endtime timestamp;
ALTER TABLE URK24CS1021_ticket ADD COLUMN seatnumber varchar(20);
INSERT INTO URK24CS1021_users (id, name, email, password, phone) VALUES
    (101, 'Alice Johnson', 'alice@mail.com', 'pass1', '9000000001'),
    (102, 'Bob Smith', 'bob@mail.com', 'pass2', '9000000002'),
    (103, 'Carol Lee', 'carol@mail.com', 'pass3', '9000000003'),
    (104, 'David Kim', 'david@mail.com', 'pass4', '9000000004'),
    (105, 'Emma Watson', 'emma@mail.com', 'pass5', '9000000005');
INSERT INTO URK24CS1021_location (venueid, name, address, city, state, country) VALUES
    (1, 'Madison Square Garden', '4 Pennsylvania Plaza', 'New York', 'NY', 'USA'),
    (2, 'Wembley Stadium', 'Wembley', 'London', 'England', 'UK'),
    (3, 'Marina Bay Sands', '10 Bayfront Ave', 'Singapore', 'Singapore', 'Singapore'),
    (4, 'Chennai Trade Centre', 'Mount Poonamallee Rd', 'Chennai', 'Tamil Nadu', 'India');
INSERT INTO URK24CS1021_event (eventid, name, eventdate, eventtime, endtime, venueid, description) VALUES
    (1, 'Rock Fest', '2023-08-15', '2023-08-15 19:00:00', '2023-08-15 23:00:00', 1, 'Outdoor rock concert'),
    (2, 'Tech Conference', '2023-07-20', '2023-07-20 09:00:00', '2023-07-20 21:00:00', 2, 'Annual tech meetup'),
    (3, 'Jazz Night', '2023-09-05', '2023-09-05 20:00:00', '2023-09-05 23:30:00', 3, 'Live jazz performance'),
    (4, 'Startup Summit', '2023-06-10', '2023-06-10 10:00:00', '2023-06-10 18:30:00', 1, 'Startup pitch day'),
    (5, 'Book Fair', '2024-01-12', '2024-01-12 10:00:00', '2024-01-12 22:00:00', 4, 'National book fair');
INSERT INTO URK24CS1021_ticket (ticketid, eventid, userid, price, status, barcode, seatnumber) VALUES
    (1, 1, 101, 150.00, 'confirmed', 'BC1001', 'A12'),
    (2, 1, 102, 150.00, 'reserved',  'BC1002', 'A13'),
    (3, 2, 103, 200.00, 'cancelled', 'BC1003', 'B05'),
    (4, 3, 104, 120.00, 'confirmed', 'BC1004', 'C21'),
    (5, 3, 105,  25.00, 'confirmed', 'BC1005', 'C22'),
    (6, 4, 101,  90.00, 'reserved',  'BC1006', 'D07'),
    (7, 2, 102,  28.50, 'confirmed', 'BC1007', 'B06'),
    (8, 5, 103,  30.00, 'reserved',  'BC1008', 'E01');

-- 1
SELECT COUNT(*) AS total_users FROM URK24CS1021_users;

-- 2
SELECT COUNT(*) AS events_2023 FROM URK24CS1021_event
WHERE eventdate BETWEEN '2023-01-01' AND '2023-12-31';

-- 3
SELECT SUM(price) AS confirmed_total FROM URK24CS1021_ticket
WHERE status = 'confirmed';

-- 4
SELECT MIN(endtime - eventtime) AS min_duration,
       MAX(endtime - eventtime) AS max_duration,
       AVG(endtime - eventtime) AS avg_duration
FROM URK24CS1021_event;

-- 5
SELECT COUNT(DISTINCT userid) AS distinct_users FROM URK24CS1021_ticket;

-- 6
SELECT name, endtime - eventtime AS duration FROM URK24CS1021_event
WHERE endtime - eventtime > INTERVAL '10 hours';

-- 7
SELECT userid, seatnumber FROM URK24CS1021_ticket
WHERE status = 'confirmed' ORDER BY seatnumber;

-- 8
SELECT u.name, u.phone FROM URK24CS1021_users u, URK24CS1021_ticket t
WHERE u.id = t.userid AND t.status = 'reserved';

-- 9
SELECT u.id, u.name, u.email, u.phone, t.price
FROM URK24CS1021_users u, URK24CS1021_ticket t
WHERE u.id = t.userid ORDER BY t.price ASC;

-- 10
SELECT ticketid, price FROM URK24CS1021_ticket ORDER BY ticketid;
UPDATE URK24CS1021_ticket SET price = CASE
    WHEN price > 30 THEN price * 0.98
    ELSE price * 0.96
END;
SELECT ticketid, price FROM URK24CS1021_ticket ORDER BY ticketid;

-- 11
SELECT country, name, address FROM URK24CS1021_location
ORDER BY country, name;

-- 12
SELECT city FROM URK24CS1021_location ORDER BY city ASC;