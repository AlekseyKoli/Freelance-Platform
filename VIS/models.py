import sqlite3


conn = sqlite3.connect('freelance_platform.db')
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS Users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
""")
c.execute("""
CREATE TABLE IF NOT EXISTS Freelancers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    skills TEXT,
    description TEXT,
    profile_picture TEXT,
    FOREIGN KEY (user_id) REFERENCES Users (id)
);
""")
c.execute("""
CREATE TABLE IF NOT EXISTS Projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    budget TEXT,
    required_skills TEXT
);
""")

c.execute("""
CREATE TABLE IF NOT EXISTS Applications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER NOT NULL,
    freelancer_id INTEGER NOT NULL,
    profile_picture TEXT,
    proposal TEXT NOT NULL,
    FOREIGN KEY (project_id) REFERENCES Projects (id),
    FOREIGN KEY (freelancer_id) REFERENCES Freelancers (id)
);
""")
c.execute("SELECT * from Users")

rows = c.fetchall()


for row in rows:
    print(row)
    

conn.commit()
conn.close()
