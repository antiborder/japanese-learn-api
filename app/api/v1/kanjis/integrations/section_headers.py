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
    },
    'zh-hans': {
        'meaning': '【基本含义】',
        'examples': '【用例】',
        'readings': '【读音】',
        'etymology': '【起源与构成】',
        'correspondence': '【与母语的对应】',
        'on_yomi': 'On-yomi (音读):',
        'kun_yomi': 'Kun-yomi (训读):',
        'translation': '翻译:',
        'explanation': '说明:'
    },
    'ko': {
        'meaning': '【기본 의미】',
        'examples': '【사용 예문】',
        'readings': '【읽는 법】',
        'etymology': '【어원과 형성】',
        'correspondence': '【모국어와의 대응】',
        'on_yomi': '온요미(音読み):',
        'kun_yomi': '훈요미(訓読み):',
        'translation': '번역:',
        'explanation': '설명:'
    },
    'id': {
        'meaning': '【Makna Dasar】',
        'examples': '【Contoh Penggunaan】',
        'readings': '【Cara Baca】',
        'etymology': '【Asal-usul dan Pembentukan】',
        'correspondence': '【Kesesuaian dengan Bahasa Ibu】',
        'on_yomi': 'On-yomi (音読み):',
        'kun_yomi': 'Kun-yomi (訓読み):',
        'translation': 'Terjemahan:',
        'explanation': 'Penjelasan:'
    },
    'hi': {
        'meaning': '【मूल अर्थ】',
        'examples': '【उदाहरण वाक्य】',
        'readings': '【उच्चारण】',
        'etymology': '【उत्पत्ति और संरचना】',
        'correspondence': '【आपकी मातृभाषा से अनुरूपता】',
        'on_yomi': 'ऑन-योमी (音読み):',
        'kun_yomi': 'कुन-योमी (訓読み):',
        'translation': 'अनुवाद:',
        'explanation': 'व्याख्या:'
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
