from fastapi import APIRouter, HTTPException, Query
from typing import List
from common.schemas.component import Component, PaginatedComponentsResponse, PaginationInfo
from integrations.dynamodb.component import component_db
import logging
import math

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/", response_model=PaginatedComponentsResponse)
def read_components(
    page: int = Query(1, ge=1, description="ページ番号（1から開始）"),
    limit: int = Query(1000, ge=1, le=1000, description="1ページあたりの件数（最大: 1000）")
):
    """
    コンポーネント一覧を取得します（ページネーション対応）。
    DynamoDBからコンポーネントデータを取得し、指定された形式に変換して返します。
    """
    try:
        # ページネーション計算
        skip = (page - 1) * limit
        
        # 総件数を取得
        total = component_db.count_components()
        
        # DynamoDBからコンポーネントデータを取得
        components_data = component_db.get_components(skip=skip, limit=limit)
        components = [
            Component(
                id=item['SK'],
                character=item.get('character'),
                name=item.get('name'),
                en=item.get('en'),
                vi=item.get('vi'),
                kanjis=None
            )
            for item in components_data
        ]
        
        # ページネーション情報を計算
        total_pages = math.ceil(total / limit) if total > 0 else 0
        has_next = page < total_pages
        has_previous = page > 1
        
        return PaginatedComponentsResponse(
            data=components,
            pagination=PaginationInfo(
                page=page,
                limit=limit,
                total=total,
                total_pages=total_pages,
                has_next=has_next,
                has_previous=has_previous
            )
        )
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
            id=component['SK'],
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

@router.get("/{component_id}/kanjis", response_model=List[dict])
def get_kanjis_by_component_id(component_id: str):
    try:
        return component_db.get_kanjis_by_component_id(str(component_id))
    except Exception as e:
        logger.error(f"Error getting kanjis for component {component_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal Server Error") 