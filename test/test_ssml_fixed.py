#!/usr/bin/env python3
"""
修正されたSSMLテスト用スクリプト
<sub>タグを使用した読み方指定をテスト
"""

import os
import sys
from dotenv import load_dotenv

# .envファイルを読み込み
load_dotenv()

# パスを追加
sys.path.append('/Users/mo/Projects/japanese-learn-api/app/api/v1/words')

from integrations.google_integration import synthesize_speech

def test_fixed_ssml():
    """修正されたSSML音声合成をテスト"""
    test_cases = [
        {
            "name": "修正SSML: 文 + ぶん",
            "word": "文",
            "reading": "ぶん",
            "filename": "test_fixed_ssml_bun.mp3"
        },
        {
            "name": "修正SSML: 北 + きた",
            "word": "北",
            "reading": "きた",
            "filename": "test_fixed_ssml_kita.mp3"
        },
        {
            "name": "修正SSML: 学校 + がっこう",
            "word": "学校",
            "reading": "がっこう",
            "filename": "test_fixed_ssml_gakkou.mp3"
        },
        {
            "name": "比較用: 文のみ",
            "word": "文",
            "reading": None,
            "filename": "test_normal_bun_compare.mp3"
        },
        {
            "name": "比較用: ぶんのみ",
            "word": "ぶん",
            "reading": None,
            "filename": "test_normal_bun_hiragana_compare.mp3"
        }
    ]
    
    print("=== 修正されたSSML音声合成テスト ===")
    print("使用するSSML: <sub alias='読み方'>漢字</sub>")
    print()
    
    for i, test_case in enumerate(test_cases, 1):
        try:
            print(f"{i}. {test_case['name']}")
            print(f"   漢字: {test_case['word']}")
            print(f"   読み方: {test_case['reading'] if test_case['reading'] else 'なし'}")
            
            # 音声合成を実行
            audio_content = synthesize_speech(test_case['word'], test_case['reading'])
            
            # 音声ファイルを保存
            with open(test_case['filename'], "wb") as f:
                f.write(audio_content)
            
            print(f"   ✅ 成功! ファイル: {test_case['filename']} ({len(audio_content)} bytes)")
            print()
            
        except Exception as e:
            print(f"   ❌ エラー: {str(e)}")
            print()
    
    print("=== テスト完了 ===")
    print("生成されたファイル:")
    for test_case in test_cases:
        if os.path.exists(test_case['filename']):
            size = os.path.getsize(test_case['filename'])
            print(f"- {test_case['filename']} ({size} bytes)")
    
    print("\n各ファイルを再生して音声を確認してください。")
    print("特に以下の比較が重要です:")
    print("1. test_fixed_ssml_bun.mp3 (修正SSML: 文+ぶん)")
    print("2. test_normal_bun_compare.mp3 (通常: 文のみ)")
    print("3. test_normal_bun_hiragana_compare.mp3 (通常: ぶんのみ)")

if __name__ == "__main__":
    test_fixed_ssml()
