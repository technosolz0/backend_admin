# app/crud/category.py
from sqlalchemy.orm import Session
from app.models.category import Category
from app.schemas.category_schema import CategoryCreate

def create_category(db: Session, category: CategoryCreate):
    db_category = Category(**category.dict())
    db.add(db_category)
    db.commit()
    db.refresh(db_category)
    return db_category

def get_categories(db: Session):
    return db.query(Category).all()
