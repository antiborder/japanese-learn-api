from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.crud import component_crud as component_crud
# from app.schemas.component import Component, ComponentCreate
from app.schemas.kanji_component import Component, ComponentCreate
from app.database import get_db

router = APIRouter()

@router.post("/components", response_model=Component)
def create_component(component: ComponentCreate, db: Session = Depends(get_db)):
    return component_crud.create_component(db=db, component=component)

@router.get("/components", response_model=List[Component])
def read_components(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return component_crud.get_components(db, skip=skip, limit=limit)

@router.get("/components/{component_id}", response_model=Component)
def read_component(component_id: int, db: Session = Depends(get_db)):
    db_component = component_crud.get_component(db, component_id=component_id)
    if db_component is None:
        raise HTTPException(status_code=404, detail="Component not found")
    return db_component 