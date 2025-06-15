from fastapi import APIRouter, HTTPException
from typing import List
from common.schemas.component import Component
from integrations.dynamodb.component import component_db
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/", response_model=List[Component])
def read_components(skip: int = 0, limit: int = 100):
    try:
        components = component_db.get_components(skip=skip, limit=limit)
        return [
            Component(
                character=item.get('character'),
                name=item.get('name'),
                en=item.get('en'),
                vi=item.get('vi'),
                kanjis=None
            )
            for item in components
        ]
    except Exception as e:
        logger.error(f"Error reading components: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error")

@router.get("/{component_id}", response_model=Component)
def read_component(component_id: str):
    try:
        component = component_db.get_component(component_id=component_id)
        logger.info(f"Raw component data from DynamoDB: {component}")
        if component is None:
            raise HTTPException(status_code=404, detail="Component not found")
        return Component(
            character=component.get('character'),
            name=component.get('name'),
            en=component.get('en'),
            vi=component.get('vi'),
            kanjis=None
        )
    except HTTPException as he:
        raise he
    except Exception as e:
        logger.error(f"Error reading component {component_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error") 