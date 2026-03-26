# DESD

The repository for collaborating on the DESD module.

## Session

Reccomended session is friday 1pm-3pm

---

Meetings on monday evenings

---

Jira task management - [https://desd26.atlassian.net/jira/software/projects/SCRUM/boards/1]()

---

Setup

# 1. Start the containers and build the environment

docker compose up --build

# 2. Sync the database tables

docker compose exec web python src/manage.py makemigrations
docker compose exec web python src/manage.py migrate

# BRFN

The Bristol Regional Food Network (BRFN) is in need of an online marketplace to connect local producers and customers in the Bristol area. This system removes the hastle of individuale sales and provides a comprehensive marketplace service improving the food network's growth and efficiency.

* Producers have the oportunity to list their products in one place for all potential customer to browse
* Producers have a detailed interface to list their products including harvest dates and allergen information
* Cusotmers can conveiniently order from a range of local producers all in one place
* Orders are handled by the producers, BRFN is not involved in deliveries

---

# Test Cases:

1. TC-001 - Passed
2. TC-002 - Passed
3. TC-003 - Passed
4. TC-004 - Passed
5. TC-005 - Passed
6. TC-006 - Passed
7. TC-007 - Passed
8. TC-008 - Passed
9. TC-009 - Passed
10. TC-010 - Passed
11. TC-011 - Passed
12. TC-012 -
13. TC-013 -
14. TC-014 - Passed
15. TC-015 - Passed
16. TC-016 -
17. TC-017 - Passed
18. TC-018 -
19. TC-019 -
20. TC-020 -
21. TC-021 - Passed
22. TC-022 - Passed
23. TC-023 - Passed
24. TC-024 - Passed
25. TC-025 - Passed
