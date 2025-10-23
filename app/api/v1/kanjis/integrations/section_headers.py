# 各言語の見出しマッピング
SECTION_HEADERS = {
    'en': {
        'meaning': '【Basic Meaning】',
        'examples': '【Usage Examples】',
        'readings': '【Readings】',
        'etymology': '【Origin and Formation】',
        'correspondence': '【Correspondence with Your Native Language】',
        'on_yomi': 'On-yomi (音読み):',
        'kun_yomi': 'Kun-yomi (訓読み):',
        'translation': 'Translation:',
        'explanation': 'Explanation:'
    },
    'vi': {
        'meaning': '【Ý nghĩa cơ bản】',
        'examples': '【Ví dụ sử dụng】',
        'readings': '【Cách đọc】',
        'etymology': '【Nguồn gốc và cấu tạo】',
        'correspondence': '【Tương ứng với tiếng mẹ đẻ】',
        'on_yomi': 'On-yomi (音読み):',
        'kun_yomi': 'Kun-yomi (訓読み):',
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
