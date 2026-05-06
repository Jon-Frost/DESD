# DESD

The repository for collaborating on the DESD module.

## Session

Friday 1pm-3pm

Group G5

---

Jira task management - [https://desd26.atlassian.net/jira/software/projects/SCRUM/boards/1]()

# BRFN

The Bristol Regional Food Network (BRFN) is in need of an online marketplace to connect local producers and customers in the Bristol area. This system removes the hastle of individuale sales and provides a comprehensive marketplace service allowing the network to grow and improve efficiency.

* Producers have the oportunity to list their products in one place for all customer to browse
* Producers have a detailed interface to list their products including harvest dates and allergen information
* Customers can conveiniently order from a range of local producers all in one place
* Orders are handled by the producers, BRFN is not involved in deliveries

# Setup

1. Start the containers and build the environment

Before first run, copy `.env.example` to `.env` and keep Cloudinary/Stripe keys blank as the system can run without the api keys:

Windows (PowerShell):

copy .env.example .env

docker compose up --build

2. Sync the database tables

docker compose exec web python src/manage.py makemigrations
docker compose exec web python src/manage.py migrate
docker compose exec web python src/manage.py seed_data

## Submission Setup (Seeded Data)


If you want a completely fresh seeded database:

docker compose down -v
docker compose up --build -d
docker compose exec web python src/manage.py migrate
docker compose exec web python src/manage.py seed_data

This command recreates the seed users and their linked sample marketplace data (orders, baskets, recurring orders, notifications, reviews).

## API Keys

- Cloudinary keys are optional. If blank, the app now uses local media storage and seeded images still work.
- Stripe keys are optional. If blank, checkout falls back to the local non-Stripe flow.
- For environment variables you will need `.env` from `.env.example` and the standard seed commands.

Demo accounts created by seed command:

- Admin: brfn_admin / Admin@BRFN2026
- Producer: olivia.barnes / Harvest!2026
- Producer: marcus.reed / Cotswold#2026
- Producer: hannah.clarke / Dairy&Grain2026
- Customer: daniel.price / Shopper!2026
- Customer: aisha.khan / Basket#2026
- Customer: tom.watkins / FreshFood2026!

---
