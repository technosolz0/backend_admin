# from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form, status
# from sqlalchemy.orm import Session
# from app.core.security import get_db
# from app.schemas.service_schema import ServiceOut, ServiceStatus
# from app.crud import service
# import os, shutil
# from uuid import uuid4

# router = APIRouter(prefix="/services", tags=["services"])


# # Helper to handle image saving
# def save_image(upload: UploadFile) -> str:
#     filename = f"{uuid4().hex}_{upload.filename}"
#     path = os.path.join("static/uploads", filename)
#     os.makedirs(os.path.dirname(path), exist_ok=True)
#     with open(path, "wb") as buffer:
#         shutil.copyfileobj(upload.file, buffer)
#     return f"/static/uploads/{filename}"


# # POST: Create New Service
# @router.post("/", response_model=ServiceOut, status_code=status.HTTP_201_CREATED)
# def create_service(
#     name: str = Form(...),
#     description: str = Form(None),
#     price: int = Form(...),
#     status: ServiceStatus = Form(default=ServiceStatus.active),
#     category_id: int = Form(...),
#     sub_category_id: int = Form(...),
#     image: UploadFile = File(None),
#     db: Session = Depends(get_db)
# ):
#     image_path = save_image(image) if image else None

#     service_data = {
#         "name": name,
#         "description": description,
#         "price": price,
#         "status": status,
#         "category_id": category_id,
#         "sub_category_id": sub_category_id,
#         "image": image_path
#     }

#     new_service = service.create_service(db, service.ServiceCreate(**service_data))
#     return new_service


# # GET: List all Services
# @router.get("/", response_model=list[ServiceOut])
# def list_services(db: Session = Depends(get_db)):
#     return service.get_services(db)


# # GET: Get service by ID
# @router.get("/{service_id}", response_model=ServiceOut)
# def get_service(service_id: int, db: Session = Depends(get_db)):
#     service_obj = service.get_service(db, service_id)
#     if not service_obj:
#         raise HTTPException(status_code=404, detail="Service not found")
#     return service_obj


# # PUT: Full update
# @router.put("/{service_id}", response_model=ServiceOut)
# def update_service(
#     service_id: int,
#     name: str = Form(...),
#     description: str = Form(None),
#     price: int = Form(...),
#     status: ServiceStatus = Form(...),
#     category_id: int = Form(...),
#     sub_category_id: int = Form(...),
#     image: UploadFile = File(None),
#     db: Session = Depends(get_db)
# ):
#     service_obj = service.get_service(db, service_id)
#     if not service_obj:
#         raise HTTPException(status_code=404, detail="Service not found")

#     image_path = save_image(image) if image else service_obj.image

#     update_data = {
#         "name": name,
#         "description": description,
#         "price": price,
#         "status": status,
#         "category_id": category_id,
#         "sub_category_id": sub_category_id,
#         "image": image_path
#     }

#     updated_service = service.update_service(
#         db, service_id, service.ServiceUpdate(**update_data)
#     )
#     return updated_service


# # PATCH: Partial update
# @router.patch("/{service_id}", response_model=ServiceOut)
# def partial_update_service(
#     service_id: int,
#     name: str = Form(None),
#     description: str = Form(None),
#     price: float = Form(None),
#     status: ServiceStatus = Form(None),
#     category_id: int = Form(None),
#     sub_category_id: int = Form(None),
#     image: UploadFile = File(None),
#     db: Session = Depends(get_db)
# ):
#     service_obj = service.get_service(db, service_id)
#     print(service_obj)
#     if not service_obj:
#         raise HTTPException(status_code=404, detail="Service not found")

#     update_data = {}

#     if name is not None:
#         update_data["name"] = name
#     if description is not None:
#         update_data["description"] = description
#     if price is not None:
#         update_data["price"] = price
#     if status is not None:
#         update_data["status"] = status
#     if category_id is not None:
#         update_data["category_id"] = category_id
#     if sub_category_id is not None:
#         update_data["sub_category_id"] = sub_category_id
#     if image is not None:
#         update_data["image"] = save_image(image)

#     updated_service = service.update_service(
#         db, service_id, service.ServiceUpdate(**update_data)
#     )
#     return updated_service


# # DELETE: Remove service
# @router.delete("/{service_id}", status_code=status.HTTP_204_NO_CONTENT)
# def delete_service(service_id: int, db: Session = Depends(get_db)):
#     service_obj = service.delete_service(db, service_id)
#     if not service_obj:
#         raise HTTPException(status_code=404, detail="Service not found")


# # POST: Toggle service status
# @router.post("/{service_id}/toggle-status", response_model=ServiceOut)
# def toggle_service_status(service_id: int, db: Session = Depends(get_db)):
#     service_obj = service.toggle_service_status(db, service_id)
#     if not service_obj:
#         raise HTTPException(status_code=404, detail="Service not found")
#     return service_obj
