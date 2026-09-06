#!/usr/bin/env python3
"""
タグ×単語の意味的な紐付けを増やすためのスクリプト。

3段階のサブコマンドに分かれている（安全のため、それぞれ明示的に実行する必要がある）。

  suggest  : 読み取り専用。全タグ・全単語の embedding からコサイン類似度を計算し、
             候補を「confident（自動採用候補）」「borderline（要LLM確認）」に振り分けて
             scripts/output/tag_suggestions.json に書き出す。DynamoDBへの書き込みは無い。

  verify   : suggestの出力を読み込み、borderline候補についてGeminiに「この単語にこのタグは
             意味的に当てはまるか」を確認させ、確認結果を
             scripts/output/tag_suggestions_verified.json に書き出す。DynamoDBへの書き込みは無い。

  apply    : verifyの出力を読み込み、--confirm を明示的に付けた場合のみDynamoDBのWORD項目に
             タグを追記する（既存タグとのunion。上書きではない）。

使い方:
  source venv/bin/activate
  AWS_PROFILE=default python scripts/suggest_word_tags.py suggest
  AWS_PROFILE=default python scripts/suggest_word_tags.py verify
  AWS_PROFILE=default python scripts/suggest_word_tags.py apply --confirm --limit 20   # まず少数で試す
  AWS_PROFILE=default python scripts/suggest_word_tags.py apply --confirm              # 全件適用
"""
import argparse
import hashlib
import json
import logging
import os
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from decimal import Decimal
from typing import Dict, List, Optional, Tuple

import boto3
from dotenv import load_dotenv

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TAGS_TS_PATH = os.path.abspath(os.path.join(PROJECT_ROOT, "..", "japanese-learn-ui", "src", "app", "data", "tags.ts"))
CACHE_DIR = os.path.join(os.path.dirname(__file__), ".cache")
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
TAG_EMBEDDING_CACHE_PATH = os.path.join(CACHE_DIR, "tag_embeddings.json")
SUGGESTIONS_PATH = os.path.join(OUTPUT_DIR, "tag_suggestions.json")
VERIFIED_PATH = os.path.join(OUTPUT_DIR, "tag_suggestions_verified.json")

# 類似度の閾値（cosine類似度、Titan embed text v1）。
# suggest実行時にサンプルを出力するので、まずそれを見て調整すること。
HIGH_THRESHOLD = 0.60  # これ以上は自動採用候補（それでもverifyでもう一段確認可能）
LOW_THRESHOLD = 0.45  # これ未満は捨てる。45〜60はLLM確認対象（borderline）
MAX_NEW_TAGS_PER_WORD = 5  # 1単語あたりの新規タグ候補数の上限

# 意味embeddingでの類似度判定に向かないタグのID。
# 理由1: 文法機能を表すタグ（品詞・接続関係など）は「単語の意味」ではなく「文法的な役割」を
#         示すものなので、語義embeddingでは判定できない（例: 助動詞, 代名詞, 疑問詞）。
# 理由2: 固有名詞的で語数が少ないタグは埋め込みが退化し、無関係な単語と広く高スコアになる
#         ことを実データで確認した（例: id=73 ベトナムの地名 は無関係な単語1095件とマッチ）。
EXCLUDED_TAG_IDS = {
    1,  # 文末詞 Sentence-final particle
    2,  # あいづち Backchannel response
    7,  # 方向動詞 Directional verb
    9,  # 前置詞 Preposition
    14,  # 助動詞 Auxiliary verb
    16,  # 順接 Sequential conjunction
    19,  # 二重動詞 Compound verb
    23,  # 類別詞 Classifier
    25,  # 代名詞 Pronoun
    33,  # 人称代名詞 Personal Pronoun
    36,  # 疑問詞 Interrogative word
    40,  # 接続詞 Conjunction
    41,  # 逆接 Adversative conjunction
    42,  # 文の接続 Sentence Connection
    73,  # ベトナムの地名 Vietnamese Place Names（退化embedding。実データで無関係な単語1095件とマッチを確認）
}


def load_tags_from_ts(path: str = TAGS_TS_PATH) -> List[Dict]:
    """tags.ts (フロントエンドのマスタ) から id/ja/english を正規表現で抜き出す。"""
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = re.compile(r"\{\s*id:\s*(\d+),\s*ja:\s*'((?:[^'\\]|\\.)*)',\s*english:\s*'((?:[^'\\]|\\.)*)'")
    tags = []
    for match in pattern.finditer(content):
        tag_id, ja, english = match.groups()
        ja = ja.replace("\\'", "'")
        english = english.replace("\\'", "'")
        tags.append({"id": int(tag_id), "ja": ja, "english": english})

    if not tags:
        raise RuntimeError(f"tags.ts からタグを1件も抽出できなかった: {path}")

    logger.info(f"tags.ts から {len(tags)} 件のタグを読み込んだ")
    return tags


def fetch_all_words() -> List[Dict]:
    """DynamoDBから全WORD項目を取得する（embedding, tags, name等）。読み取りのみ。"""
    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(os.getenv("DYNAMODB_TABLE_NAME", "japanese-learn-table"))

    items = []
    last_evaluated_key = None
    while True:
        params = {
            "KeyConditionExpression": "PK = :pk",
            "ExpressionAttributeValues": {":pk": "WORD"},
        }
        if last_evaluated_key:
            params["ExclusiveStartKey"] = last_evaluated_key

        response = table.query(**params)
        items.extend(response.get("Items", []))

        last_evaluated_key = response.get("LastEvaluatedKey")
        if not last_evaluated_key:
            break

    logger.info(f"DynamoDBから {len(items)} 件のWORD項目を取得した")
    return items


def _decimal_list_to_float(values) -> List[float]:
    return [float(v) for v in values]


def get_tag_embeddings(tags: List[Dict], embedding_service) -> Dict[int, List[float]]:
    """タグのembeddingをキャッシュ付きで取得する（Bedrock呼び出し削減のため）。"""
    os.makedirs(CACHE_DIR, exist_ok=True)

    cache: Dict[str, Dict] = {}
    if os.path.exists(TAG_EMBEDDING_CACHE_PATH):
        with open(TAG_EMBEDDING_CACHE_PATH, "r", encoding="utf-8") as f:
            cache = json.load(f)

    result: Dict[int, List[float]] = {}
    updated = False

    for tag in tags:
        text = f"{tag['ja']} {tag['english']}".strip()
        text_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        key = str(tag["id"])

        cached_entry = cache.get(key)
        if cached_entry and cached_entry.get("hash") == text_hash:
            result[tag["id"]] = cached_entry["embedding"]
            continue

        logger.info(f"タグ embedding を生成: [{tag['id']}] {text}")
        embedding = embedding_service.generate_embedding(text)
        result[tag["id"]] = embedding
        cache[key] = {"hash": text_hash, "embedding": embedding, "text": text}
        updated = True

    if updated:
        with open(TAG_EMBEDDING_CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(cache, f, ensure_ascii=False)
        logger.info(f"タグ embedding キャッシュを更新: {TAG_EMBEDDING_CACHE_PATH}")

    return result


def cmd_suggest(args):
    import numpy as np

    from app.api.v1.chat.services.embedding_service import EmbeddingService

    tags = [t for t in load_tags_from_ts() if t["id"] not in EXCLUDED_TAG_IDS]
    tags_by_id = {t["id"]: t for t in tags}
    logger.info(f"意味embeddingでの判定に向かないタグ {len(EXCLUDED_TAG_IDS)} 件を除外し、残り {len(tags)} 件で計算する")

    words = fetch_all_words()
    words_with_embedding = [w for w in words if w.get("embedding") and len(w["embedding"]) == 1536]
    skipped = len(words) - len(words_with_embedding)
    if skipped:
        logger.warning(f"embeddingが無い単語を {skipped} 件スキップした（先に generate_embeddings.py --entity-type word を実行すること）")

    embedding_service = EmbeddingService()
    tag_embeddings = get_tag_embeddings(tags, embedding_service)

    tag_ids = list(tag_embeddings.keys())
    tag_matrix = np.array([tag_embeddings[tid] for tid in tag_ids], dtype=np.float32)
    tag_matrix /= np.linalg.norm(tag_matrix, axis=1, keepdims=True)

    word_matrix = np.array(
        [_decimal_list_to_float(w["embedding"]) for w in words_with_embedding], dtype=np.float32
    )
    word_matrix /= np.linalg.norm(word_matrix, axis=1, keepdims=True)

    # words x tags のコサイン類似度行列
    sims = word_matrix @ tag_matrix.T

    suggestions = []
    all_top_scores = []

    for i, word in enumerate(words_with_embedding):
        existing_tags = set(int(t) for t in word.get("tags", []))
        row = sims[i]

        candidates = []
        for j, tag_id in enumerate(tag_ids):
            if tag_id in existing_tags:
                continue
            score = float(row[j])
            if score >= LOW_THRESHOLD:
                candidates.append((tag_id, score))

        candidates.sort(key=lambda x: x[1], reverse=True)
        candidates = candidates[:MAX_NEW_TAGS_PER_WORD]

        if candidates:
            all_top_scores.append(candidates[0][1])

        if not candidates:
            continue

        confident = [c for c in candidates if c[1] >= HIGH_THRESHOLD]
        borderline = [c for c in candidates if c[1] < HIGH_THRESHOLD]

        suggestions.append(
            {
                "word_id": int(word["SK"]),
                "name": word.get("name", ""),
                "hiragana": word.get("hiragana", ""),
                "english": word.get("english", ""),
                "existing_tags": sorted(existing_tags),
                "confident": [
                    {"tag_id": tid, "ja": tags_by_id[tid]["ja"], "english": tags_by_id[tid]["english"], "score": round(s, 4)}
                    for tid, s in confident
                ],
                "borderline": [
                    {"tag_id": tid, "ja": tags_by_id[tid]["ja"], "english": tags_by_id[tid]["english"], "score": round(s, 4)}
                    for tid, s in borderline
                ],
            }
        )

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(SUGGESTIONS_PATH, "w", encoding="utf-8") as f:
        json.dump(
            {
                "high_threshold": HIGH_THRESHOLD,
                "low_threshold": LOW_THRESHOLD,
                "max_new_tags_per_word": MAX_NEW_TAGS_PER_WORD,
                "words": suggestions,
            },
            f,
            ensure_ascii=False,
            indent=2,
        )

    n_confident = sum(len(s["confident"]) for s in suggestions)
    n_borderline = sum(len(s["borderline"]) for s in suggestions)
    logger.info(f"対象単語: {len(words_with_embedding)} 件")
    logger.info(f"候補ありの単語: {len(suggestions)} 件")
    logger.info(f"confident候補（自動採用ライン以上）: {n_confident} 件")
    logger.info(f"borderline候補（LLM確認対象）: {n_borderline} 件")
    logger.info(f"出力: {SUGGESTIONS_PATH}")

    if all_top_scores:
        arr = np.array(all_top_scores)
        logger.info(
            "類似度スコア分布（各単語のトップ候補）: "
            f"min={arr.min():.3f} p25={np.percentile(arr, 25):.3f} median={np.median(arr):.3f} "
            f"p75={np.percentile(arr, 75):.3f} max={arr.max():.3f}"
        )

    logger.info("=== サンプル（先頭10件）===")
    for s in suggestions[:10]:
        top = (s["confident"] + s["borderline"])[:3]
        top_str = ", ".join(f"{c['ja']}({c['score']})" for c in top)
        logger.info(f"  {s['name']}({s['hiragana']}) [{s['english']}] -> {top_str}")


def _extract_json(text: str):
    text = text.strip()
    text = re.sub(r"^```(?:json)?", "", text).strip()
    text = re.sub(r"```$", "", text).strip()
    return json.loads(text)


def cmd_verify(args):
    from google import genai

    if not os.path.exists(SUGGESTIONS_PATH):
        raise RuntimeError(f"{SUGGESTIONS_PATH} が無い。先に `suggest` を実行すること")

    with open(SUGGESTIONS_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("GEMINI_API_KEY が設定されていない")
    client = genai.Client(api_key=api_key)
    model_name = os.getenv("GEMINI_MODEL_NAME", "gemini-3.1-flash-lite")

    # confident帯にも実データで誤検出が確認された（例: 「二」-> 「間違う」 score=0.6159）ため、
    # confident/borderlineの区別なく全候補をLLMで確認する。embeddingスコアは
    # 「LLMに確認させる価値がある候補を絞り込むための足切り」としてのみ使う。
    words_with_candidates = [w for w in data["words"] if w["confident"] or w["borderline"]]
    logger.info(f"候補を持つ単語: {len(words_with_candidates)} 件をLLM確認する")

    # 既にverify済みの結果があれば再利用する（中断後の再実行で無駄なAPI呼び出しをしない）
    previously_verified: Dict[int, Optional[List[Dict]]] = {}
    if os.path.exists(VERIFIED_PATH):
        with open(VERIFIED_PATH, "r", encoding="utf-8") as f:
            prev_data = json.load(f)
        for w in prev_data.get("words", []):
            if w.get("llm_confirmed") is not None:
                previously_verified[w["word_id"]] = w["llm_confirmed"]
        logger.info(f"再利用可能な確認済み結果: {len(previously_verified)} 件")

    target_words = [w for w in words_with_candidates if w["word_id"] not in previously_verified]
    if args.limit:
        already_counted = len(words_with_candidates) - len(target_words)
        remaining_budget = max(0, args.limit - already_counted)
        target_words = target_words[:remaining_budget]
    target_word_ids = {w["word_id"] for w in target_words}
    logger.info(f"今回LLM呼び出しする単語: {len(target_word_ids)} 件（並列数={args.workers}）")

    def verify_one(w: Dict) -> Tuple[int, List[Dict]]:
        all_candidates = w["confident"] + w["borderline"]
        candidate_lines = "\n".join(f"- id={c['tag_id']}: {c['ja']} ({c['english']})" for c in all_candidates)
        prompt = f"""あなたは日本語学習アプリの単語タグ付け担当です。
以下の単語に対して、候補タグのそれぞれが意味的に当てはまるかを判定してください。

単語: {w['name']}（{w['hiragana']}） / 英語訳: {w['english']}

候補タグ:
{candidate_lines}

判定基準:
- 単語の意味・用途として自然に結びつくタグだけを「はい」とすること
- 単なる字面の類似や、こじつけの関連づけは「いいえ」とすること
- 迷う場合は「いいえ」とすること（false positiveを避ける）

以下のJSON形式のみで回答してください（説明文は不要）:
{{"results": [{{"tag_id": 数値, "applies": true または false}}, ...]}}
"""
        try:
            response = client.models.generate_content(model=model_name, contents=prompt)
            result = _extract_json(response.text)
            applies_ids = {int(r["tag_id"]) for r in result.get("results", []) if r.get("applies")}
        except Exception as e:
            logger.error(f"LLM確認に失敗（単語 {w['name']}）: {e}")
            applies_ids = set()

        confirmed = [c for c in all_candidates if c["tag_id"] in applies_ids]
        return w["word_id"], confirmed

    newly_verified: Dict[int, List[Dict]] = {}
    done = 0

    def save_progress():
        verified_words = []
        for w in data["words"]:
            all_candidates = w["confident"] + w["borderline"]
            if not all_candidates:
                verified_words.append({**w, "llm_confirmed": []})
            elif w["word_id"] in previously_verified:
                verified_words.append({**w, "llm_confirmed": previously_verified[w["word_id"]]})
            elif w["word_id"] in newly_verified:
                verified_words.append({**w, "llm_confirmed": newly_verified[w["word_id"]]})
            else:
                verified_words.append({**w, "llm_confirmed": None})
        with open(VERIFIED_PATH, "w", encoding="utf-8") as f:
            json.dump({**data, "words": verified_words}, f, ensure_ascii=False, indent=2)

    if target_words:
        with ThreadPoolExecutor(max_workers=args.workers) as executor:
            futures = {executor.submit(verify_one, w): w for w in target_words}
            for future in as_completed(futures):
                w = futures[future]
                try:
                    word_id, confirmed = future.result()
                except Exception as e:
                    logger.error(f"LLM確認に失敗（単語 {w['name']}）: {e}")
                    word_id, confirmed = w["word_id"], []
                newly_verified[word_id] = confirmed
                done += 1
                if done % 50 == 0 or done == len(target_words):
                    logger.info(f"進捗: {done}/{len(target_words)}")
                    save_progress()

    save_progress()

    with open(VERIFIED_PATH, "r", encoding="utf-8") as f:
        final_data = json.load(f)
    n_confirmed = sum(len(w.get("llm_confirmed") or []) for w in final_data["words"])
    n_unverified = sum(1 for w in final_data["words"] if w.get("llm_confirmed") is None and (w["confident"] or w["borderline"]))
    logger.info(f"LLM確認で採用: {n_confirmed} 件")
    if n_unverified:
        logger.info(f"未確認のまま残っている単語: {n_unverified} 件（再実行すれば続きから処理される）")
    logger.info(f"出力: {VERIFIED_PATH}")


def cmd_apply(args):
    # embeddingスコアのみのconfident帯にも実データで誤検出が確認されているため、
    # applyはLLM確認済み（llm_confirmed）の候補のみを対象にする。verify未実施では適用しない。
    if not os.path.exists(VERIFIED_PATH):
        raise RuntimeError(f"{VERIFIED_PATH} が無い。先に `verify` を実行してLLM確認を済ませること")

    with open(VERIFIED_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    to_apply: List[Tuple[int, List[int], str]] = []
    skipped_unverified = 0
    for w in data["words"]:
        if w.get("llm_confirmed") is None:
            if w["confident"] or w["borderline"]:
                skipped_unverified += 1
            continue
        new_tag_ids = [c["tag_id"] for c in w["llm_confirmed"]]
        if not new_tag_ids:
            continue
        to_apply.append((w["word_id"], sorted(set(new_tag_ids)), w["name"]))

    if skipped_unverified:
        logger.warning(f"verify未実施（limit指定などで未確認）の単語 {skipped_unverified} 件はスキップした")

    if args.limit:
        to_apply = to_apply[: args.limit]

    logger.info(f"適用対象: {len(to_apply)} 単語")

    if not args.confirm:
        logger.info("dry-run（--confirm を付けていないのでDynamoDBへの書き込みは行わない）")
        for word_id, new_tags, name in to_apply[:20]:
            logger.info(f"  [dry-run] word_id={word_id} ({name}) に追加: {new_tags}")
        return

    dynamodb = boto3.resource("dynamodb")
    table = dynamodb.Table(os.getenv("DYNAMODB_TABLE_NAME", "japanese-learn-table"))

    success = 0
    failed = 0
    for word_id, new_tags, name in to_apply:
        try:
            response = table.get_item(Key={"PK": "WORD", "SK": str(word_id)})
            item = response.get("Item")
            if not item:
                logger.warning(f"word_id={word_id} がDynamoDBに見つからない。スキップ")
                continue

            existing = set(int(t) for t in item.get("tags", []))
            merged = sorted(existing | set(new_tags))

            table.update_item(
                Key={"PK": "WORD", "SK": str(word_id)},
                UpdateExpression="SET #tags = :tags",
                ExpressionAttributeNames={"#tags": "tags"},
                ExpressionAttributeValues={":tags": merged},
            )
            success += 1
        except Exception as e:
            logger.error(f"word_id={word_id} の更新に失敗: {e}")
            failed += 1

    logger.info(f"適用完了。成功: {success}, 失敗: {failed}")


def main():
    env_file = os.path.join(PROJECT_ROOT, ".env")
    if os.path.exists(env_file):
        load_dotenv(env_file)

    parser = argparse.ArgumentParser(description="タグ×単語の意味的な紐付けを増やすスクリプト")
    subparsers = parser.add_subparsers(dest="command", required=True)

    p_suggest = subparsers.add_parser("suggest", help="embedding類似度で候補を抽出（読み取りのみ）")
    p_suggest.set_defaults(func=cmd_suggest)

    p_verify = subparsers.add_parser("verify", help="候補をGeminiで確認（読み取りのみ、Gemini APIを消費）")
    p_verify.add_argument("--limit", type=int, help="確認する単語数の上限（お試し用。既存の確認済み分に追加で処理する件数）")
    p_verify.add_argument("--workers", type=int, default=8, help="Gemini呼び出しの並列数（デフォルト8）")
    p_verify.set_defaults(func=cmd_verify)

    p_apply = subparsers.add_parser("apply", help="DynamoDBのWORD項目にタグを追記する")
    p_apply.add_argument("--confirm", action="store_true", help="実際に書き込む（無ければdry-run）")
    p_apply.add_argument("--limit", type=int, help="適用する単語数の上限（お試し用）")
    p_apply.set_defaults(func=cmd_apply)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
