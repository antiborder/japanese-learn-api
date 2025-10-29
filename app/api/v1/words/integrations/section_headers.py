# 各言語の見出しマッピング
SECTION_HEADERS = {
    'en': {
        'meaning': '【Meaning】',
        'examples': '【Examples】',
        'synonyms': '【Synonyms】',
        'antonyms': '【Antonyms】',
        'usage': '【Usage】',
        'notation': '【Notation】',
        'sentence1': '【Example Sentence 1】',
        'sentence2': '【Example Sentence 2】',
        'etymology': '【Etymology】',
        'japanese': 'Japanese:',
        'translation': 'Translation:',
        'explanation': 'Explanation:'
    },
    'vi': {
        'meaning': '【Ý nghĩa】',
        'examples': '【Ví dụ cụ thể】',
        'synonyms': '【Từ đồng nghĩa】',
        'antonyms': '【Từ trái nghĩa】',
        'usage': '【Cách sử dụng】',
        'notation': '【Cách viết】',
        'sentence1': '【Ví dụ câu 1】',
        'sentence2': '【Ví dụ câu 2】',
        'etymology': '【Nguồn gốc】',
        'japanese': 'Tiếng Nhật:',
        'translation': 'Bản dịch:',
        'explanation': 'Giải thích:'
    }
}


def get_section_headers(lang_code: str) -> dict:
    """
    言語コードから見出し辞書を取得
    
    Args:
        lang_code: 言語コード（例：'en', 'vi'）
    
    Returns:
        見出し辞書（デフォルトは英語）
    """
    return SECTION_HEADERS.get(lang_code.lower(), SECTION_HEADERS['en'])





