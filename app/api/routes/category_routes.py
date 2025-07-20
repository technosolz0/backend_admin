from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form, status
from sqlalchemy.orm import Session
from app.schemas.category_schema import CategoryOut, CategoryUpdate, CategoryStatus
from app.core.security import get_db
from app.models.category import Category
import os
import shutil
from uuid import uuid4

router = APIRouter(prefix="/categories", tags=["categories"])

# POST: Create New Category with image
@router.post("/", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
def create_new_category(
    name: str = Form(...),
    status: CategoryStatus = Form(default=CategoryStatus.active),
    image: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    filename = f"{uuid4().hex}_{image.filename}"
    image_path = os.path.join("static/uploads", filename)
    os.makedirs(os.path.dirname(image_path), exist_ok=True)
    with open(image_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    new_category = Category(
        name=name,
        status=status,
        image=f"/static/uploads/{filename}"
    )
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category

# GET: List all categories
@router.get("/", response_model=list[CategoryOut])
def list_all_categories(db: Session = Depends(get_db)):
    return db.query(Category).all()

# GET: Get category by ID
@router.get("/{category_id}", response_model=CategoryOut)
def get_category(category_id: int, db: Session = Depends(get_db)):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category

# PUT: Full update (replace image optional)
@router.put("/{category_id}", response_model=CategoryOut)
def update_category(
    category_id: int,
    name: str = Form(...),
    status: CategoryStatus = Form(default=CategoryStatus.active),
    image: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    # Replace image if provided
    if image:
        filename = f"{uuid4().hex}_{image.filename}"
        image_path = os.path.join("static/uploads", filename)
        os.makedirs(os.path.dirname(image_path), exist_ok=True)
        with open(image_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        category.image = f"/static/uploads/{filename}"

    category.name = name
    category.status = status
    db.commit()
    db.refresh(category)
    return category

# PATCH: Partial update (replace image optional)
@router.patch("/{category_id}", response_model=CategoryOut)
def partial_update_category(
    category_id: int,
    name: str = Form(None),
    status: CategoryStatus = Form(None),
    image: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    if name is not None:
        category.name = name
    if status is not None:
        category.status = status
    if image:
        filename = f"{uuid4().hex}_{image.filename}"
        image_path = os.path.join("static/uploads", filename)
        os.makedirs(os.path.dirname(image_path), exist_ok=True)
        with open(image_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        category.image = f"/static/uploads/{filename}"

    db.commit()
    db.refresh(category)
    return category

# DELETE: Remove category
@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(category_id: int, db: Session = Depends(get_db)):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    db.delete(category)
    db.commit()

# POST: Toggle category status
@router.post("/{category_id}/toggle-status", response_model=CategoryOut)
def toggle_category_status(category_id: int, db: Session = Depends(get_db)):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    category.status = CategoryStatus.inactive if category.status == CategoryStatus.active else CategoryStatus.active
    db.commit()
    db.refresh(category)
    return category