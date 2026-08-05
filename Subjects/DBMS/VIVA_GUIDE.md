# DBMS Lab — Viva Guide
**23CS2014 Database Systems Lab · A M Armaan · URK24CS1021**

Covers Ex1(a), Ex1(b), Ex2 and Ex3 — every keyword you actually ran, how to open and
drive the database live, and how to explain every mark on your screenshots.

---

## 0. Read this first — the flavour question

Your screenshots say `labdb=#`. The teacher's sample output says `SQL>`. She will notice.

> **The answer:** "The lab reference is Oracle SQL\*Plus, but Oracle XE isn't installable on my
> laptop, so I ran the same queries on a real PostgreSQL 17 server locally. Every screenshot is
> genuine, unedited output from that server. The SQL is standard SQL — only a few dialect
> details differ, like `VARCHAR2` becoming `varchar` and `DESC table` becoming `\d table`."

Do not apologise for it and do not call it "the same thing". It is real output from a real
RDBMS, which is exactly what the exercise asks for. Section 9 has the dialect table if she
pushes further.

---

## 1. Opening the database

### PostgreSQL — what your screenshots show

```
psql -U postgres -d labdb
```

| Piece | Meaning |
|---|---|
| `psql` | The PostgreSQL command-line client |
| `-U postgres` | Connect as user (role) `postgres` |
| `-d labdb` | Connect to database `labdb` |
| `-h 127.0.0.1` | Host (optional here — localhost is the default) |
| `-c "SQL"` | Run one command and exit, instead of going interactive |

Password when asked: `postgres`. The server runs as the Windows service
`postgresql-x64-17` on port `5432`.

Once in, the prompt is `labdb=#` — *database name* `=#`.

### Oracle SQL\*Plus — the lab's reference

```
sqlplus username/password@localhost:1521/XE
```
Prompt is `SQL>`. Exit with `EXIT`.

### MySQL — what CS1006's screenshots show

```
mysql -u root -p
```
Prompt is `mysql>`. You must pick a database first with `USE dbname;`.

---

## 2. Getting around inside psql

These start with a backslash. **They are client commands, not SQL** — psql interprets them
itself and never sends them to the server. That is why they need no semicolon, and why two of
them produce no output at all (see §4).

| Command | Does |
|---|---|
| `\l` | **L**ist all databases on the server |
| `\c labdb` | **C**onnect to (switch to) another database |
| `\dt` | **D**isplay **t**ables in the current database |
| `\d urk24cs1021_users` | **D**escribe one table — columns, types, indexes, constraints |
| `\d+ table` | Same, plus storage and description |
| `\du` | **D**isplay **u**sers/roles |
| `\dp table` | **D**isplay **p**rivileges (access privileges — what GRANT/REVOKE changed) |
| `\conninfo` | Show what you're connected to, as what user, on what port |
| `\set NAME value` | Set a **psql client variable** (this is how AUTOCOMMIT is toggled) |
| `\?` | Help on backslash commands |
| `\h SELECT` | Help on SQL syntax for a given statement |
| `\q` | **Q**uit |

**Equivalents you may be asked for:**

| Task | PostgreSQL | Oracle | MySQL |
|---|---|---|---|
| List databases | `\l` | `SELECT name FROM v$database;` | `SHOW DATABASES;` |
| Switch database | `\c dbname` | (one DB per instance; switch schema with `ALTER SESSION`) | `USE dbname;` |
| List tables | `\dt` | `SELECT table_name FROM user_tables;` | `SHOW TABLES;` |
| Describe a table | `\d t` | `DESC t;` | `DESC t;` |
| Quit | `\q` | `EXIT;` | `EXIT;` |

---

## 3. Your schema

Four tables, every one prefixed with your register number so they don't collide with anyone
else's on a shared server.

```
URK24CS1021_users     id, name, email, password, phone
URK24CS1021_location  venueid, name, address, city, state, country
URK24CS1021_event     eventid, name, eventdate, eventtime, venueid, description
URK24CS1021_ticket    ticketid, eventid, userid, price, status, barcode
```

**Why the names are odd — each of these is a real exam question:**

- **`users`, not `user`** — `USER` is a reserved word (in Oracle it's a built-in function
  returning the current username; creating a table called `user` gives `ORA-00903`).
- **`eventdate` / `eventtime`, not `date` / `time`** — `DATE` and `TIME` are reserved type names.
- **`location`, not `venue`** — Ex1(a) Q5 renames it. Every experiment after Ex1(a) must use
  the new name.
- **`id`, not `userid`** — Ex1(a) Q9 renames the column. Same rule.
- **`seatnumber` is gone** — Ex1(a) Q7 drops it. **`barcode` is new** — Q10 adds it.

The whole point of Ex1(a) is that the schema is *mutated* by the exercise. If she asks "why
doesn't your Ex2 use `venue`?", that's the answer.

---

## 4. Reading your own screenshots

This is what a viva actually is: she points at the screen and asks what something is.

| What you see | What it is |
|---|---|
| `labdb=#` | Ready for a new statement |
| `labdb(#` | **Continuation prompt** — the statement isn't finished; no `;` yet. Multi-line queries show this on every line after the first. |
| `urk24cs1021_users` when you typed `URK24CS1021_users` | PostgreSQL **folds unquoted identifiers to lower case**. `"URK24CS1021_users"` in double quotes would preserve case. It is not an error. |
| `CREATE TABLE` / `ALTER TABLE` / `GRANT` on a line by itself | The **command tag** — the server echoing that the statement succeeded. It's the output, not part of your input. |
| `INSERT 0 5` | 5 rows inserted. The `0` is the OID, a legacy field that is always 0 now. |
| `UPDATE 8` / `DELETE 2` | 8 rows updated / 2 rows deleted. |
| `(1 row)` / `(8 rows)` | How many rows the SELECT returned. |
| `(0 rows)` | The query ran fine and matched nothing. Correct SQL, empty answer. |
| `03:30:00`, `12:00:00` in Ex3 Q4 | These are **intervals** (durations), not clock times. `endtime - eventtime` on two timestamps yields an interval. |
| **Nothing at all** — Ex1(b) Q14 and Q15 | `\set AUTOCOMMIT on/off` is a psql *client* command. It never reaches the server, so the server prints nothing. **This is correct, not a failed screenshot.** Say it in exactly those words. |
| Ex1(b) Q12 showing ticket 903 but not 904 | Proof the `ROLLBACK TO SAVEPOINT` worked — 903 was inserted before the savepoint and survived, 904 after it and was undone. |

---

## 5. The five sub-languages

| | Stands for | Does | Your experiment |
|---|---|---|---|
| **DDL** | Data **Definition** Language | Defines/changes *structure* | Ex1(a) |
| **DML** | Data **Manipulation** Language | Changes *rows* | Ex1(b), Ex2 |
| **DQL** | Data **Query** Language | Reads rows (`SELECT`) | Ex2, Ex3 |
| **DCL** | Data **Control** Language | Permissions | Ex1(b) Q6–Q10 |
| **TCL** | **Transaction** Control Language | Transaction boundaries | Ex1(b) Q11–Q15 |

Common trip-up: **`SELECT` is DQL**, though many textbooks lump it into DML. If she says DML,
don't argue — say "DQL, or DML depending on the classification used."

Second trip-up: **DDL auto-commits.** A `CREATE`/`ALTER`/`DROP`/`TRUNCATE` cannot be rolled
back in Oracle/MySQL — it commits the transaction implicitly. (PostgreSQL is unusual: it *can*
roll back DDL.)

---

## 6. Keyword reference — DDL (Ex1a)

| Keyword | Meaning | Your line |
|---|---|---|
| `CREATE TABLE` | Make a new table | `CREATE TABLE URK24CS1021_users (...)` |
| `ALTER TABLE` | Change an existing table's structure | `ALTER TABLE URK24CS1021_users ADD COLUMN age numeric(3);` |
| `ADD COLUMN` | Add a new column | Q3 |
| `DROP COLUMN` | Remove a column **and its data** | `ALTER TABLE URK24CS1021_ticket DROP COLUMN seatnumber;` |
| `RENAME TO` | Rename the table | `ALTER TABLE URK24CS1021_venue RENAME TO URK24CS1021_location;` |
| `RENAME COLUMN … TO` | Rename a column | `ALTER TABLE URK24CS1021_users RENAME COLUMN userid TO id;` |
| `ALTER COLUMN … TYPE` | Change a column's data type/size | `ALTER COLUMN description TYPE varchar(1000)` |
| `TRUNCATE TABLE` | Delete **all** rows, keep the table | `TRUNCATE TABLE URK24CS1021_users;` |
| `DROP TABLE` | Delete the table itself | (used in the reset step) |
| `CONSTRAINT name` | Give a constraint an explicit name so it can be dropped later | `ADD CONSTRAINT users_email_uq UNIQUE (email)` |

### Constraints

| Keyword | Meaning | Your line |
|---|---|---|
| `PRIMARY KEY` | Unique **and** not null. One per table. Identifies a row. | `userid numeric(10) PRIMARY KEY` |
| `FOREIGN KEY … REFERENCES` | Value must exist in the referenced table's key. Enforces **referential integrity**. | `FOREIGN KEY (venueid) REFERENCES URK24CS1021_location(venueid)` |
| `REFERENCES` | Short inline form of the same thing | `eventid numeric(10) REFERENCES URK24CS1021_event(eventid)` |
| `UNIQUE` | No two rows may share this value. **Allows NULLs** (unlike PK). | `ADD CONSTRAINT users_email_uq UNIQUE (email)` |
| `CHECK` | Value must satisfy a condition | `CHECK (id BETWEEN 101 AND 105)` |
| `NOT NULL` | Value is mandatory *(not in your files — know it anyway)* | — |

**PRIMARY KEY vs UNIQUE** is the single most-asked constraint question:
PK = unique + not null + only one per table; UNIQUE = unique only, allows NULL, many per table.

### `TRUNCATE` vs `DELETE` vs `DROP` — asked almost every time

| | Removes | Keeps table | Has `WHERE` | Rollback | Type |
|---|---|---|---|---|---|
| `DELETE` | chosen rows | yes | yes | yes | DML |
| `TRUNCATE` | all rows | yes | no | **Oracle/MySQL: no. PostgreSQL: yes** | DDL |
| `DROP` | the table itself | no | no | Oracle/MySQL: no. PostgreSQL: yes | DDL |

`TRUNCATE` is also faster than `DELETE` on a full table — it deallocates the storage instead
of removing rows one at a time, which is why it can't be given a `WHERE` clause.

> **Careful — this one can catch you out.** The textbook answer is "TRUNCATE can't be rolled
> back", and that's true in Oracle and MySQL, where DDL causes an implicit commit. **PostgreSQL
> is the exception: its DDL is transactional**, so on the server your screenshots came from,
> `BEGIN; TRUNCATE t; ROLLBACK;` really does bring the rows back (verified). If she asks, give
> the textbook answer first, then add "though PostgreSQL is unusual here — its DDL is
> transactional, so it can be rolled back." That reads as knowing more, not as contradicting her.

---

## 7. Keyword reference — DML & DQL (Ex1b, Ex2, Ex3)

| Keyword | Meaning | Your line |
|---|---|---|
| `INSERT INTO … VALUES` | Add rows | `INSERT INTO URK24CS1021_users (id, name, …) VALUES (101, 'Alice Johnson', …);` |
| `UPDATE … SET` | Change values in existing rows | `UPDATE URK24CS1021_users SET email = 'mary.ann.new@mail.com' WHERE id = 102;` |
| `DELETE FROM` | Remove rows | `DELETE FROM URK24CS1021_ticket WHERE status = 'cancelled';` |
| `SELECT` | Read rows | `SELECT * FROM URK24CS1021_users;` |
| `FROM` | Which table(s) to read from | — |
| `*` | All columns | — |
| `WHERE` | Filter rows **before** grouping | `WHERE status = 'confirmed'` |
| `AS` | Alias — rename a column or table in the output | `SELECT COUNT(*) AS total_users` |
| `AND` / `OR` | Combine conditions | `WHERE city = 'New York' AND country = 'USA'` |
| `BETWEEN a AND b` | Range test, **inclusive of both ends** | `WHERE eventdate BETWEEN '2023-01-01' AND '2023-12-31'` |
| `IN (…)` | Matches any value in a list | `WHERE ticketid IN (903, 904)` |
| `DISTINCT` | Remove duplicate values | `SELECT COUNT(DISTINCT userid)` |
| `ORDER BY` | Sort the result | `ORDER BY city, country` |
| `ASC` / `DESC` | Ascending (default) / descending | `ORDER BY eventdate DESC` |
| `GROUP BY` | Collapse rows into groups, one output row per group | `SELECT eventid, AVG(price) … GROUP BY eventid` |
| `\|\|` | String concatenation (Oracle & PostgreSQL) | `SELECT name \|\| ' <' \|\| email \|\| '>' AS display` |
| `CASE WHEN … THEN … ELSE … END` | If/else *inside* a query | Ex3 Q10 |
| `INTERVAL '10 hours'` | A literal duration, for comparing against a time difference | `WHERE endtime - eventtime > INTERVAL '10 hours'` |

### Aggregate functions (the core of Ex3)

| Function | Returns | Your line |
|---|---|---|
| `COUNT(*)` | Number of rows | `SELECT COUNT(*) AS total_users FROM URK24CS1021_users;` |
| `COUNT(col)` | Rows where `col` is **not null** | — |
| `COUNT(DISTINCT col)` | Number of different non-null values | `COUNT(DISTINCT userid)` |
| `SUM(col)` | Total | `SELECT SUM(price) AS confirmed_total` |
| `AVG(col)` | Average | `AVG(endtime - eventtime)` |
| `MIN(col)` | Smallest | `MIN(endtime - eventtime)` |
| `MAX(col)` | Largest | `MAX(endtime - eventtime)` |

**Facts she can test you on:**
- `SUM` and `AVG` need numbers. `COUNT`, `MIN` and `MAX` also work on text and dates.
- Aggregates **ignore NULLs** — except `COUNT(*)`, which counts rows regardless.
- `COUNT(DISTINCT *)` is **illegal**. `DISTINCT` works with `COUNT(col)`, `SUM`, `AVG`,
  and is legal but pointless with `MIN`/`MAX` (the smallest value doesn't change when you
  remove duplicates). This is stated in your own Description paragraph.
- **`WHERE` filters rows before grouping; `HAVING` filters groups after.** You didn't need
  `HAVING`, but it is the obvious follow-up question to any `GROUP BY`.

### In your Description paragraph but not in your queries

She can ask about anything your own record claims to describe:

- `IS NULL` / `IS NOT NULL` — you must use these, never `= NULL`, because NULL is "unknown"
  and comparing anything to unknown gives unknown, not true.
- `LIKE` — pattern matching. `%` = any number of characters, `_` = exactly one.
  `WHERE name LIKE 'A%'` finds names starting with A.

---

## 8. Keyword reference — DCL & TCL (Ex1b)

### DCL

| Keyword | Meaning | Your line |
|---|---|---|
| `CREATE ROLE x LOGIN` | Create a user. **`LOGIN` makes it able to connect** — without it you get a group role that cannot log in. | `CREATE ROLE john LOGIN;` |
| `GRANT priv ON obj TO role` | Give a permission | `GRANT SELECT ON URK24CS1021_users TO john;` |
| `REVOKE priv ON obj FROM role` | Take it back | `REVOKE INSERT ON URK24CS1021_event FROM mary;` |
| `ALL PRIVILEGES` | Every permission on that object | `GRANT ALL PRIVILEGES ON URK24CS1021_ticket TO jane;` |
| `ALL TABLES IN SCHEMA public` | Applies to every table in the schema at once | `REVOKE ALL PRIVILEGES ON ALL TABLES IN SCHEMA public FROM guest;` |
| `EXECUTE` | Permission to run a function/procedure | `GRANT EXECUTE ON PROCEDURE URK24CS1021_ticket_count() TO admin;` |
| `CREATE OR REPLACE PROCEDURE` | Define a stored procedure, overwriting one of the same name | Ex1(b) Q9 |
| `LANGUAGE sql` | Which language the procedure body is written in | Ex1(b) Q9 |

Check your work with `\du` (roles) and `\dp tablename` (privileges).
In `\du`, a role that shows **"Cannot login"** was created *without* `LOGIN` — that's `admin`
in your Q9, which is deliberate: it's a group role for a permission, not a login account.

### TCL

| Keyword | Meaning | Your line |
|---|---|---|
| `BEGIN` | Start a transaction | Ex1(b) Q11–Q13 |
| `COMMIT` | Make everything since `BEGIN` permanent | `COMMIT;` |
| `ROLLBACK` | Undo the whole transaction | — |
| `SAVEPOINT sp1` | Mark a point you can return to *within* the transaction | `SAVEPOINT sp1;` |
| `ROLLBACK TO SAVEPOINT sp1` | Undo back to that mark only — the transaction stays open | `ROLLBACK TO SAVEPOINT sp1;` |
| `\set AUTOCOMMIT on/off` | psql client setting: whether each statement commits by itself | Q14, Q15 |

**The key TCL fact:** a transaction lives in **one connection**. Open a second terminal and
your `SAVEPOINT` is not there. That's why Q11–Q13 run `BEGIN … COMMIT` as one continuous
block in a single session.

**`ROLLBACK` vs `ROLLBACK TO SAVEPOINT`:** plain `ROLLBACK` discards everything and ends the
transaction; `ROLLBACK TO SAVEPOINT` rewinds to the mark and leaves you still inside it.

---

## 9. Dialect differences

Only the ones that appear in your own files or CS1006's.

| Purpose | Oracle (lab reference) | PostgreSQL (your screenshots) | MySQL (CS1006's) |
|---|---|---|---|
| Variable text | `VARCHAR2(255)` | `varchar(255)` | `VARCHAR(255)` |
| Number | `NUMBER(10)` | `numeric(10)` | `INT` |
| Decimal | `NUMBER(10,2)` | `numeric(10,2)` | `DECIMAL(10,2)` |
| Describe a table | `DESC t;` | `\d t` | `DESC t;` |
| Rename table | `RENAME t TO u;` | `ALTER TABLE t RENAME TO u;` | `RENAME TABLE t TO u;` |
| Change column type | `MODIFY col type` | `ALTER COLUMN col TYPE type` | `MODIFY col type` |
| Rename column | `RENAME COLUMN a TO b` | `RENAME COLUMN a TO b` | `CHANGE a b type` |
| Concatenate | `a \|\| b` | `a \|\| b` | `CONCAT(a, b)` |
| Autocommit | `SET AUTOCOMMIT ON` | `\set AUTOCOMMIT on` | `SET autocommit = 1;` |
| Prompt | `SQL>` | `labdb=#` | `mysql>` |

The standard SQL — `SELECT`, `WHERE`, `GROUP BY`, `ORDER BY`, aggregates, constraints,
`GRANT`/`REVOKE`, `COMMIT`/`ROLLBACK` — is **identical across all three**. Only the items
above differ. That is the honest, short answer to "is this the same as Oracle?"

---

## 10. Ex3 — the two questions you must be ready for

The Ex3 question set asks for things the given schema cannot express. You added the missing
columns openly, in the setup, with visible `ALTER TABLE` statements — they're in `ex3.sql` and
`ex3_commands.txt`. Have these two sentences ready:

**"Where did `endtime` come from?"**
> "Questions 4 and 6 ask for the time *taken* by an event and for events longer than 10 hours.
> The given schema only has a start time, `eventtime`, so a duration can't be expressed. I
> added an `endtime` column with `ALTER TABLE` in the setup, and the duration is computed as
> `endtime - eventtime`, which gives an interval."

**"Where did `seatnumber` come from? You dropped it in Ex1(a)."**
> "Yes — Ex1(a) Q7 drops it, and Ex3 Q7 asks for seat numbers. I added the column back with
> `ALTER TABLE` in the setup so the question could be answered on real data."

Also for Ex3 Q10 — she may ask why the price changed by different percentages:
> "A single `UPDATE` with a `CASE` expression: tickets over 30 get 2% off, the rest 4%. The
> screenshot shows a `SELECT` before and after, so both branches are visible — 150 became 147,
> and 25 became 24."

---

## 11. What each experiment proves

**Ex1(a) — DDL.** That you can build a schema and then evolve it: add/drop columns, rename
tables and columns, widen types, and add PK/FK/UNIQUE/CHECK constraints after the fact.
*Likely question:* "Which of these can't be undone?" → `TRUNCATE`, and dropping a column takes
its data with it.

**Ex1(b) — DML + DCL + TCL.** Row edits, permissions, transactions. *Likely question:* the
savepoint one — see §4, ticket 903 vs 904.

**Ex2 — Basic SQL.** `SELECT` with filtering, sorting, grouping, and the aggregate functions
introduced. *Likely question:* "What's the difference between `WHERE` and `ORDER BY`?" →
one filters which rows come back, the other only changes their order.

**Ex3 — Advanced SQL.** Aggregates, `GROUP BY`, `ORDER BY`. *Likely question:* anything in §7's
"facts she can test you on", plus the two schema questions in §10.

---

## 12. Rapid fire

- **What is a primary key?** Unique + not null, identifies a row, one per table.
- **PK vs UNIQUE?** UNIQUE allows NULL and you can have many; PK allows neither.
- **What is a foreign key for?** Referential integrity — the value must exist in the parent table.
- **DELETE vs TRUNCATE vs DROP?** See the table in §6.
- **Why `users` and not `user`?** Reserved word.
- **Can you roll back a `TRUNCATE`?** In Oracle/MySQL no — DDL auto-commits. In PostgreSQL yes,
  its DDL is transactional. Give the first half, then the second.
- **What does `COUNT(*)` count?** Rows, including ones full of NULLs.
- **Does `AVG` include NULLs?** No — aggregates skip them.
- **WHERE vs HAVING?** WHERE filters rows before grouping, HAVING filters groups after.
- **Why is your table name lowercase in the output?** PostgreSQL folds unquoted identifiers.
- **Why is that screenshot empty?** `\set` is a client command; the server sends nothing back.
- **What's `labdb(#`?** The continuation prompt — the statement has no `;` yet.
- **Difference between `ROLLBACK` and `ROLLBACK TO SAVEPOINT`?** Whole transaction vs back to a mark.
- **What does `LOGIN` do in `CREATE ROLE`?** Lets the role connect. Without it, it's a group role.
- **What is `INSERT 0 5`?** 5 rows inserted; the 0 is a legacy OID field.
- **Is your output real?** Yes — every screenshot is captured from a live PostgreSQL session,
  nothing was edited.
