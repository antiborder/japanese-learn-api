"""
DynamoDB integrations package for Users API
"""
from .progress import ProgressDynamoDB
from .plan import PlanDynamoDB
from .sentences_progress import SentencesProgressDynamoDB
from .sentences_plan import SentencesPlanDynamoDB
from .kana_progress import KanaProgressDynamoDB
from .kana_plan import KanaPlanDynamoDB
from .user_settings import UserSettingsDynamoDB

# インスタンスを提供
progress_db = ProgressDynamoDB()
plan_db = PlanDynamoDB()
sentences_progress_db = SentencesProgressDynamoDB()
sentences_plan_db = SentencesPlanDynamoDB()
kana_progress_db = KanaProgressDynamoDB()
kana_plan_db = KanaPlanDynamoDB()
user_settings_db = UserSettingsDynamoDB()
