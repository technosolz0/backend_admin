


# from fastapi import FastAPI
# from fastapi.openapi.utils import get_openapi
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.staticfiles import StaticFiles

# from app.api.routes import (
#     admin_auth,
#     category_routes,
#     user_routes,
#     service_provider_routes,
#     sub_category_routes,booking_routes,payment_route,user_address_router
# )

# from app.database import Base, engine
# from app.models import service_provider_model  # Ensure models are imported
# # If you have other model files, import them too so metadata includes all

# # Initialize app
# app = FastAPI()

# # Mount static directory
# app.mount("/static", StaticFiles(directory="static"), name="static")

# # Auto DB table creation during development
# @app.on_event("startup")
# def on_startup():
#     Base.metadata.create_all(bind=engine)

# # CORS config
# origins = [
#     "http://localhost:3002",
#     "http://127.0.0.1:3002",
#     "http://194.164.148.133:3002/",
#     # Add your production domains here
#     "http://194.164.148.133:3002",
#     "http://10.108.231.167:3002",
# ]

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # Include routers
# app.include_router(admin_auth.router, prefix="/api")
# app.include_router(user_routes.router, prefix="/api")
# app.include_router(category_routes.router, prefix="/api")
# app.include_router(sub_category_routes.router, prefix="/api")
# # app.include_router(service_routes.router, prefix="/api")
# app.include_router(service_provider_routes.router, prefix="/api")

# app.include_router(booking_routes.router, prefix="/api")
# app.include_router(payment_route.router, prefix="/api")
# app.include_router(user_address_router.router, prefix="/api")




# # Custom OpenAPI for JWT
# def custom_openapi():
#     if app.openapi_schema:
#         return app.openapi_schema
#     openapi_schema = get_openapi(
#         title="Servex API",
#         version="1.0.0",
#         description="Servex Backend with JWT Authentication",
#         routes=app.routes,
#     )
#     openapi_schema["components"]["securitySchemes"] = {
#         "BearerAuth": {
#             "type": "http",
#             "scheme": "bearer",
#             "bearerFormat": "JWT"
#         }
#     }
#     for path in openapi_schema["paths"]:
#         for method in openapi_schema["paths"][path]:
#             if method in ["get", "post", "put", "delete", "patch"]:
#                 openapi_schema["paths"][path][method]["security"] = [{"BearerAuth": []}]
#     app.openapi_schema = openapi_schema
#     return app.openapi_schema

# app.openapi = custom_openapi

# @app.get("/")
# def root():
#     return {"message": "Serwex API is running ✅"}



from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker
from app.database import Base, engine
from app.models import (
    user,
    service_provider_model,
    category,
    sub_category,
    booking_model,
    payment_model,
    user_address,
    vendor_subcategory_charge
)

from app.api.routes import (
    admin_auth,
    category_routes,
    user_routes,
    service_provider_routes,
    sub_category_routes,
    booking_routes,
    payment_route,
    user_address_router,
    delete_request_routes,
    wallet_routes,
    vendor_earnings_routes,
    cancel_reason_routes,
    vendor_dashboard_routes,
    withdrawal_routes, admin_withdrawal_routes,vendor_bank_routes,
)

# -------------------------
# Initialize FastAPI app
# -------------------------
app = FastAPI()

# Mount static directory
app.mount("/static", StaticFiles(directory="static"), name="static")

# -------------------------
# Database auto-update on startup
# -------------------------
@app.on_event("startup")
def on_startup():
    """
    Auto-create tables and add missing columns in PostgreSQL.
    Works only for new tables and missing columns.
    """
    # Create all tables
    Base.metadata.create_all(bind=engine)

    # Optional: add missing columns dynamically
    # Not recommended for production, better use Alembic
    inspector = inspect(engine)
    from sqlalchemy import Table, Column
    from sqlalchemy import text

    for table in Base.metadata.tables.values():
        table_name = table.name
        if inspector.has_table(table_name):
            existing_columns = [col['name'] for col in inspector.get_columns(table_name)]
            for column in table.columns:
                if column.name not in existing_columns:
                    # Add missing column
                    ddl = f'ALTER TABLE {table_name} ADD COLUMN {column.compile(dialect=engine.dialect)}'
                    with engine.connect() as conn:
                        conn.execute(text(ddl))
                        conn.commit()

# -------------------------
# CORS configuration
# -------------------------
origins = [
    "http://localhost:3002",
    "http://127.0.0.1:3002",
    "http://194.164.148.133:3002",
    "http://10.108.231.167:3002",
    "https://admin.serwex.in",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------
# Include Routers
# -------------------------
app.include_router(admin_auth.router, prefix="/api")
app.include_router(user_routes.router, prefix="/api")
app.include_router(category_routes.router, prefix="/api")
app.include_router(sub_category_routes.router, prefix="/api")
app.include_router(service_provider_routes.router, prefix="/api")
app.include_router(booking_routes.router, prefix="/api")
app.include_router(payment_route.router, prefix="/api")
app.include_router(user_address_router.router, prefix="/api")
app.include_router(delete_request_routes.router, prefix="/api")
app.include_router(wallet_routes.router, prefix="/api")
app.include_router(vendor_earnings_routes.router, prefix="/api")
app.include_router(cancel_reason_routes.router, prefix="/api")
app.include_router(vendor_dashboard_routes.router, prefix="/api")

app.include_router(withdrawal_routes.router, prefix="/api")
app.include_router(admin_withdrawal_routes.router, prefix="/api")
app.include_router(vendor_bank_routes.router, prefix="/api")

# -------------------------
# Custom OpenAPI with JWT
# -------------------------
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Serwex API",
        version="1.0.0",
        description="Serwex Backend with JWT Authentication",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
    }
    for path in openapi_schema["paths"]:
        for method in openapi_schema["paths"][path]:
            if method in ["get", "post", "put", "delete", "patch"]:
                openapi_schema["paths"][path][method]["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

# -------------------------
# Root endpoint
# -------------------------
@app.get("/")
def root():
    return {"message": "Serwex API is running ✅"}
