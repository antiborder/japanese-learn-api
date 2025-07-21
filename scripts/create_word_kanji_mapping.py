#!/usr/bin/env python3
"""
単語と漢字の紐付けデータを作成するスクリプト

使用方法:
python scripts/create_word_kanji_mapping.py

このスクリプトは以下の処理を行います:
1. data/dynamodb_source/words_XXXXXXXX.csvのname列から漢字を抽出
2. その漢字がdata/dynamodb_source/kanjis_XXXXXXXX.csvに存在するかチェック
3. 存在する場合、word_kanji_YYYYMMDD.csvとkanji_word_YYYYMMDD.csvを作成
"""

import csv
import os
import re
import glob
from datetime import datetime, timezone
from typing import Set, Dict, List, Tuple

def extract_kanji_from_text(text: str) -> Set[str]:
    """
    テキストから漢字を抽出する
    
    Args:
        text: 漢字を含むテキスト
        
    Returns:
        抽出された漢字のセット
    """
    # 漢字のUnicode範囲: 4E00-9FFF (CJK統合漢字)
    kanji_pattern = re.compile(r'[\u4e00-\u9fff]')
    kanji_chars = set(kanji_pattern.findall(text))
    return kanji_chars

def load_kanji_ids(kanji_file_path: str) -> Dict[str, int]:
    """
    漢字ファイルから漢字文字とIDのマッピングを読み込む
    
    Args:
        kanji_file_path: 漢字CSVファイルのパス
        
    Returns:
        漢字文字をキー、IDを値とする辞書
    """
    kanji_ids = {}
    
    try:
        with open(kanji_file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                character = row.get('character', '').strip()
                kanji_id = int(row.get('SK', '0'))
                if character:
                    kanji_ids[character] = kanji_id
    except FileNotFoundError:
        print(f"警告: 漢字ファイル {kanji_file_path} が見つかりません")
    except Exception as e:
        print(f"エラー: 漢字ファイル {kanji_file_path} の読み込みに失敗: {e}")
    
    return kanji_ids

def load_words(words_file_path: str) -> List[Tuple[int, str]]:
    """
    単語ファイルから単語IDと名前のリストを読み込む
    
    Args:
        words_file_path: 単語CSVファイルのパス
        
    Returns:
        (単語ID, 単語名)のタプルのリスト
    """
    words = []
    
    try:
        with open(words_file_path, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                word_id = int(row.get('SK', '0'))
                word_name = row.get('name', '').strip()
                if word_name:
                    words.append((word_id, word_name))
    except FileNotFoundError:
        print(f"エラー: 単語ファイル {words_file_path} が見つかりません")
    except Exception as e:
        print(f"エラー: 単語ファイル {words_file_path} の読み込みに失敗: {e}")
    
    return words

def create_mapping_files(words_file_path: str, kanji_file_path: str, output_date: str):
    """
    単語と漢字の紐付けファイルを作成する
    
    Args:
        words_file_path: 単語CSVファイルのパス
        kanji_file_path: 漢字CSVファイルのパス
        output_date: 出力ファイルの日付 (YYYYMMDD形式)
    """
    print(f"処理開始: {words_file_path} -> {kanji_file_path}")
    
    # 漢字IDのマッピングを読み込み
    kanji_ids = load_kanji_ids(kanji_file_path)
    print(f"読み込まれた漢字数: {len(kanji_ids)}")
    
    # 単語リストを読み込み
    words = load_words(words_file_path)
    print(f"読み込まれた単語数: {len(words)}")
    
    # 紐付けデータを収集
    word_kanji_mappings = []  # WORD#id,KANJI#id,word,kanji
    kanji_word_mappings = []  # KANJI#id,WORD#id,word,kanji
    
    for word_id, word_name in words:
        # 単語から漢字を抽出
        kanji_chars = extract_kanji_from_text(word_name)
        
        for kanji_char in kanji_chars:
            # 漢字が存在するかチェック
            if kanji_char in kanji_ids:
                kanji_id = kanji_ids[kanji_char]
                
                # word_kanji_YYYYMMDD.csv用のデータ
                word_kanji_mappings.append({
                    'PK': f'WORD#{word_id}',
                    'SK': f'KANJI#{kanji_id}',
                    'word': word_name,
                    'kanji': kanji_char,
                    'EntityType': 'WordKanji'
                })
                
                # kanji_word_YYYYMMDD.csv用のデータ
                kanji_word_mappings.append({
                    'PK': f'KANJI#{kanji_id}',
                    'SK': f'WORD#{word_id}',
                    'word': word_name,
                    'kanji': kanji_char,
                    'EntityType': 'KanjiWord'
                })
    
    print(f"作成された紐付け数: {len(word_kanji_mappings)}")
    
    # word_kanji_YYYYMMDD.csvを作成
    word_kanji_file = f'data/dynamodb_source/word_kanji_{output_date}.csv'
    with open(word_kanji_file, 'w', encoding='utf-8', newline='') as file:
        fieldnames = ['PK', 'SK', 'word', 'kanji', 'EntityType']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(word_kanji_mappings)
    
    print(f"作成完了: {word_kanji_file}")
    
    # kanji_word_YYYYMMDD.csvを作成
    kanji_word_file = f'data/dynamodb_source/kanji_word_{output_date}.csv'
    with open(kanji_word_file, 'w', encoding='utf-8', newline='') as file:
        fieldnames = ['PK', 'SK', 'word', 'kanji', 'EntityType']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(kanji_word_mappings)
    
    print(f"作成完了: {kanji_word_file}")

def find_data_files() -> List[Tuple[str, str]]:
    """
    dataディレクトリから単語ファイルと漢字ファイルのペアを探す
    
    Returns:
        (単語ファイルパス, 漢字ファイルパス)のタプルのリスト
    """
    # 単語ファイルを探す
    word_files = glob.glob('data/dynamodb_source/words_*.csv')
    kanji_files = glob.glob('data/dynamodb_source/kanjis_*.csv')
    
    file_pairs = []
    for word_file in word_files:
        if kanji_files:
            file_pairs.append((word_file, kanji_files[0]))  # 最初の1つだけペア
    
    return file_pairs

def main():
    """メイン処理"""
    print("単語と漢字の紐付けデータ作成スクリプト")
    print("=" * 50)
    
    # 出力日付を取得
    output_date = datetime.now(timezone.utc).strftime('%Y%m%d')
    print(f"出力日付: {output_date}")
    
    # データファイルを探す
    file_pairs = find_data_files()
    
    if not file_pairs:
        print("エラー: 処理対象のファイルが見つかりません")
        print("data/dynamodb_source/words_XXXXXXXX.csv と data/dynamodb_source/kanjis_XXXXXXXX.csv のペアが必要です")
        return
    
    print(f"処理対象ファイル数: {len(file_pairs)}")
    
    # 各ファイルペアを処理
    for word_file, kanji_file in file_pairs:
        print(f"\n処理中: {word_file} -> {kanji_file}")
        create_mapping_files(word_file, kanji_file, output_date)
    
    print("\n処理完了!")

if __name__ == "__main__":
    main() 