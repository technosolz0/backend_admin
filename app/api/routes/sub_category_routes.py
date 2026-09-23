from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form, status
from sqlalchemy.orm import Session
from app.core.security import get_db
from app.models.sub_category import SubCategory
from app.schemas.sub_category_schema import SubCategoryOut, SubCategoryStatus
from app.core.firebase_storage import upload_to_firebase, delete_from_firebase
import os

router = APIRouter(prefix="/subcategories", tags=["subcategories"])


def save_image(image: UploadFile, folder_id: int = None, old_image: str = None) -> str:
    """Save uploaded image to Firebase Storage, delete old if exists, return new URL."""
    if old_image:
        delete_from_firebase(old_image)

    folder = f"subcategories/{folder_id}" if folder_id else "subcategories"
    return upload_to_firebase(image, folder_path=folder)


@router.post("/", response_model=SubCategoryOut, status_code=status.HTTP_201_CREATED)
def create_sub_category(
    name: str = Form(...),
    status: SubCategoryStatus = Form(default=SubCategoryStatus.active),
    category_id: int = Form(...),
    service_charge: float = Form(default=0.0),
    image: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    image_path = save_image(image, folder_id=category_id) if image else None

    new_sub_category = SubCategory(
        name=name,
        status=status,
        category_id=category_id,
        service_charge=service_charge,
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


@router.get("/by-category/{category_id}", response_model=list[SubCategoryOut])
def get_subcategories_by_category(category_id: int, db: Session = Depends(get_db)):
    subcategories = db.query(SubCategory).filter(SubCategory.category_id == category_id).all()
    if not subcategories:
        raise HTTPException(status_code=404, detail="No subcategories found for this category")
    return subcategories


@router.put("/{sub_category_id}", response_model=SubCategoryOut)
def update_sub_category(
    sub_category_id: int,
    name: str = Form(...),
    status: SubCategoryStatus = Form(...),
    category_id: int = Form(...),
    service_charge: float = Form(...),
    image: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    sub_category = db.query(SubCategory).filter(SubCategory.id == sub_category_id).first()
    if not sub_category:
        raise HTTPException(status_code=404, detail="Sub-category not found")

    if image:
        sub_category.image = save_image(image, folder_id=category_id, old_image=sub_category.image)

    sub_category.name = name
    sub_category.status = status
    sub_category.category_id = category_id
    sub_category.service_charge = service_charge

    db.commit()
    db.refresh(sub_category)
    return sub_category


@router.patch("/{sub_category_id}", response_model=SubCategoryOut)
def partial_update_sub_category(
    sub_category_id: int,
    name: str = Form(None),
    status: SubCategoryStatus = Form(None),
    category_id: int = Form(None),
    service_charge: float = Form(None),
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
    if service_charge is not None:
        sub_category.service_charge = service_charge
    if image:
        target_cat = category_id if category_id else sub_category.category_id
        sub_category.image = save_image(image, folder_id=target_cat, old_image=sub_category.image)

    db.commit()
    db.refresh(sub_category)
    return sub_category


@router.delete("/{sub_category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_sub_category(sub_category_id: int, db: Session = Depends(get_db)):
    sub_category = db.query(SubCategory).filter(SubCategory.id == sub_category_id).first()
    if not sub_category:
        raise HTTPException(status_code=404, detail="Sub-category not found")

    if sub_category.image:
        delete_from_firebase(sub_category.image)

    db.delete(sub_category)
    db.commit()


@router.post("/{sub_category_id}/toggle-status", response_model=SubCategoryOut)
def toggle_sub_category_status(sub_category_id: int, db: Session = Depends(get_db)):
    sub_category = db.query(SubCategory).filter(SubCategory.id == sub_category_id).first()
    if not sub_category:
        raise HTTPException(status_code=404, detail="Sub-category not found")

    sub_category.status = (
        SubCategoryStatus.inactive
        if sub_category.status == SubCategoryStatus.active
        else SubCategoryStatus.active
    )
    db.commit()
    db.refresh(sub_category)
    return sub_category
