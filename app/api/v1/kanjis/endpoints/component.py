from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from crud import component_crud
from common.schemas.kanji_component import Component, ComponentCreate
from common.database import get_db, Base
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/", response_model=Component)
def create_component(component: ComponentCreate, db: Session = Depends(get_db)):
    try:
        return component_crud.create_component(db=db, component=component)
    except Exception as e:
        logger.error(f"Error creating component: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/", response_model=List[Component])
def read_components(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    try:
        return component_crud.get_components(db, skip=skip, limit=limit)
    except Exception as e:
        logger.error(f"Error reading components: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/{component_id}", response_model=Component)
def read_component(component_id: int, db: Session = Depends(get_db)):
    try:
        component = component_crud.get_component(db, component_id=component_id)
        if component is None:
            raise HTTPException(status_code=404, detail="Component not found")
        return component
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error reading component {component_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error") 