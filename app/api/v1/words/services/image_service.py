from fastapi import HTTPException
from integrations.aws_integration import (
    check_word_images_exist, 
    save_word_image_to_s3, 
    generate_presigned_url_for_image
)
from integrations.google_integration import search_images, download_image
import logging
from typing import List

logger = logging.getLogger(__name__)


def get_word_images(word_id: int, word_name: str) -> List[str]:
    """
    単語の画像URLリストを取得する
    
    処理フロー：
    1. S3に画像が存在するかチェック
    2. 存在すれば署名付きURLを生成して返す
    3. 存在しなければGoogle APIで検索
    4. 画像をダウンロードしてS3に保存
    5. 署名付きURLを生成して返す
    
    Args:
        word_id: 単語ID
        word_name: 単語名（検索クエリとして使用）
    
    Returns:
        署名付き画像URLのリスト（最大4件）
    
    Raises:
        HTTPException: 処理に失敗した場合
    """
    try:
        logger.info(f"Getting images for word_id: {word_id}, word_name: {word_name}")
        
        # ステップ1: S3に画像が存在するかチェック
        existing_image_keys = check_word_images_exist(word_id)
        
        if existing_image_keys:
            # S3に画像が存在する場合、署名付きURLを生成して返す
            logger.info(f"Found {len(existing_image_keys)} images in S3, generating presigned URLs")
            image_urls = []
            for key in existing_image_keys:
                try:
                    url = generate_presigned_url_for_image(key)
                    image_urls.append(url)
                except Exception as e:
                    logger.error(f"Error generating presigned URL for {key}: {str(e)}")
                    continue
            
            if image_urls:
                logger.info(f"Successfully generated {len(image_urls)} presigned URLs")
                return image_urls
        
        # ステップ2: S3に画像がない場合、Google APIで検索
        logger.info(f"Images not found in S3, searching with Google API")
        
        if not word_name:
            raise HTTPException(status_code=404, detail="Word name is required for image search")
        
        try:
            # Google画像検索
            google_image_urls = search_images(word_name, num_results=4)
            
            if not google_image_urls:
                raise HTTPException(
                    status_code=404, 
                    detail=f"No images found for word: {word_name}"
                )
            
            logger.info(f"Found {len(google_image_urls)} images from Google API")
            
        except Exception as e:
            logger.error(f"Error searching images with Google API: {str(e)}")
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to search images: {str(e)}"
            )
        
        # ステップ3: 画像をダウンロードしてS3に保存
        saved_image_keys = []
        
        for index, image_url in enumerate(google_image_urls, start=1):
            try:
                # 画像をダウンロード
                image_content, extension = download_image(image_url)
                
                if image_content is None:
                    logger.warning(f"Failed to download image {index} from {image_url}")
                    continue
                
                # S3に保存
                save_word_image_to_s3(word_id, index, image_content, extension)
                
                # 保存したキーを記録
                image_key = f"images/words/{word_id}/image_{index}.{extension}"
                saved_image_keys.append(image_key)
                
                logger.info(f"Successfully saved image {index} to S3")
                
            except Exception as e:
                logger.error(f"Error processing image {index}: {str(e)}")
                continue
        
        # 少なくとも1枚は保存できているかチェック
        if not saved_image_keys:
            raise HTTPException(
                status_code=500, 
                detail="Failed to download and save any images"
            )
        
        logger.info(f"Successfully saved {len(saved_image_keys)} images to S3")
        
        # ステップ4: 署名付きURLを生成して返す
        image_urls = []
        for key in saved_image_keys:
            try:
                url = generate_presigned_url_for_image(key)
                image_urls.append(url)
            except Exception as e:
                logger.error(f"Error generating presigned URL for {key}: {str(e)}")
                continue
        
        if not image_urls:
            raise HTTPException(
                status_code=500, 
                detail="Failed to generate presigned URLs for images"
            )
        
        logger.info(f"Successfully generated {len(image_urls)} presigned URLs")
        return image_urls
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_word_images for word_id {word_id}: {str(e)}")
        raise HTTPException(
            status_code=500, 
            detail=f"Unexpected error: {str(e)}"
        )
