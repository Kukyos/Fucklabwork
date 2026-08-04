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

-- 1
INSERT INTO URK24CS1021_users (id, name, email, password, phone) VALUES
    (101, 'Alice Johnson', 'alice@mail.com', 'pass1', '9000000001'),
    (102, 'Bob Smith', 'bob@mail.com', 'pass2', '9000000002'),
    (103, 'Carol Lee', 'carol@mail.com', 'pass3', '9000000003'),
    (104, 'David Kim', 'david@mail.com', 'pass4', '9000000004'),
    (105, 'Emma Watson', 'emma@mail.com', 'pass5', '9000000005');
INSERT INTO URK24CS1021_location (venueid, name, address, city, state, country) VALUES
    (1, 'Madison Square Garden', '4 Pennsylvania Plaza', 'New York', 'NY', 'USA'),
    (2, 'Wembley Stadium', 'Wembley', 'London', 'England', 'UK'),
    (3, 'Marina Bay Sands', '10 Bayfront Ave', 'Singapore', 'Singapore', 'Singapore');
INSERT INTO URK24CS1021_event (eventid, name, eventdate, eventtime, venueid, description) VALUES
    (1, 'Rock Fest', '2023-08-15', '2023-08-15 19:00:00', 1, 'Outdoor rock concert'),
    (2, 'Tech Conference', '2023-07-20', '2023-07-20 09:00:00', 2, 'Annual tech meetup'),
    (3, 'Jazz Night', '2023-09-05', '2023-09-05 20:00:00', 3, 'Live jazz performance'),
    (4, 'Startup Summit', '2023-06-10', '2023-06-10 10:00:00', 1, 'Startup pitch day');
INSERT INTO URK24CS1021_ticket (ticketid, eventid, userid, price, status, barcode) VALUES
    (1, 1, 101, 150.00, 'confirmed', 'BC1001'),
    (2, 1, 102, 150.00, 'confirmed', 'BC1002'),
    (3, 2, 103, 200.00, 'cancelled', 'BC1003'),
    (4, 3, 104, 120.00, 'confirmed', 'BC1004'),
    (5, 3, 105, 120.00, 'confirmed', 'BC1005'),
    (6, 4, 101, 90.00, 'cancelled', 'BC1006'),
    (7, 2, 102, 200.00, 'confirmed', 'BC1007');

-- 2
SELECT * FROM URK24CS1021_users;
SELECT * FROM URK24CS1021_event;
SELECT * FROM URK24CS1021_location;
SELECT * FROM URK24CS1021_ticket;

-- 3
SELECT * FROM URK24CS1021_location ORDER BY city, country;

-- 4
SELECT COUNT(*) AS total_users FROM URK24CS1021_users;

-- 5
SELECT * FROM URK24CS1021_event ORDER BY eventdate DESC, eventtime DESC;

-- 6
SELECT eventid, AVG(price) AS avg_price
FROM URK24CS1021_ticket GROUP BY eventid;

-- 7
SELECT eventid, SUM(price) AS total_price, COUNT(*) AS ticket_count
FROM URK24CS1021_ticket GROUP BY eventid;

-- 8
SELECT eventid, COUNT(*) AS ticket_count
FROM URK24CS1021_ticket GROUP BY eventid;

-- 9
SELECT COUNT(DISTINCT id) AS distinct_users FROM URK24CS1021_users;

-- 10
SELECT * FROM URK24CS1021_event WHERE eventdate > '2023-07-30';

-- 11
SELECT SUM(price) AS confirmed_total
FROM URK24CS1021_ticket WHERE status = 'confirmed';

-- 12
SELECT name || ' <' || email || '>' AS display FROM URK24CS1021_users;

-- 13
SELECT * FROM URK24CS1021_location
WHERE city = 'New York' AND country = 'USA';

-- 14
SELECT city, country FROM URK24CS1021_location ORDER BY country ASC;

-- 15
DELETE FROM URK24CS1021_ticket WHERE status = 'cancelled';