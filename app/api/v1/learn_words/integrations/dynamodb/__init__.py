"""
DynamoDB integrations package for Japanese Learn API - Learning History
"""
from .learn import LearnDynamoDB
from .next import NextDynamoDB
from .progress import ProgressDynamoDB
from .plan import PlanDynamoDB

# 既存のAPIとの互換性のため、メインのインスタンスを提供
learn_history_db = LearnDynamoDB()
next_db = NextDynamoDB()
progress_db = ProgressDynamoDB()
plan_db = PlanDynamoDB() 