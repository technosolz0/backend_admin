# from fastapi import FastAPI
# from fastapi.openapi.utils import get_openapi
# from app.api.routes import admin_auth, category_routes, user_routes, service_provider_routes,sub_category_routes,service_routes  # ✅ import your combined users router here
# from app.database import Base, engine
# from fastapi.middleware.cors import CORSMiddleware
# from fastapi.staticfiles import StaticFiles
# from mangum import Mangum

# app = FastAPI()


# app.mount("/static", StaticFiles(directory="static"), name="static")
# Base.metadata.create_all(bind=engine)

# # CORS config
# origins = [
#     "http://localhost:3000",
#     "http://127.0.0.1:3000",
#     # Add production origins here
# ]

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=origins,
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # ✅ Include routers

# app.include_router(admin_auth.router, prefix="/api")         # combined user management + auth routes
# app.include_router(user_routes.router, prefix="/api")         # combined user management + auth routes
# app.include_router(category_routes.router, prefix="/api")

# app.include_router(sub_category_routes.router, prefix="/api")
# app.include_router(service_routes.router, prefix="/api")

# app.include_router(service_provider_routes.router, prefix="/api")  # service provider routes
# handler = Mangum(app) 
# # ✅ Swagger Bearer Token config
# def custom_openapi():
#     if app.openapi_schema:
#         return app.openapi_schema
#     openapi_schema = get_openapi(
#         title="Servex API",
#         version="1.0.0",
#         description="Custom FastAPI with JWT Auth",
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
#     return {"message": "Servex API is running ✅"}
from fastapi import FastAPI
from fastapi.openapi.utils import get_openapi
from app.api.routes import (
    admin_auth,
    category_routes,
    user_routes,
    service_provider_routes,
    sub_category_routes,
    service_routes
)
from app.database import Base, engine
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
Base.metadata.create_all(bind=engine)

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    # Add production origins here
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(admin_auth.router, prefix="/api")
app.include_router(user_routes.router, prefix="/api")
app.include_router(category_routes.router, prefix="/api")
app.include_router(sub_category_routes.router, prefix="/api")
app.include_router(service_routes.router, prefix="/api")
app.include_router(service_provider_routes.router, prefix="/api")

# Custom OpenAPI with JWT support
def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Servex API",
        version="1.0.0",
        description="Custom FastAPI with JWT Auth",
        routes=app.routes,
    )
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT"
        }
    }
    for path in openapi_schema["paths"]:
        for method in openapi_schema["paths"][path]:
            if method in ["get", "post", "put", "delete", "patch"]:
                openapi_schema["paths"][path][method]["security"] = [{"BearerAuth": []}]
    app.openapi_schema = openapi_schema
    return app.openapi_schema

app.openapi = custom_openapi

@app.get("/")
def root():
    return {"message": "Servex API is running ✅"}
