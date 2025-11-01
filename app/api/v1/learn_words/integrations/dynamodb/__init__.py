"""
DynamoDB integrations package for Japanese Learn API - Learning History
"""
from .learn import LearnDynamoDB
from .next import NextDynamoDB

# 既存のAPIとの互換性のため、メインのインスタンスを提供
learn_history_db = LearnDynamoDB()
next_db = NextDynamoDB() 