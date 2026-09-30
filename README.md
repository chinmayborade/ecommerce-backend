# E-Commerce Backend using FastAPI

A FastAPI-based ecommerce backend for managing users, products, categories, cart operations, and orders. It includes JWT-based authentication, role-based access control for users and admins, and SQLAlchemy models for database persistence.

## Features

- User registration and login with JWT authentication
- User profile management and password updates
- Product and category management
- Cart and checkout flow
- Order creation and tracking
- Admin-only endpoints for managing users and products
- Database setup using SQLAlchemy
- Deployment-ready configuration for Railway

## Tech Stack

- Python 3
- FastAPI
- SQLAlchemy
- PostgreSQL / SQLite-compatible database URL
- JWT (via python-jose)
- Passlib + bcrypt for password hashing
- Pydantic for request/response validation

## Project Structure

```text
.
├── main.py                 # App entry point and router registration
├── database.py            # SQLAlchemy engine, session, and base model setup
├── models.py              # Database models
├── requirements.txt       # Python dependencies
├── Procfile               # Process file for deployment
├── railway.toml           # Railway deployment configuration
├── .env                   # Environment variables (not committed)
├── routers/
│   ├── admin.py           # Admin-only APIs
│   ├── auth.py            # Auth and JWT logic
│   ├── cart.py            # Cart endpoints
│   ├── categories.py      # Category endpoints
│   ├── orders.py          # Order endpoints
│   ├── product.py         # Product endpoints
│   ├── user.py            # User profile endpoints
│   └── __init__.py
├── __init__.py
├── .gitignore
└── README.md
```

## Environment Variables

Create a `.env` file in the project root with the following values:

```env
DATABASE_URL=sqlite:///./ecommerce.db
SECRET_KEY=your_super_secret_key
ALGORITHM=HS256
```

Notes:
- `DATABASE_URL` can be a SQLite database or PostgreSQL URL.
- If you use PostgreSQL, the app includes a conversion from `postgres://` to `postgresql://` automatically.
- `SECRET_KEY` should be a long, random string in production.

## Installation

1. Clone the repository

```bash
git clone https://github.com/chinmayborade/ecommerce-backend.git
cd ecommerce-backend
```

2. Create a virtual environment

```bash
python -m venv .venv
source .venv/bin/activate   # On Windows: .venv\Scripts\activate
```

3. Install dependencies

```bash
pip install -r requirements.txt
```

## Running the App

Start the FastAPI server:

```bash
uvicorn main:app --reload
```

The app will be available at:

- http://127.0.0.1:8000
- Swagger docs: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

## API Overview

### Authentication

- `POST /auth/` - Register a new user
- `POST /auth/token` - Login and get JWT token

### User

- `GET /user/profile_info` - Get current user's profile
- `PUT /user/update_profile` - Update profile details
- `PUT /user/change_password` - Change password

### Admin

- `GET /admin/users` - View all non-admin users
- `POST /admin/create_prod` - Create a product
- `PUT /admin/update_prod/{prod_id}` - Update a product
- `DELETE /admin/delete_prod/{prod_id}` - Delete a product

### Products, Orders, Cart, Categories

The project also includes router modules for product listing, cart management, order processing, and category handling. These endpoints are registered in `main.py` and can be explored in the Swagger UI.

## Database

The app uses SQLAlchemy models defined in `models.py` and creates database tables on startup through:

```python
Base.metadata.create_all(bind=engine)
```

## Deployment

This repository includes deployment configuration for Railway:

- `Procfile`
- `railway.toml`

You can deploy the app to Railway by linking the repository and configuring environment variables in the Railway dashboard.

## Notes

- The project currently uses a simple role-based system with `user` and `admin` roles.
- The JWT token is issued with email, user ID, and role in the payload.
- For production, use a strong secret key, secure database credentials, and hardened environment configuration.

## License

This project does not currently include a license file. Add one if you want to publish or distribute the code publicly.
