# E-Market Project Documentation

## 1. Project Overview

E-Market is a Django-based ecommerce backend implementing a marketplace workflow with customer accounts, product catalog management, cart handling, order processing, and payment integration.

Key architectural elements:
- Django REST Framework for API design
- Custom user authentication with JWT (`rest_framework_simplejwt`)
- Redis caching for product catalog performance and session/throttle isolation
- Celery with RabbitMQ for delayed order stock verification tasks
- Razorpay payment initialization and webhook-based transaction confirmation
- Clean separation by Django app: `users`, `products`, `carts`, `orders`, `payments`

## 2. Technology Stack

### Backend and Frameworks
- Python / Django
- Django REST Framework (DRF)
- DRF Spectacular for OpenAPI schema and Swagger docs
- Django Filters for product filtering

### Authentication & Authorization
- `rest_framework_simplejwt` for JWT access and refresh tokens
- Custom `User` model using email login
- Token blacklist support for logout

### Caching and Performance
- Redis as primary cache backend for product listing and application state
- Redis also used for:
  - request throttling cache
  - session cache
- `apps.core.utils.cache_manager.CacheManager` implements versioned cache keys for products, carts, and orders.

### Asynchronous Processing
- Celery for background task execution
- RabbitMQ as Celery message broker
- Redis as Celery result backend
- `inspect_order_stock_ttl` delayed task restores stock or records completed payment flows

### Payment Integration
- Razorpay via a shared payment utility client
- Payment initialization endpoint + signed webhook receiver
- Transaction audit model tracks payment gateway state

## 3. Core Configuration

### Base Settings
- `config/settings/base.py`
  - Defines installed apps, including `apps.core`, `apps.users`, `apps.products`, `apps.carts`, `apps.orders`, and `apps.payments`
  - Uses `AUTH_USER_MODEL = 'users.User'`
  - Middleware includes global exception middleware from `apps.core.exceptions.global_exception_middleware`

### Development Settings
- `config/settings/development.py`
  - Loads JWT auth configuration
  - Loads Redis cache configuration
  - Loads Celery configuration
  - Loads payment provider config
  - Uses Redis-backed session engine with `SESSION_ENGINE = "django.contrib.sessions.backends.cache"`

### Cache Setup
- `config/settings/components/cache.py`
  - `default` cache: `REDIS_CACHE_URL`
  - `throttle` cache: `REDIS_THROTTLE_URL`
  - `session` cache: `REDIS_SESSION_URL`

### Celery Setup
- `config/settings/components/celery_config.py`
  - Message broker configured from `CELERY_BROKER_URL` (default RabbitMQ)
  - Result backend configured from `CELERY_RESULT_BACKEND` (default Redis)
  - `CELERY_TASK_ACKS_LATE = True`
  - `CELERY_TASK_REJECT_ON_WORKER_LOST = True`
  - Queue definitions include `checkout` and `checkout.dlq`
  - Task route maps `apps.orders.tasks.inspect_order_stock_ttl` to `checkout`

### Celery App Loading
- `config/celery.py`
  - Creates `Celery('e-market')`
  - Loads Django settings with namespace `CELERY`
  - Autodiscover tasks from installed apps

### Project URLs
- `config/urls.py`
  - `admin/`
  - `api/v1/auth/` → user auth and profile
  - `api/v1/products/` → products, categories, variants, inventory logs
  - `api/v1/carts/` → cart and cart item operations
  - `api/v1/orders/` → checkout and order queries
  - `api/v1/payments/` → payment initialization and Razorpay webhook
  - `api/schema/` and `api/docs/` for API schema and docs

## 4. App-by-App Flow

### 4.1 Users App (`apps.users`)

#### Models
- `User` (`apps.users.models.user_model.User`)
  - Email-based authentication
  - `first_name`, `last_name`, `phone_number`
  - `is_staff` and `is_active`
  - Inherits audit fields from `apps.core.models.BaseModel`
- `Address` (`apps.users.models.address_model.Address`)
  - Stores user shipping addresses
  - `address_type` and `is_default`
  - Saves default address rule automatically

#### Serializers
- `RegisterSerializer` handles account creation and password hashing
- `LoginSerializer` authenticates user credentials via Django `authenticate`
- `LogoutSerializer` validates refresh token blacklisting
- `UserSerializer` returns profile data
- `AddressSerializer` validates address formatting and enforces per-user unique address types

#### Views
- `RegisterAPIView` (`POST /api/v1/auth/register/`)
  - Allows anyone to register
- `LoginAPIView` (`POST /api/v1/auth/login/`)
  - Issues JWT access and refresh tokens
- `CustomTokenRefreshAPIView` (`POST /api/v1/auth/token/refresh/`)
  - Refreshes access tokens
- `LogoutAPIView` (`POST /api/v1/auth/logout/`)
  - Requires authentication
  - Blacklists provided refresh token
- `ProfileAPIView` (`GET /api/v1/auth/profile/`)
  - Requires authentication
  - Returns authenticated user profile
- `AddressViewSet` (`/api/v1/auth/addresses/`)
  - Requires authentication
  - User can list, create, update, and delete their own addresses
  - Access is scoped to `request.user`

#### Access Rules
- Public actions: register, login, token refresh
- Authenticated actions: logout, profile, address management

### 4.2 Products App (`apps.products`)

#### Models
- `Category` (`apps.products.models.product_model.Category`)
  - Category `/ products relationship`
  - Auto-generates `slug` if missing
- `Product` (`apps.products.models.product_model.Product`)
  - Contains `name`, `description`, `category`
  - Soft-delete and activity fields are implied by base audit model
- `ProductVariant` (`apps.products.models.product_model.ProductVariant`)
  - Item SKU model with `sku`, `price`, `stock_quantity`, `size`, `color`
  - Used by cart and order item flows

#### Serializers
- `CategorySerializer` for category CRUD
- `ProductListSerializer` for public product listings
- `ProductDetailSerializer` for product retrieval
- `ProductWriteSerializer` for admin product create/update
- `ProductVariantSerializer` for SKU-level admin management
- `InventoryLogSerializer` for audit inventory records

#### Cache Manager
- `apps.core.utils.cache_manager.CacheManager`
  - Maintains versioned cache layers for `Products`, `Carts`, and `Orders`
  - Uses a global master switch and per-scope version keys
  - Builds cache keys with `master_version`, `scope_id`, and `sub_version`
  - Provides `get_cached_data` and `set_cached_data`
  - Bumps version on product/category changes to invalidate stale keys

#### Views
- `CategoryViewSet` (`/api/v1/products/categories/`)
  - `list` and `retrieve`: open to public
  - `create`, `update`, `destroy`, `restore`: admin-only
  - Automatic soft-delete restore route `POST /api/v1/products/categories/<id>/restore/`
- `ProductViewSet` (`/api/v1/products/items/`)
  - `list` and `retrieve`: open to public
  - `create`, `update`, `destroy`: admin-only
  - `list` uses Redis caching with query-string hashing and cursor pagination
  - `retrieve` bypasses cache for real-time data
  - `perform_create`, `perform_update`, `perform_destroy` call cache version bumps
- `ProductVariantViewSet` (`/api/v1/products/variants/`)
  - Public read access for list/retrieve
  - Admin-only for create/update/delete
- `InventoryLogViewSet` (`/api/v1/products/inventory-logs/`)
  - Admin-only inventory audit endpoint
  - `perform_create` updates product variant stock atomically
  - `perform_update` reconciles stock changes safely with delta application

#### URLs
- `GET /api/v1/products/categories/`
- `GET /api/v1/products/categories/<id>/`
- `POST /api/v1/products/categories/`
- `PUT/PATCH /api/v1/products/categories/<id>/`
- `DELETE /api/v1/products/categories/<id>/`
- `POST /api/v1/products/categories/<id>/restore/`
- `GET /api/v1/products/items/`
- `GET /api/v1/products/items/<id>/`
- `POST /api/v1/products/items/`
- `PUT/PATCH /api/v1/products/items/<id>/`
- `DELETE /api/v1/products/items/<id>/`
- `GET /api/v1/products/variants/`
- `GET /api/v1/products/variants/<id>/`
- `POST /api/v1/products/variants/`
- `PATCH /api/v1/products/variants/<id>/`
- `DELETE /api/v1/products/variants/<id>/`
- `GET /api/v1/products/inventory-logs/`
- `POST /api/v1/products/inventory-logs/`

### 4.3 Carts App (`apps.carts`)

#### Models
- `Cart` (`apps.carts.models.cart_model.Cart`)
  - One-to-one relation to authenticated `User`
  - `session_key` fallback for guest carts
  - Stores shopping basket items
- `CartItem` (`apps.carts.models.cart_model.CartItem`)
  - Links to `Cart` and `ProductVariant`
  - Ensures unique variant per cart
  - `quantity` with min value validation

#### Serializers
- `CartItemVariantSerializer` embeds variant details inside cart responses
- `CartItemSerializer` updates quantity and computes `line_total`
- `AddToCartSerializer` validates add requests against active variant stock
- `CartSerializer` returns total item count and cart total amount

#### Views
- `CartAPIView` (`/api/v1/carts/`)
  - `GET` fetches current cart for authenticated or anonymous users
  - `POST` adds or increments a cart item
- `CartItemDetailAPIView` (`/api/v1/carts/items/<item_id>/`)
  - `PATCH` updates item quantity
  - `DELETE` removes item from cart permanently

#### Cart Behavior
- Authenticated users: cart is stored by `user`
- Anonymous guests: cart is stored by `session_key`
- Adding the same variant increments quantity rather than creating duplicate lines
- Stock availability is validated before adding items

### 4.4 Orders App (`apps.orders`)

#### Models
- `Order` (`apps.orders.models.order_model.Order`)
  - Linked to a `User`
  - `status` with choices: `PENDING`, `PROCESSING`, `COMPLETED`, `CANCELLED`, `FAILED`
  - `total_amount`
  - `shipping_address_snapshot` stores immutable JSON address data
- `OrderItem` (`apps.orders.models.order_model.OrderItem`)
  - Links to `Order` and `ProductVariant`
  - Stores `price_at_purchase`, `sku_snapshot`, and metadata snapshot

#### Serializers
- `CheckoutItemSerializer` validates each requested `variant_id` and `quantity`
- `CheckoutRequestSerializer` validates order checkout payload and binds address ownership
- `OrderItemSerializer` serializes saved order items with product title
- `OrderSerializer` formats order header and nested order items

#### Views
- `CheckoutView` (`POST /api/v1/orders/checkout/`)
  - Requires `IsAuthenticated`
  - Converts validated cart contents into a pending order
  - Locks `ProductVariant` rows with `select_for_update()`
  - Deducts reserved stock from variants
  - Creates `OrderItem` snapshots and total amount
  - Clears matching cart items permanently
  - Schedules `inspect_order_stock_ttl` Celery task to run in 5 minutes
- `OrderViewSet` (`/api/v1/orders/orders/`)
  - Read-only endpoint for order queries
  - Authenticated user access
  - Staff users can see all orders
  - Regular users only see their own orders

#### Task Flow
- `apps.orders.tasks.inspect_order_stock_ttl`
  - Runs after checkout countdown expires
  - If order remains `PENDING`: cancels it and restores reserved variant stock
  - If order is `PROCESSING` or `COMPLETED`: writes an inventory log entry for successful sale
  - Uses Celery retry management for operational DB failures

#### URLs
- `POST /api/v1/orders/checkout/`
- `GET /api/v1/orders/orders/`
- `GET /api/v1/orders/orders/<id>/`

### 4.5 Payments App (`apps.payments`)

#### Models
- `Transaction` (`apps.payments.models.payment_model.Transaction`)
  - Linked to `Order`
  - Tracks payment gateway and status
  - Stores `gateway_order_id`, `gateway_transaction_id`, `gateway_signature` and raw webhook snapshot
- `PaymentGateway` and `TransactionStatus` define provider and status choices

#### Serializers
- `PaymentInitResponseSerializer` describes the data returned to the frontend for payment initialization
- `TransactionAuditSerializer` can serialize transaction audit state when needed

#### Views
- `InitializePaymentView` (`POST /api/v1/payments/initiate/<order_id>/`)
  - Requires `IsAuthenticated`
  - Validates order ownership and payable state
  - Creates Razorpay order intent via external API call
  - Stores transaction record and updates order status to `PROCESSING`
  - Returns `gateway_order_id`, `amount`, `currency`, and public key ID for checkout
- `RazorpayWebhookView` (`POST /api/v1/payments/webhook/razorpay/`)
  - `AllowAny` because Razorpay sends server-to-server callbacks
  - Verifies webhook signature using `RAZORPAY` webhook secret
  - Marks transaction `SUCCESS` and order `COMPLETED` when payment is confirmed

#### Access Rules
- Payment initiation: authenticated users only
- Webhook: public endpoint for provider callbacks

## 5. API Interaction Flow

### Customer Journey
1. Register with `POST /api/v1/auth/register/`
2. Login with `POST /api/v1/auth/login/`
3. Browse products with `GET /api/v1/products/items/` and `GET /api/v1/products/items/<id>/`
4. Add variants to cart with `POST /api/v1/carts/`
5. Update or remove items via `PATCH`/`DELETE /api/v1/carts/items/<item_id>/`
6. Add or select address using `/api/v1/auth/addresses/`
7. Checkout with `POST /api/v1/orders/checkout/`
8. Initiate payment with `POST /api/v1/payments/initiate/<order_id>/`
9. Razorpay webhook confirms payment asynchronously at `/api/v1/payments/webhook/razorpay/`
10. View orders with `GET /api/v1/orders/orders/`

### Admin Journey
1. Authenticate as staff or superuser via login
2. Manage product categories and products with `/api/v1/products/categories/` and `/api/v1/products/items/`
3. Manage variants via `/api/v1/products/variants/`
4. Manage inventory logs securely via `/api/v1/products/inventory-logs/`
5. View all orders via `/api/v1/orders/orders/`

## 6. Authorization and Permissions Summary

### Public Endpoints
- `POST /api/v1/auth/register/`
- `POST /api/v1/auth/login/`
- `POST /api/v1/auth/token/refresh/`
- Product listing and retrieval endpoints
- Variant listing and retrieval endpoints
- Razorpay webhook endpoint

### Authenticated Endpoints
- `POST /api/v1/auth/logout/`
- `GET /api/v1/auth/profile/`
- `GET/POST/PATCH/DELETE /api/v1/auth/addresses/`
- Cart operations under `/api/v1/carts/`
- Checkout endpoint `/api/v1/orders/checkout/`
- Payment initialization `/api/v1/payments/initiate/<order_id>/`
- Read own orders `/api/v1/orders/orders/`

### Admin-Only Actions
- All non-public product category management
- All non-public product item management
- All variant create/update/delete actions
- Inventory log creation and updates
- Product category restore actions

## 7. System and Flow Design Notes

### Product Listing Cache
- Product listing uses deterministic query key hashing
- Cache keys include query filters, cursor position, category scope, and version tokens
- Cache invalidation occurs on product category changes and product create/update/delete actions
- Product detail views bypass cache for real-time inventory accuracy

### Checkout Reservation and Delay Task
- Checkout creates `Order` and reserves stock immediately
- Cart items are hard-deleted once reserved
- `inspect_order_stock_ttl` runs after a 5-minute countdown
  - Re-adds stock if payment is not completed
  - Finalizes inventory audit if payment succeeded
- This design reduces overselling and preserves transactional inventory integrity

### Payment Finalization
- Payment initialization writes an order-processing intent and transaction record atomically
- Razorpay webhook updates the transaction and order status after successful payment
- The webhook verifies request authenticity to protect the flow

## 8. File and Route Map

### Main Entry Points
- `manage.py`
- `config/urls.py`
- `config/celery.py`
- `config/settings/development.py`
- `config/settings/components/cache.py`
- `config/settings/components/celery_config.py`

### Apps and Primary Files
- `apps/users/`
  - Models: `user_model.py`, `address_model.py`
  - Serializers: `auth_serializer.py`, `address_serializer.py`
  - Views: `auth_view.py`, `address_view.py`
  - URLs: `urls.py`
- `apps/products/`
  - Models: `product_model.py`
  - Serializers: `product_serializer.py`, `variant_serializer.py`, `inventory_serializer.py`
  - Views: `product_view.py`, `variant_view.py`, `inventory_view.py`
  - URLs: `urls.py`
  - Filters: `product_filter.py`
- `apps/carts/`
  - Models: `cart_model.py`
  - Serializers: `cart_serializer.py`
  - Views: `cart_view.py`
  - URLs: `urls.py`
- `apps/orders/`
  - Models: `order_model.py`
  - Serializers: `order_serializer.py`
  - Views: `order_view.py`
  - Tasks: `tasks.py`
  - URLs: `urls.py`
- `apps/payments/`
  - Models: `payment_model.py`
  - Serializers: `payment_serializer.py`
  - Views: `payment_view.py`
  - URLs: `urls.py`
- `apps/core/`
  - `views/base_view.py`
  - `utils/cache_manager.py`
  - `utils/response_handler.py`
  - `utils/serializer_handler.py`
  - `utils/payment_utils.py`

## 9. Important Behaviors to Remember

- Guest cart persistence is based on `request.session.session_key`.
- Order checkout reserves stock before payment and removes cart items.
- A 5-minute delayed Celery task validates the order lifecycle after checkout.
- Product listing cache is intentionally separate from detail reads.
- Admin-only routes protect catalog and inventory management.
- JWT authentication is the primary secure access mechanism.

---

## 10. Usage Tips

- Run Django with the appropriate `DJANGO_SETTINGS_MODULE=config.settings.development` or production settings.
- Ensure RabbitMQ and Redis are available and reachable by the configured service URLs.
- Use Swagger docs at `/api/docs/` during development for endpoint exploration.
- Create an admin or superuser before using admin-protected product or inventory endpoints.
- Populate Razorpay settings via environment variables for payment integration.
