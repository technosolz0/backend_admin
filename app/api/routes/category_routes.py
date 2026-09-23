from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Form, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from app.schemas.category_schema import CategoryOut, CategoryStatus
from app.core.security import get_db
from app.models.category import Category
from app.utils.image_utils import compress_image
from app.core.redis import get_cache, set_cache, delete_cache_pattern
from app.core.firebase_storage import upload_to_firebase, delete_from_firebase
import os

router = APIRouter(prefix="/categories", tags=["categories"])

# -------------------------------------------------------------------
# POST: Create New Category with compressed image
# -------------------------------------------------------------------
@router.post("/", response_model=CategoryOut, status_code=status.HTTP_201_CREATED)
async def create_new_category(
    name: str = Form(...),
    status: CategoryStatus = Form(default=CategoryStatus.active),
    image: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    new_category = Category(
        name=name,
        status=status,
        image=""
    )
    db.add(new_category)
    db.flush()

    # Compress before saving to Firebase Storage
    compressed = compress_image(image, max_size=(800, 800), quality=75)
    image_url = upload_to_firebase(
        compressed,
        folder_path=f"categories/{new_category.id}",
        content_type="image/jpeg"
    )
    new_category.image = image_url

    db.commit()
    db.refresh(new_category)

    # Invalidate category cache
    await delete_cache_pattern("categories:*")
    return new_category

# -------------------------------------------------------------------
# GET: List all categories
# -------------------------------------------------------------------
@router.get("/", response_model=list[CategoryOut])
async def list_all_categories(db: Session = Depends(get_db)):
    cache_key = "categories:all"
    cached_categories = await get_cache(cache_key)
    if cached_categories is not None:
        return cached_categories

    categories = db.query(Category).all()
    categories_json = jsonable_encoder(categories)
    await set_cache(cache_key, categories_json, ttl_seconds=1800)  # 30 mins
    return categories

# -------------------------------------------------------------------
# GET: Get category by ID
# -------------------------------------------------------------------
@router.get("/{category_id}", response_model=CategoryOut)
async def get_category(category_id: int, db: Session = Depends(get_db)):
    cache_key = f"categories:id:{category_id}"
    cached_category = await get_cache(cache_key)
    if cached_category is not None:
        return cached_category

    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    category_json = jsonable_encoder(category)
    await set_cache(cache_key, category_json, ttl_seconds=1800)
    return category

# -------------------------------------------------------------------
# PUT: Full update (replace image optional, compressed)
# -------------------------------------------------------------------
@router.put("/{category_id}", response_model=CategoryOut)
async def update_category(
    category_id: int,
    name: str = Form(...),
    status: CategoryStatus = Form(default=CategoryStatus.active),
    image: UploadFile = File(None),
    db: Session = Depends(get_db)
):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    if image:
        if category.image:
            delete_from_firebase(category.image)

        compressed = compress_image(image, max_size=(800, 800), quality=75)
        category.image = upload_to_firebase(
            compressed,
            folder_path=f"categories/{category_id}",
            content_type="image/jpeg"
        )

    category.name = name
    category.status = status
    db.commit()
    db.refresh(category)

    await delete_cache_pattern("categories:*")
    return category

# -------------------------------------------------------------------
# PATCH: Partial update (replace image optional, compressed)
# -------------------------------------------------------------------
@router.patch("/{category_id}", response_model=CategoryOut)
async def partial_update_category(
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
        if category.image:
            delete_from_firebase(category.image)

        compressed = compress_image(image, max_size=(800, 800), quality=75)
        category.image = upload_to_firebase(
            compressed,
            folder_path=f"categories/{category_id}",
            content_type="image/jpeg"
        )

    db.commit()
    db.refresh(category)

    await delete_cache_pattern("categories:*")
    return category

# -------------------------------------------------------------------
# DELETE: Remove category
# -------------------------------------------------------------------
@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(category_id: int, db: Session = Depends(get_db)):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    if category.image:
        delete_from_firebase(category.image)

    db.delete(category)
    db.commit()

    await delete_cache_pattern("categories:*")

# -------------------------------------------------------------------
# POST: Toggle category status
# -------------------------------------------------------------------
@router.post("/{category_id}/toggle-status", response_model=CategoryOut)
async def toggle_category_status(category_id: int, db: Session = Depends(get_db)):
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")

    category.status = (
        CategoryStatus.inactive if category.status == CategoryStatus.active else CategoryStatus.active
    )
    db.commit()
    db.refresh(category)

    await delete_cache_pattern("categories:*")
    return category

