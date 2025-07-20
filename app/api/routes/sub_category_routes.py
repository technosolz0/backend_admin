from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form, status
from sqlalchemy.orm import Session
from app.core.security import get_db
from app.models.sub_category import SubCategory
from app.schemas.sub_category_schema import SubCategoryOut, SubCategoryStatus
import os, shutil
from uuid import uuid4

router = APIRouter(prefix="/subcategories", tags=["subcategories"])

@router.post("/", response_model=SubCategoryOut, status_code=status.HTTP_201_CREATED)
def create_sub_category(
    name: str = Form(...),
    status: SubCategoryStatus = Form(default=SubCategoryStatus.active),
    category_id: int = Form(...),
    image: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    image_path = None
    if image:
        filename = f"{uuid4().hex}_{image.filename}"
        image_path = os.path.join("static/uploads", filename)
        os.makedirs(os.path.dirname(image_path), exist_ok=True)
        with open(image_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        image_path = f"/static/uploads/{filename}"

    new_sub_category = SubCategory(
        name=name,
        status=status,
        category_id=category_id,
        image=image_path
    )
    db.add(new_sub_category)
    db.commit()
    db.refresh(new_sub_category)
    return new_sub_category

@router.get("/", response_model=list[SubCategoryOut])
def list_sub_categories(db: Session = Depends(get_db)):
    return db.query(SubCategory).all()

@router.get("/{sub_category_id}", response_model=SubCategoryOut)
def get_sub_category(sub_category_id: int, db: Session = Depends(get_db)):
    sub_category = db.query(SubCategory).filter(SubCategory.id == sub_category_id).first()
    if not sub_category:
        raise HTTPException(status_code=404, detail="Sub-category not found")
    return sub_category

@router.put("/{sub_category_id}", response_model=SubCategoryOut)
def update_sub_category(
    sub_category_id: int,
    name: str = Form(...),
    status: SubCategoryStatus = Form(...),
    category_id: int = Form(...),
    image: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    sub_category = db.query(SubCategory).filter(SubCategory.id == sub_category_id).first()
    if not sub_category:
        raise HTTPException(status_code=404, detail="Sub-category not found")

    if image:
        filename = f"{uuid4().hex}_{image.filename}"
        image_path = os.path.join("static/uploads", filename)
        os.makedirs(os.path.dirname(image_path), exist_ok=True)
        with open(image_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        sub_category.image = f"/static/uploads/{filename}"

    sub_category.name = name
    sub_category.status = status
    sub_category.category_id = category_id

    db.commit()
    db.refresh(sub_category)
    return sub_category

@router.patch("/{sub_category_id}", response_model=SubCategoryOut)
def partial_update_sub_category(
    sub_category_id: int,
    name: str = Form(None),
    status: SubCategoryStatus = Form(None),
    category_id: int = Form(None),
    image: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    sub_category = db.query(SubCategory).filter(SubCategory.id == sub_category_id).first()
    if not sub_category:
        raise HTTPException(status_code=404, detail="Sub-category not found")

    if name:
        sub_category.name = name
    if status:
        sub_category.status = status
    if category_id:
        sub_category.category_id = category_id
    if image:
        filename = f"{uuid4().hex}_{image.filename}"
        image_path = os.path.join("static/uploads", filename)
        os.makedirs(os.path.dirname(image_path), exist_ok=True)
        with open(image_path, "wb") as buffer:
            shutil.copyfileobj(image.file, buffer)
        sub_category.image = f"/static/uploads/{filename}"

    db.commit()
    db.refresh(sub_category)
    return sub_category

@router.delete("/{sub_category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sub_category(sub_category_id: int, db: Session = Depends(get_db)):
    sub_category = db.query(SubCategory).filter(SubCategory.id == sub_category_id).first()
    if not sub_category:
        raise HTTPException(status_code=404, detail="Sub-category not found")
    db.delete(sub_category)
    db.commit()

@router.post("/{sub_category_id}/toggle-status", response_model=SubCategoryOut)
def toggle_sub_category_status(sub_category_id: int, db: Session = Depends(get_db)):
    sub_category = db.query(SubCategory).filter(SubCategory.id == sub_category_id).first()
    if not sub_category:
        raise HTTPException(status_code=404, detail="Sub-category not found")
    sub_category.status = 'Inactive' if sub_category.status == 'Active' else 'Active'
    db.commit()
    db.refresh(sub_category)
    return sub_category
