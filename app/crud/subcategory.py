from sqlalchemy.orm import Session
from app.models.sub_category import SubCategory
from app.schemas.sub_category_schema import SubCategoryCreate, SubCategoryUpdate

def create_subcategory(db: Session, subcategory: SubCategoryCreate):
    db_subcategory = SubCategory(**subcategory.dict())
    db.add(db_subcategory)
    db.commit()
    db.refresh(db_subcategory)
    return db_subcategory

def get_subcategories(db: Session):
    return db.query(SubCategory).all()

def get_subcategory(db: Session, subcategory_id: int):
    return db.query(SubCategory).filter(SubCategory.id == subcategory_id).first()

def update_subcategory(db: Session, subcategory_id: int, subcategory: SubCategoryUpdate):
    db_subcategory = get_subcategory(db, subcategory_id)
    if not db_subcategory:
        return None
    for key, value in subcategory.dict(exclude_unset=True).items():
        setattr(db_subcategory, key, value)
    db.commit()
    db.refresh(db_subcategory)
    return db_subcategory




def delete_subcategory(db: Session, subcategory_id: int):
    db_subcategory = get_subcategory(db, subcategory_id)
    if not db_subcategory:
        return None
    db.delete(db_subcategory)
    db.commit()
    return db_subcategory
