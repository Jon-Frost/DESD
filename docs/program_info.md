# Program Info

## Container Overview

This application runs across five Docker containers, each with a single, well-defined responsibility.

---

### 1. `db` — PostgreSQL Database
The `db` container runs a PostgreSQL 15 server and is the sole source of truth for all application data — users, products, orders, baskets, notifications, and recipes. It stores data on a named Docker volume (`postgres_data`) so that data persists across container restarts. No other container writes to the filesystem directly; all persistent state goes through this container.

---

### 2. `web` — Django Web Application
The `web` container runs the Django application server. It handles all incoming HTTP requests from the browser: rendering pages, processing forms, authenticating users, and applying business logic. When an action requires a notification to be sent (e.g. a customer places an order), the web container does not write the notification itself — it queues a background job and returns a response to the user immediately, keeping the experience fast.

---

### 3. `adminer` — Database Admin UI
The `adminer` container provides a browser-based graphical interface for inspecting and managing the PostgreSQL database directly. It is useful during development for running queries, checking table contents, and debugging data issues without needing a local database client. It connects to the `db` container and is accessible on port 8080.

---

### 4. `redis` — Message Broker
The `redis` container runs a Redis in-memory data store, used here exclusively as a message broker. When the `web` container queues a background job (via `create_notification.delay(...)`), it serialises the job as a JSON message and pushes it into a Redis queue. Redis holds the message until a worker is ready to process it. Redis has no knowledge of Django or the application — it is purely a fast, reliable queue.

---

### 5. `celery` — Background Worker
The `celery` container runs a Celery worker process using the same Django codebase as the `web` container. It continuously polls the Redis queue and executes any jobs it finds. Currently it handles the `create_notification` task, which writes `Notification` records to the database. Because it runs in its own container, background processing is completely isolated from the web server — a slow or failing notification job has no impact on page load times.
