# from app.schemas.category_schema import CategoryOut
# from app.schemas.sub_category_schema import SubCategoryOut
# from pydantic import BaseModel
# from typing import Optional
# from enum import Enum
# from app.schemas.category_schema import CategoryOut
# from app.schemas.sub_category_schema import SubCategoryOut


# class ServiceStatus(str, Enum):
#     active = "Active"
#     inactive = "Inactive"

# class ServiceBase(BaseModel):
#     name: str
#     description: Optional[str]
#     price: int
#     status: ServiceStatus
#     category_id: int
#     sub_category_id: int
#     image: Optional[str] = None

# class ServiceCreate(ServiceBase):
#     pass

# class ServiceUpdate(BaseModel):
#     name: Optional[str]
#     description: Optional[str]
#     price: Optional[int]
#     status: Optional[ServiceStatus]
#     category_id: Optional[int]
#     sub_category_id: Optional[int]
#     image: Optional[str]


# class ServiceOut(BaseModel):
#     id: int
#     name: str
#     description: Optional[str]
#     price: int
#     status: ServiceStatus
#     category: CategoryOut
#     sub_category: SubCategoryOut
#     image: Optional[str]

#     class Config:
#         from_attributes = True
