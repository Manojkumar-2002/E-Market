# E-Market Flow Documentation

## Overview

This document describes the E-Market backend in a customer-centered flow, beginning with anonymous browsing, then cart usage, registration/login, checkout, payment, order review, and administrative operations.

## 1. Public Visitor Experience

### 1.1 Product Discovery

Unauthenticated users can:
- browse products at `GET /api/v1/products/items/`
- view product details at `GET /api/v1/products/items/<id>/`
- explore product categories at `GET /api/v1/products/categories/`
- view variants at `GET /api/v1/products/variants/`

These endpoints are intentionally open to everyone. The system uses Redis caching for product listings to speed up repeated catalog queries.

### 1.2 Guest Cart Behavior

Unauthenticated visitors can still interact with the cart:
- add a variant to the cart using `POST /api/v1/carts/`
- update an existing cart item with `PATCH /api/v1/carts/items/<item_id>/`
- remove a cart item with `DELETE /api/v1/carts/items/<item_id>/`

Guest carts are stored by `session_key`. If the browser session does not already have a key, the app creates one automatically. This allows anonymous shoppers to build baskets without registering first.

### 1.3 Cart Rules for Guests

- Adding a product variant to the cart checks available stock before insertion.
- If the same variant is added again, the cart increments the quantity instead of creating duplicate items.
- The cart persists for the current browser session via Django session storage.

## 2. User Registration and Authentication Flow

### 2.1 Register First

A visitor can create an account using:
- `POST /api/v1/auth/register/`

The registration flow:
- accepts `email`, `password`, and optional user fields
- creates a secure user record
- stores user credentials with hashed passwords

### 2.2 Login and Token Usage

After registration, the user logs in with:
- `POST /api/v1/auth/login/`

On successful login, the system returns:
- an access token
- a refresh token

These JWT tokens are required for all secured operations.

### 2.3 Token Refresh and Logout

Authenticated users can refresh their access token with:
- `POST /api/v1/auth/token/refresh/`

To end a session, users call:
- `POST /api/v1/auth/logout/`

Logout blacklists the refresh token so it cannot be reused.

### 2.4 Profile Endpoint

A logged-in user can retrieve profile details from:
- `GET /api/v1/auth/profile/`

This endpoint returns the user’s email, name, phone, staff status, and audit timestamps.

## 3. Address Management for Checkout

Authenticated users can manage shipping addresses at:
- `GET /api/v1/auth/addresses/`
- `POST /api/v1/auth/addresses/`
- `PATCH /api/v1/auth/addresses/<id>/`
- `DELETE /api/v1/auth/addresses/<id>/`

Important behavior:
- Address records are tied to the logged-in user.
- The system enforces one address type per user (`HOME`, `OFFICE`, `OTHER`).
- If a user marks an address as default, the app automatically clears `is_default` for the user’s other addresses.

## 4. Product Catalog and Administrative Controls

### 4.1 Product Listing and Filtering

The products app offers both public and admin data paths:
- `GET /api/v1/products/items/` — public product listing
- `GET /api/v1/products/items/<id>/` — public product details

Product listing is cached in Redis for fast response times. The cache key depends on query filters and cursor pagination state.

### 4.2 Admin Product Operations

Only staff users may perform management actions on products and categories:
- create, update, delete categories
- create, update, delete products
- restore soft-deleted categories
- create, update, delete product variants
- add inventory logs

Admin endpoints include:
- `POST /api/v1/products/categories/`
- `PUT/PATCH /api/v1/products/categories/<id>/`
- `DELETE /api/v1/products/categories/<id>/`
- `POST /api/v1/products/categories/<id>/restore/`
- `POST /api/v1/products/items/`
- `PUT/PATCH /api/v1/products/items/<id>/`
- `DELETE /api/v1/products/items/<id>/`
- `POST /api/v1/products/variants/`
- `PATCH /api/v1/products/variants/<id>/`
- `DELETE /api/v1/products/variants/<id>/`
- `GET/POST /api/v1/products/inventory-logs/`

### 4.3 Inventory Management

Inventory logs are admin-only and maintain an audit trail for stock updates. When a new inventory log entry is created or updated, the related `ProductVariant` stock is adjusted with a row lock to avoid race conditions.

## 5. Cart-to-Checkout Flow

### 5.1 From Cart to Order

The checkout path starts only after login:
- `POST /api/v1/orders/checkout/`

Checkout requires:
- a valid address belonging to the authenticated user
- a list of cart items with `variant_id` and `quantity`

During checkout:
- the app validates each requested variant and quantity
- each variant row is locked with `select_for_update()` to prevent overselling
- variant stock is reduced immediately by the reserved quantity
- an `Order` record is created with `status = PENDING`
- all cart items for the user are removed
- a delayed Celery task is scheduled for later validation

### 5.2 What the Delayed Task Does

The app uses Celery with RabbitMQ to schedule `inspect_order_stock_ttl` after 5 minutes.

That task performs:
- if the order is still `PENDING`, cancel it and restore variant stock
- if the order is `PROCESSING` or `COMPLETED`, write an inventory audit entry
- a retry strategy is configured for transient database errors

This guarantees that reserved stock is not lost, while also allowing a payment window.

## 6. Payment Flow

### 6.1 Starting Payment

Authenticated users initiate payment with:
- `POST /api/v1/payments/initiate/<order_id>/`

The payment flow includes:
- checking order ownership and status
- refusing payment for cancelled or already processed orders
- creating a Razorpay order via the provider API
- updating the local order status to `PROCESSING`
- creating a `Transaction` record with gateway IDs and status `PENDING`
- returning payment intent details to the frontend

### 6.2 Payment Confirmation

Razorpay confirms final payment delivery through a webhook at:
- `POST /api/v1/payments/webhook/razorpay/`

The webhook request is:
- verified by cryptographic signature
- parsed for `order.paid` events
- matched to the local transaction by `gateway_order_id`

When payment succeeds, the app:
- marks the transaction `SUCCESS`
- saves the provider payment ID and signature
- updates the corresponding `Order` status to `COMPLETED`

This webhook endpoint is publicly accessible because payment providers send it from outside the app.

## 7. Order Access and Visibility

Authenticated users can view their own orders:
- `GET /api/v1/orders/orders/`
- `GET /api/v1/orders/orders/<id>/`

Order data includes:
- shipped address snapshot
- total amount
- order status
- nested line items with product title, SKU snapshot, and purchase price

Admin users can access all orders, while regular customers see only their own.

## 8. Technology and Infrastructure Details

### Backend
- Django
- Django REST Framework
- Django Filters
- DRF Spectacular

### Authentication
- JWT access & refresh tokens via `rest_framework_simplejwt`
- Custom email-based user model
- Token blacklist for logout support

### Cache and Sessions
- Redis cache for product listings and shared application state
- Redis-throttle cache for request throttling
- Redis session cache for authenticated or anonymous sessions

### Background Tasks
- Celery with RabbitMQ broker
- Redis result backend
- `apps.orders.tasks.inspect_order_stock_ttl` mapped to the `checkout` queue

### Payment Provider
- Razorpay integration via `apps.core.utils.payment_utils`
- configurable via `PAYMENTS` settings

## 9. Security and Roles Summary

### Public access
- product browsing
- product details
- variants listing
- cart creation and updates for guest sessions
- Razorpay webhook receipt

### Authenticated user access
- profile retrieval
- logout
- address management
- checkout and payment initiation
- viewing own orders

### Admin-only access
- managing categories and products
- changing variants
- creating and updating inventory logs
- restoring soft-deleted categories

## 10. Recommended User Journey

1. Browse products anonymously.
2. Add items to a cart as a guest if desired.
3. Register an account.
4. Login and receive JWT tokens.
5. Add or select a shipping address.
6. Place an order via the checkout API.
7. Initiate payment for the order.
8. Wait for Razorpay webhook confirmation.
9. View order history as an authenticated user.

## 11. Key Files for Each Flow

- `apps/users/` — login, registration, profile, addresses
- `apps/products/` — categories, products, variants, inventory audit
- `apps/carts/` — cart lifecycle and guest session support
- `apps/orders/` — order creation, checkout reservation, delayed task
- `apps/payments/` — payment intent and webhook processing
- `apps/core/utils/cache_manager.py` — versioned Redis cache keys
- `config/settings/components/cache.py` — Redis cache mapping
- `config/settings/components/celery_config.py` — RabbitMQ and Celery queues

## 12. Quick Route Map

### Authentication
- `POST /api/v1/auth/register/`
- `POST /api/v1/auth/login/`
- `POST /api/v1/auth/token/refresh/`
- `POST /api/v1/auth/logout/`
- `GET /api/v1/auth/profile/`
- `GET/POST/PATCH/DELETE /api/v1/auth/addresses/`

### Products
- `GET /api/v1/products/items/`
- `GET /api/v1/products/items/<id>/`
- `GET /api/v1/products/categories/`
- `GET /api/v1/products/variants/`

### Cart
- `GET /api/v1/carts/`
- `POST /api/v1/carts/`
- `PATCH /api/v1/carts/items/<item_id>/`
- `DELETE /api/v1/carts/items/<item_id>/`

### Orders
- `POST /api/v1/orders/checkout/`
- `GET /api/v1/orders/orders/`
- `GET /api/v1/orders/orders/<id>/`

### Payments
- `POST /api/v1/payments/initiate/<order_id>/`
- `POST /api/v1/payments/webhook/razorpay/`
