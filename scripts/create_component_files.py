#!/usr/bin/env python3
"""
コンポーネント関連のCSVファイルを作成するプログラム

1. components_XXXXXXXX.csv - 重複なしのコンポーネント一覧
2. kanji_component_XXXXXXXX.csv - 漢字からコンポーネントへの関係
3. component_kanji_XXXXXXXX.csv - コンポーネントから漢字への関係
"""

import csv
import os
import glob
from typing import List, Tuple, Dict
from datetime import datetime, timezone

def read_component_relations(file_path: str) -> List[Tuple[str, List[str]]]:
    """コンポーネント関係ファイルを読み込む"""
    relations = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            kanji = row.get('kanji', '').strip()
            components_str = row.get('components', '').strip()
            
            if kanji and components_str:
                # コンポーネントをカンマで分割
                components = [comp.strip() for comp in components_str.split(',') if comp.strip()]
                relations.append((kanji, components))
    
    return relations

def extract_unique_components(relations: List[Tuple[str, List[str]]]) -> List[str]:
    """重複なしのコンポーネントを抽出"""
    unique_components = set()
    for _, components in relations:
        unique_components.update(components)
    return sorted(list(unique_components))

def get_kanji_id_mapping() -> Dict[str, str]:
    """既存の漢字ファイルから漢字IDマッピングを取得"""
    kanji_to_id = {}
    
    # 漢字ファイルを探す
    kanji_files = glob.glob('data/dynamodb_source/kanjis_*.csv')
    if not kanji_files:
        print("警告: 漢字ファイルが見つかりません")
        return kanji_to_id
    
    kanji_file = kanji_files[0]  # 最初のファイルを使用
    
    with open(kanji_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            kanji_char = row.get('char', '').strip()
            kanji_id = row.get('id', '').strip()
            if kanji_char and kanji_id:
                kanji_to_id[kanji_char] = kanji_id
    
    return kanji_to_id

def create_components_csv(components: List[str], output_path: str) -> Dict[str, str]:
    """components_XXXXXXXX.csvを作成し、コンポーネントIDマッピングを返す"""
    component_to_id = {}
    
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['PK', 'SK', 'char', 'EntityType'])
        
        for i, component in enumerate(components, 1):
            component_id = str(i)
            component_to_id[component] = component_id
            writer.writerow(['COMPONENT', component_id, component, 'Component'])
    
    return component_to_id

def create_kanji_component_csv(relations: List[Tuple[str, List[str]]], output_path: str,
                              kanji_to_id: Dict[str, str], component_to_id: Dict[str, str]):
    """kanji_component_XXXXXXXX.csvを作成"""
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['PK', 'SK', 'kanji_char', 'component_char', '', '', 'EntityType'])
        
        for kanji, components in relations:
            kanji_id = kanji_to_id.get(kanji, '')
            if not kanji_id:
                print(f"警告: 漢字 '{kanji}' のIDが見つかりません")
                continue
                
            for component in components:
                component_id = component_to_id.get(component, '')
                if not component_id:
                    print(f"警告: コンポーネント '{component}' のIDが見つかりません")
                    continue
                    
                writer.writerow([f'KANJI#{kanji_id}', f'COMPONENT#{component_id}', kanji, component, '', '', 'KanjiComponent'])

def create_component_kanji_csv(relations: List[Tuple[str, List[str]]], output_path: str,
                              kanji_to_id: Dict[str, str], component_to_id: Dict[str, str]):
    """component_kanji_XXXXXXXX.csvを作成"""
    with open(output_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['PK', 'SK', 'kanji_char', 'component_char', '', '', 'EntityType'])
        
        for kanji, components in relations:
            kanji_id = kanji_to_id.get(kanji, '')
            if not kanji_id:
                print(f"警告: 漢字 '{kanji}' のIDが見つかりません")
                continue
                
            for component in components:
                component_id = component_to_id.get(component, '')
                if not component_id:
                    print(f"警告: コンポーネント '{component}' のIDが見つかりません")
                    continue
                    
                writer.writerow([f'COMPONENT#{component_id}', f'KANJI#{kanji_id}', kanji, component, '', '', 'ComponentKanji'])

def main():
    # ファイルパス設定
    input_file = 'data/component_relation_source/component_relation_source.csv'
    output_dir = 'data/dynamodb_source'
    
    # 出力ディレクトリが存在しない場合は作成
    os.makedirs(output_dir, exist_ok=True)
    
    # 現在の日時を取得してファイル名に使用
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
    
    # ファイル名を設定
    components_file = f'components_{timestamp}.csv'
    kanji_component_file = f'kanji_component_{timestamp}.csv'
    component_kanji_file = f'component_kanji_{timestamp}.csv'
    
    # ファイルパスを設定
    components_path = os.path.join(output_dir, components_file)
    kanji_component_path = os.path.join(output_dir, kanji_component_file)
    component_kanji_path = os.path.join(output_dir, component_kanji_file)
    
    print(f"入力ファイル: {input_file}")
    print(f"出力ディレクトリ: {output_dir}")
    print(f"タイムスタンプ: {timestamp}")
    print()
    
    # 既存の漢字IDマッピングを取得
    print("既存の漢字IDマッピングを取得中...")
    kanji_to_id = get_kanji_id_mapping()
    print(f"取得完了: {len(kanji_to_id)}個の漢字ID")
    
    # コンポーネント関係を読み込み
    print("コンポーネント関係を読み込み中...")
    relations = read_component_relations(input_file)
    print(f"読み込み完了: {len(relations)}個の漢字")
    
    # 重複なしのコンポーネントを抽出
    print("重複なしのコンポーネントを抽出中...")
    unique_components = extract_unique_components(relations)
    print(f"抽出完了: {len(unique_components)}個のコンポーネント")
    
    # componentsファイルを作成し、コンポーネントIDマッピングを取得
    print(f"\n{components_file}を作成中...")
    component_to_id = create_components_csv(unique_components, components_path)
    print(f"作成完了: {components_path}")
    
    # kanji_componentファイルを作成
    print(f"\n{kanji_component_file}を作成中...")
    create_kanji_component_csv(relations, kanji_component_path, kanji_to_id, component_to_id)
    print(f"作成完了: {kanji_component_path}")
    
    # component_kanjiファイルを作成
    print(f"\n{component_kanji_file}を作成中...")
    create_component_kanji_csv(relations, component_kanji_path, kanji_to_id, component_to_id)
    print(f"作成完了: {component_kanji_path}")
    
    print(f"\n全てのファイルが正常に作成されました！")
    print(f"作成されたファイル:")
    print(f"  - {components_file}")
    print(f"  - {kanji_component_file}")
    print(f"  - {component_kanji_file}")

if __name__ == "__main__":
    main() 