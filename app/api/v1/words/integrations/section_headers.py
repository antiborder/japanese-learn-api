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
    },
    'zh-hans': {
        'meaning': '【含义】',
        'examples': '【例子】',
        'synonyms': '【近义词】',
        'antonyms': '【反义词】',
        'usage': '【用法】',
        'notation': '【写法】',
        'sentence1': '【例句1】',
        'sentence2': '【例句2】',
        'etymology': '【词源】',
        'japanese': '日语：',
        'translation': '翻译：',
        'explanation': '说明：'
    },
    'ko': {
        'meaning': '【의미】',
        'examples': '【예문】',
        'synonyms': '【유의어】',
        'antonyms': '【반의어】',
        'usage': '【용법】',
        'notation': '【표기】',
        'sentence1': '【예문 1】',
        'sentence2': '【예문 2】',
        'etymology': '【어원】',
        'japanese': '일본어:',
        'translation': '번역:',
        'explanation': '설명:'
    },
    'id': {
        'meaning': '【Makna】',
        'examples': '【Contoh】',
        'synonyms': '【Sinonim】',
        'antonyms': '【Antonim】',
        'usage': '【Penggunaan】',
        'notation': '【Penulisan】',
        'sentence1': '【Kalimat Contoh 1】',
        'sentence2': '【Kalimat Contoh 2】',
        'etymology': '【Asal-usul】',
        'japanese': 'Bahasa Jepang:',
        'translation': 'Terjemahan:',
        'explanation': 'Penjelasan:'
    },
    'hi': {
        'meaning': '【अर्थ】',
        'examples': '【उदाहरण】',
        'synonyms': '【पर्यायवाची】',
        'antonyms': '【विलोम】',
        'usage': '【प्रयोग】',
        'notation': '【लिपि/लेखन】',
        'sentence1': '【उदाहरण वाक्य 1】',
        'sentence2': '【उदाहरण वाक्य 2】',
        'etymology': '【शब्द-व्युत्पत्ति】',
        'japanese': 'जापानी:',
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





