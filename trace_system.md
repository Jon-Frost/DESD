# System Trace Documentation

## This will help with understanding the project so far

## 1) We have 2 profiles that can interact with the system so far

- **Producer**: creates and manages products, and maintains a producer bio.
- **Customer**: browses products, adds items to basket, and places orders.

### View database: run localhost:8080 and use the env variables for login

The project runs in Docker with PostgreSQL as the database and Adminer for DB inspection.

### View website: run localhost:8000 and create profiles for customer and producer to view their pages

---

## 2) Runtime architecture and service communication

### Services (`docker-compose.yaml`)

- **`db`**: PostgreSQL 15
  - Stores all Django data tables.
  - Persists data in named Docker volume `postgres_data`.
- **`web`**: Django app
  - Runs `python src/manage.py runserver 0.0.0.0:8000`.
  - Connects to PostgreSQL using environment variables (`POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `DB_HOST`, `DB_PORT`).
- **`adminer`**:
  - Exposes database UI at `http://localhost:8080`.
  - Connects to the same PostgreSQL service.

### Configuration handoff

- Environment values are injected from `.env` by Docker.
- Django reads those values in `src/core/settings.py` under `DATABASES`.
- So the chain is:
  - `.env` -> `docker-compose.yaml` -> container env vars -> `settings.py` -> Django DB connection.

---

## 3) Request routing trace (URL communication across files)

### Root routing (`src/core/urls.py`)

- `path('admin/', admin.site.urls)` routes Django admin.
- `path('', include('marketplace.urls'))` forwards all app traffic to marketplace routing.

### App routing (`src/marketplace/urls.py`)

Maps URL paths to function views in `src/marketplace/views.py`:

- Auth + onboarding:
  - `/` -> `home`
  - `/signup/` -> `signup_choice`
  - `/signup/producer/` -> `signup_producer`
  - `/signup/customer/` -> `signup_customer`
  - `/login/`, `/logout/`
- Producer features:
  - `/products/add/` -> `add_product`
  - `/products/<id>/` -> `producer_product_actions`
  - `/products/<id>/edit/` -> `edit_product`
  - `/products/<id>/delete/` -> `delete_product`
  - `/producer/bio/` -> `producer_bio`
  - `/producers/<id>/` -> `producer_bio_public`
- Customer market + basket features:
  - `/market/` -> `customer_market`
  - `/basket/add/<product_id>/` -> `add_to_basket`
  - `/basket/` -> `view_basket`
  - `/basket/remove/<item_id>/` -> `remove_from_basket`
  - `/basket/checkout/` -> `checkout`
  - `/orders/<order_id>/confirmation/` -> `order_confirmation`

---

## 4) Data model trace (how DB tables relate)

Defined in `src/marketplace/models.py`.

### User profile models

- **`Producer`** (`OneToOne` with Django `User`)
- **`Customer`** (`OneToOne` with Django `User`)

This allows one login system (`auth.User`) with role-specific profile data.

### Product model

- **`Product`** (`ForeignKey` to `Producer`)
- Includes: name, description, price, unit, stock quantity, category, organic flag, allergen info.

### Basket and order models

- **`BasketItem`** (`ForeignKey` to `Customer`, `ForeignKey` to `Product`)
  - Represents one line in a customer basket.
  - `unique_together = ('customer', 'product')` ensures one row per product per customer basket.
- **`CustomerOrder`** (`ForeignKey` to `Customer`)
  - Stores checkout-level data: delivery address/date, card holder, card last4, total, status.
- **`OrderItem`** (`ForeignKey` to `CustomerOrder`, `ForeignKey` to `Product`)
  - Stores order lines and snapshots `unit_price` at purchase time.

### Migration trace

- `src/marketplace/migrations/0006_basket_and_orders.py` creates:
  - `BasketItem`
  - `CustomerOrder`
  - `OrderItem`

So schema evolution path is:

- Existing marketplace tables (producer/customer/product)
- then migration `0006` adds basket + ordering subsystem.

---

## 5) Form validation and input handling trace

Defined in `src/marketplace/forms.py`.

### Signup forms

- `ProducerSignupForm` and `CustomerSignupForm`:
  - Create `auth.User` first.
  - Then attach and save corresponding profile model (`Producer`/`Customer`).

### Product form

- `ProductForm`:
  - Used by producers for product create/edit.
  - Includes all product details including stock quantity.

### Checkout form

- `CheckoutForm` captures:
  - `delivery_address`
  - `preferred_delivery_date`
  - `card_holder_name`
  - `card_number`
  - `card_expiry`
  - `card_cvv`

Validation behavior:

- `clean_card_number`: strips spaces/hyphens, requires exactly 16 digits.
- `clean_preferred_delivery_date`: must not be in the past.
- `clean_card_expiry`: expects `MM/YY` format.

Security behavior in flow:

- Full card number is validated but only last 4 digits are persisted in `CustomerOrder.card_number_last4`.

---

## 6) View-layer trace (request -> business logic -> DB -> response)

Defined in `src/marketplace/views.py`.

### Helper role gates

- `_get_logged_in_producer(user)` and `_get_logged_in_customer(user)`
  - Return profile if user has the role.
  - Return `None` otherwise.
- Most role-based views redirect to `home` if role check fails.

### Producer feature flow

1. Producer visits `/products/add/`.
2. `add_product` verifies producer profile.
3. On POST:
   - validates `ProductForm`
   - sets `product.producer = producer_profile`
   - saves product
4. Producer products are fetched and rendered on page.

For updates/deletes:

- `producer_product_actions` opens action page for owned product.
- `edit_product` binds form to instance and saves changes.
- `delete_product` removes product on POST.

### Customer browse flow

1. Customer visits `/market/`.
2. `customer_market` ensures customer role.
3. Loads products with `select_related('producer')`.
4. Renders `customer_market.html` with stock and add form.

### Add-to-basket flow

1. Customer submits POST to `/basket/add/<product_id>/`.
2. `add_to_basket`:
   - validates quantity >= 1
   - fetches/creates `BasketItem` for `(customer, product)`
   - computes `new_quantity = existing + requested`
   - checks `new_quantity <= product.stock_quantity`
   - if valid: saves basket line
   - else: returns error message
3. Redirects back to market with feedback message.

Important stock rule:

- Basket add operation never lets basket quantity exceed current stock, preventing stock from going below 0 at checkout.

### Basket view flow

1. Customer visits `/basket/`.
2. `view_basket` loads basket rows with products.
3. Computes total as sum of line subtotals.
4. Renders basket table + checkout form.

### Remove-from-basket flow

1. POST to `/basket/remove/<item_id>/`.
2. `remove_from_basket` verifies basket row belongs to current customer.
3. Deletes row and redirects back to basket.

### Checkout flow (critical stock update path)

1. POST to `/basket/checkout/`.
2. `checkout` verifies basket is non-empty.
3. Validates `CheckoutForm`.
4. Re-checks every basket line against **current** product stock (important for race/late stock changes).
5. Creates `CustomerOrder` row with checkout details and total.
6. For each basket line:
   - creates `OrderItem`
   - decrements `Product.stock_quantity` by ordered quantity
   - saves product
7. Deletes all customer `BasketItem` rows.
8. Redirects to order confirmation.

Result:

- Product stock is reduced only after successful order creation and line item creation.
- Basket is cleared only after order persists.

### Order confirmation flow

1. Customer visits `/orders/<order_id>/confirmation/`.
2. `order_confirmation` verifies order ownership.
3. Loads order items and renders summary page.

---

## 7) Template communication trace

### Base layout (`src/marketplace/templates/marketplace/base.html`)

- Provides top bar, nav, sidebar, content block.
- Displays role-aware menu items:
  - producer links for product/bio
  - customer links for market/basket
- Displays basket icon + count in top bar for customers.

### Market page (`customer_market.html`)

- Receives `products` context from `customer_market` view.
- For each product:
  - shows metadata and stock
  - renders quantity input + add button when stock > 0
  - renders out-of-stock notice when stock == 0
- POST target is `add_to_basket` route.

### Basket page (`basket.html`)

- Receives `basket_items`, `total`, and `form` from `view_basket` or failed `checkout`.
- Shows line-level and total pricing.
- Remove buttons POST to `remove_from_basket`.
- Checkout form POSTs to `checkout`.

### Confirmation page (`order_confirmation.html`)

- Receives `order` and `order_items`.
- Displays final order metadata and line totals.

---

## 8) Cross-cutting context and messaging

### Context processor (`src/marketplace/context_processors.py`)

- `basket_count(request)`:
  - if authenticated customer -> counts basket rows
  - otherwise -> 0
- Injected globally via `TEMPLATES[...]['context_processors']` in `src/core/settings.py`.

Effect:

- Any template can use `{{ basket_count }}` without passing it manually from every view.

### Django messages

- Views use `messages.success(...)` and `messages.error(...)`.
- Templates render `messages` blocks on market/basket pages.
- This communicates action outcomes across redirects.

---

## 9) End-to-end feature traces

### Feature A: Producer creates a product

1. Browser -> `/products/add/`
2. URL resolver -> `views.add_product`
3. Form validation (`ProductForm`)
4. DB write -> `Product`
5. Redirect + template rerender with updated producer product list

Files involved:

- `src/marketplace/urls.py`
- `src/marketplace/views.py`
- `src/marketplace/forms.py`
- `src/marketplace/models.py`
- `src/marketplace/templates/marketplace/producer_add_product.html`

### Feature B: Customer adds item to basket

1. Browser POST from `customer_market.html` form
2. URL resolver -> `views.add_to_basket`
3. Reads quantity and checks stock boundaries
4. DB write/update -> `BasketItem`
5. Redirect to market + success/error message
6. `basket_count` context processor updates top-bar badge on next render

Files involved:

- `src/marketplace/templates/marketplace/customer_market.html`
- `src/marketplace/urls.py`
- `src/marketplace/views.py`
- `src/marketplace/models.py`
- `src/marketplace/context_processors.py`
- `src/marketplace/templates/marketplace/base.html`

### Feature C: Customer checkout and stock deduction

1. Browser POST from `basket.html` to `/basket/checkout/`
2. URL resolver -> `views.checkout`
3. `CheckoutForm` validation
4. Stock re-check for each basket line
5. DB writes:
   - create `CustomerOrder`
   - create `OrderItem` rows
   - decrement each `Product.stock_quantity`
   - delete `BasketItem` rows
6. Redirect to `/orders/<id>/confirmation/`
7. Render summary in `order_confirmation.html`

Files involved:

- `src/marketplace/templates/marketplace/basket.html`
- `src/marketplace/forms.py`
- `src/marketplace/views.py`
- `src/marketplace/models.py`
- `src/marketplace/urls.py`
- `src/marketplace/templates/marketplace/order_confirmation.html`

---

## 10) Database inspection trace with Adminer

- Open: `http://localhost:8080`
- Login with PostgreSQL credentials from `.env`.
- You can inspect these key tables:
  - `marketplace_product`
  - `marketplace_basketitem`
  - `marketplace_customerorder`
  - `marketplace_orderitem`
  - `marketplace_customer`
  - `marketplace_producer`

Typical verification examples:

- After add-to-basket: check `marketplace_basketitem.quantity`.
- After checkout: basket rows gone, order/orderitem rows created, product stock reduced.

---

## 11) Current design assumptions and constraints

- Role detection uses `user.producer` / `user.customer` profile existence.
- Basket count currently counts distinct product lines, not total units.
- Checkout persists only card last 4 digits, not full PAN.
- Stock protection is enforced both on add-to-basket and again at checkout.

---

## 12) Quick system communication map

- **Routing**: `core/urls.py` -> `marketplace/urls.py`
- **Controller layer**: `marketplace/views.py`
- **Validation layer**: `marketplace/forms.py`
- **Persistence layer**: `marketplace/models.py` + migrations
- **Presentation layer**: templates under `templates/marketplace/`
- **Global UI state**: `marketplace/context_processors.py` -> `basket_count`
- **Infrastructure**: `docker-compose.yaml` + `core/settings.py`

This is the full flow from browser action to database mutation and back to rendered UI.

---

## 13) Practical use cases

### Use case 1: Producer adds a new product

**Goal:** A producer lists a new item in the marketplace.

1. Producer logs in and opens `/products/add/`.
2. Route in `marketplace/urls.py` maps to `views.add_product`.
3. View verifies the user has a producer profile.
4. Producer submits product form (name, category, price, stock, etc.).
5. `ProductForm` validates data in `marketplace/forms.py`.
6. `views.add_product` sets `product.producer = request.user.producer`.
7. Product is saved in `marketplace_product` table.
8. Page reloads and the newly added product appears in the producer list.

**Files involved:**

- `src/marketplace/templates/marketplace/producer_add_product.html`
- `src/marketplace/urls.py`
- `src/marketplace/views.py`
- `src/marketplace/forms.py`
- `src/marketplace/models.py`

### Use case 2: Producer updates their bio

**Goal:** A producer edits public profile text.

1. Producer opens `/producer/bio/`.
2. Route maps to `views.producer_bio`.
3. View loads current producer instance and pre-fills `ProducerBioForm`.
4. Producer submits updated bio text.
5. Form validates and saves into `Producer.bio`.
6. Updated text is now visible on public producer page `/producers/<producer_id>/`.

**Files involved:**

- `src/marketplace/templates/marketplace/producer_bio.html`
- `src/marketplace/templates/marketplace/producer_bio_public.html`
- `src/marketplace/urls.py`
- `src/marketplace/views.py`
- `src/marketplace/forms.py`
- `src/marketplace/models.py`

### Use case 3: Customer adds items to basket

**Goal:** A customer adds one or more units of a product to their basket.

1. Customer opens `/market/` and sees available products.
2. In `customer_market.html`, customer enters quantity and clicks **Add**.
3. Form POST goes to `/basket/add/<product_id>/` -> `views.add_to_basket`.
4. View checks:

- user is a customer,
- quantity is at least 1,
- new basket quantity does not exceed `product.stock_quantity`.

5. If item already exists in basket, quantity is incremented; otherwise a new `BasketItem` is created.
6. Success/error message is sent via Django messages and user is redirected back to market.
7. Basket count updates in top bar using global `basket_count` context processor.

**Files involved:**

- `src/marketplace/templates/marketplace/customer_market.html`
- `src/marketplace/templates/marketplace/base.html`
- `src/marketplace/urls.py`
- `src/marketplace/views.py`
- `src/marketplace/models.py`
- `src/marketplace/context_processors.py`
