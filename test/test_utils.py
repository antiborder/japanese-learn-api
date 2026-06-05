from utils import convert_hiragana_to_romaji, convert_romaji_to_hiragana


class TestConvertHiraganaToRomaji:
    def test_basic_vowels(self):
        assert convert_hiragana_to_romaji("あいうえお") == "aiueo"

    def test_basic_consonants(self):
        assert convert_hiragana_to_romaji("かきくけこ") == "kakikukeko"

    def test_compound_kana(self):
        assert convert_hiragana_to_romaji("きゃ") == "kya"
        assert convert_hiragana_to_romaji("しゃしゅしょ") == "shashusho"
        assert convert_hiragana_to_romaji("ちゃちゅちょ") == "chachucho"

    def test_n(self):
        assert convert_hiragana_to_romaji("ん") == "n"

    def test_unknown_character_passthrough(self):
        assert convert_hiragana_to_romaji("犬") == "犬"

    def test_empty_string(self):
        assert convert_hiragana_to_romaji("") == ""

    def test_mixed(self):
        assert convert_hiragana_to_romaji("にほん") == "nihon"


class TestConvertRomajiToHiragana:
    def test_basic_vowels(self):
        assert convert_romaji_to_hiragana("a") == "あ"
        assert convert_romaji_to_hiragana("i") == "い"

    def test_compound(self):
        assert "きゃ" in convert_romaji_to_hiragana("kya")

    def test_empty_string(self):
        assert convert_romaji_to_hiragana("") == ""
