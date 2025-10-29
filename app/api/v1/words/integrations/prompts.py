def create_description_prompt(word_name: str, word_hiragana: str, language_name: str, headers: dict) -> str:
    """
    AI解説生成用のプロンプトを作成
    
    Args:
        word_name: 単語名（日本語）
        word_hiragana: 単語の読み（ひらがな）
        language_name: 言語名（例：'English', 'Vietnamese'）
        headers: 見出し辞書
    
    Returns:
        プロンプトテキスト
    """
    prompt = f"""You are a Japanese language teacher. Please provide a comprehensive explanation of the Japanese word "{word_name}" in {language_name}.
    After receiving your response text, I will replace the full-width brackets 《》 【】 『』 ［］ in your response with HTML tags.
Therefore, please do not omit these brackets.
In particular, enclose headings with 【】, and enclose the text that follows with 『』.
Also, enclose Japanese words or sentences with 《》 because we will highlight them in the web application. 
In the texts enclosed in 《》, please add full-width brackets［ before and ］ after the words which is identical to {word_name} itself, conjugation of {word_name}, or nearly identical to {word_name}. (do not delete 《》. 《》can enclose ［］.)
Do not include any extra text.

Make it natural, educational, and easy to understand for learners. Change lines before beginning of new sentences. Use bullet points with ⚫︎ as often as possible for users to read. Do not continue without changeng lines.
Attention!!: Do not include any explanations that have not been verified as accurate.

Word: {word_name}
Reading (hiragana): {word_hiragana}

Please structure your explanation using the following format in {language_name}:

{headers['meaning']}
『Explain the meaning of the word in detail.』

{headers['examples']}
『Provide specific examples of how this word is used (2-3 examples).
example (in a case of english): 
⚫︎《Japanese sentence》
Translation: English translation』

{headers['usage']}
『Explain when and how to use this word in conversation.』

{headers['notation']}
『Explain how this word is typically written (hiragana, katakana, kanji).
Are there other ways to write this word?
Are there variations in the okurigana (suffix hiragana)?』

{headers['synonyms']}
『List similar words or synonyms (if any).』

{headers['antonyms']}
『List antonyms or opposite words (if any).』

{headers['sentence1']}
『《[Japanese example sentence]》
・{headers['translation']} [Translation in {language_name}]
・{headers['explanation']} [Brief explanation]』
{headers['sentence2']} (if any)
『《[Japanese example sentence]》
・{headers['translation']} [Translation in {language_name}]
・{headers['explanation']} [Brief explanation]』
{headers['etymology']}
『Explain the etymology or origin of the word (if known). Do not include wrong explanation』

Please write the entire explanation in {language_name}, keeping the section headers as they are. Make it natural, educational, and easy to understand for learners."""

    return prompt
