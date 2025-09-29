import logging
import random
from decimal import Decimal

logger = logging.getLogger(__name__)

PROFICIENCY_THRESHOLD = Decimal('0.4')  # 習熟度の差の閾値

class ModeService:
    def determine_next_mode(self, proficiency_MJ: Decimal, proficiency_JM: Decimal) -> str:
        """次の学習モードを決定します
        
        Args:
            proficiency_MJ: MJモードの習熟度（0-1）
            proficiency_JM: JMモードの習熟度（0-1）
            
        Returns:
            str: 次の学習モード（"MJ" または "JM"）
        """
        # 習熟度の差を計算
        proficiency_diff = proficiency_MJ - proficiency_JM
        
        # 差が-0.4以下の場合、MJになる確率100%
        if proficiency_diff <= -PROFICIENCY_THRESHOLD:
            return "MJ"
        
        # 差が0.4以上の場合、JMになる確率100%
        if proficiency_diff >= PROFICIENCY_THRESHOLD:
            return "JM"
        
        # その他の場合、線形に確率を計算
        # -0.4から0.4の範囲を0から1の範囲にマッピング
        jm_probability = (proficiency_diff + PROFICIENCY_THRESHOLD) / (PROFICIENCY_THRESHOLD * Decimal('2'))
        
        # 確率に基づいてモードを決定
        return "JM" if random.random() < float(jm_probability) else "MJ"
