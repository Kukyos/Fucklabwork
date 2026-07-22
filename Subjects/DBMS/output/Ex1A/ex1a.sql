-- 1
CREATE TABLE URK24CS1021_users (
    userid numeric(10) PRIMARY KEY,
    name varchar(255),
    email varchar(255),
    password varchar(255),
    phone varchar(20)
);
CREATE TABLE URK24CS1021_venue (
    venueid numeric(10) PRIMARY KEY,
    name varchar(255),
    address varchar(255),
    city varchar(255),
    state varchar(255),
    country varchar(255)
);
CREATE TABLE URK24CS1021_event (
    eventid numeric(10) PRIMARY KEY,
    name varchar(255),
    eventdate date,
    eventtime timestamp,
    venueid numeric(10),
    description varchar(500)
);
CREATE TABLE URK24CS1021_ticket (
    ticketid numeric(10) PRIMARY KEY,
    eventid numeric(10) REFERENCES URK24CS1021_event(eventid),
    userid numeric(10),
    seatnumber varchar(20),
    price numeric(10,2),
    status varchar(50)
);

-- 2
\d URK24CS1021_users
\d URK24CS1021_event
\d URK24CS1021_venue
\d URK24CS1021_ticket

-- 3
ALTER TABLE URK24CS1021_users ADD COLUMN age numeric(3);

-- 4
ALTER TABLE URK24CS1021_users DROP COLUMN age;

-- 5
ALTER TABLE URK24CS1021_venue RENAME TO URK24CS1021_location;

-- 6
ALTER TABLE URK24CS1021_event ALTER COLUMN description TYPE varchar(1000);

-- 7
ALTER TABLE URK24CS1021_ticket DROP COLUMN seatnumber;

-- 8
ALTER TABLE URK24CS1021_users ADD CONSTRAINT users_email_uq UNIQUE (email);

-- 9
ALTER TABLE URK24CS1021_users RENAME COLUMN userid TO id;

-- 10
ALTER TABLE URK24CS1021_ticket ADD COLUMN barcode varchar(50);

-- 11
ALTER TABLE URK24CS1021_location ALTER COLUMN name TYPE varchar(300);

-- 12
ALTER TABLE URK24CS1021_event ADD CONSTRAINT event_venue_fk
    FOREIGN KEY (venueid) REFERENCES URK24CS1021_location(venueid);

-- 13
ALTER TABLE URK24CS1021_users ADD CONSTRAINT users_id_chk CHECK (id BETWEEN 101 AND 105);

-- 14
ALTER TABLE URK24CS1021_users ADD CONSTRAINT users_phone_uq UNIQUE (phone);

-- 15
TRUNCATE TABLE URK24CS1021_users;