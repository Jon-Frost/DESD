# DESD

The repository for collaborating on the DESD module.

## Session

Reccomended session is friday 1pm-3pm

---

Meetings on monday 5pm

---

Jira link: https://desd26.atlassian.net/?continue=https%3A%2F%2Fdesd26.atlassian.net%2Fwelcome%2Fsoftware%3FprojectId%3D10000&atlOrigin=eyJpIjoiMzEzOWM4NzlkZmZmNGUwMWIxODNmZjNjODgxNTQyZTMiLCJwIjoiamlyYS1zb2Z0d2FyZSJ9

---

Setup

# 1. Start the containers and build the environment

docker compose up -d --build

# 2. Sync the database tables

docker compose exec web python src/manage.py migrate

# 3. Create an admin login

docker compose exec web python src/manage.py createsuperuser

access from - http://localhost:8000/admin


### Migrate Commands

docker compose exec web python src/manage.py makemigrations
docker compose exec web python src/manage.py migrate

---
