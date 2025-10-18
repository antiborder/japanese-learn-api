"""
DynamoDB integrations package for Users API
"""
from .progress import ProgressDynamoDB
from .plan import PlanDynamoDB

# インスタンスを提供
progress_db = ProgressDynamoDB()
plan_db = PlanDynamoDB()
