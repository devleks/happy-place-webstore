# state.md — Current Instance Test State

## Environment Assumptions

- **Backend API:** `http://127.0.0.1:5001/api` (override via `BASE_URL`)
- **Ports (expected):**
  - backend `5001`
  - customer `3000`
  - admin `3001`
  - employee `3002`
  - POS `3003`

## Required Local Tools

- `bash`
- `curl`
- `python3`

## Required Seed Accounts

- **Admin:** `admin@happyplace.co.ke` / `admin123`
- **Manager:** `manager@happyplace.co.ke` / `manager123`

## Canonical API Endpoints Used by Current UAT Runner

### Customer

- `POST /auth/customer/register`
- `POST /auth/customer/login`
- `GET /products?page=1&per_page=12`
- `GET /products/<slug>`
- `POST /cart/items`
- `PATCH /cart/items/<item_id_or_variant_id>`
- `POST /orders/shipping-preview`
- `POST /orders`
- `GET /orders`
- `GET /orders/<order_id>`
- `POST /wishlist` (alias supported)
- `GET /wishlist`

### Employee / POS

- `POST /auth/employee/login`
- `GET /pos/shifts/current`
- `POST /pos/shifts/start`
- `POST /pos/transactions`
- `GET /pos/transactions/<id>/receipt/thermal?width=58`
- `GET /pos/transactions/<id>/receipt/html`

### Admin

- `GET /admin/dashboard/metrics`  (NOTE: not `/admin/dashboard`)
- `POST /admin/orders/<order_id>/tracking`
- `GET /admin/orders/<order_id>/tracking`

## Known Risk Areas

- Authentication token acceptance across customer/employee/admin endpoints.
- Cart update route accepts both item_id and variant_id, but method must be `PUT` or `PATCH`.
- Admin dashboard metrics route is `/api/admin/dashboard/metrics` (older scripts used `/api/admin/dashboard`).
