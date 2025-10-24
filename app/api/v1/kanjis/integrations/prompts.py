def create_kanji_description_prompt(kanji_character: str, language_name: str, headers: dict) -> str:
    """
    漢字のAI解説生成用のプロンプトを作成
    
    Args:
        kanji_character: 漢字の一文字
        language_name: 言語名（例：'English', 'Vietnamese'）
        headers: 見出し辞書
    
    Returns:
        プロンプトテキスト
    """
    prompt = f"""You are a Japanese language teacher. Please provide a comprehensive explanation of the Japanese kanji character "{kanji_character}" in {language_name}.
    After receiving your response text, I will replace the full-width brackets 《》 【】 『』 ［］ in your response with HTML tags.
Therefore, please do not omit these brackets.
In particular, enclose headings with 【】, and enclose the text that follows with 『』.
Also, enclose Japanese words or sentences with 《》 because we will highlight them in the web application. 
In the texts enclosed in 《》, please add full-width brackets［ before and ］ after {kanji_character} itself. (do not delete 《》. 《》can enclose ［］.)
Do not include any extra text.

Make it natural, educational, and easy to understand for learners. Change lines before beginning of new sentences. Use bullet points with ⚫︎ as often as possible for users to read. Do not continue without changing lines.
Attention!!: Do not include any explanations that have not been verified as accurate.

Kanji: {kanji_character}

Please structure your explanation using the following format in {language_name}:

{headers['meaning']}
『Explain the basic core meaning of the kanji character in detail. This should be the core meaning that underlies various uses of the character.』

{headers['readings']}
『List the readings of the kanji character:
・On-yomi (音読み): [Chinese-derived readings]
・Kun-yomi (訓読み): [Japanese native readings]』

{headers['examples']}
『Provide specific examples of how this kanji is used (maximum 3 examples).
example (in a case of english): 
⚫︎《Japanese word or sentence containing the kanji》
Translation: English translation』

{headers['correspondence']}
『Explain the correspondence with the user's native language only if you can find any reliable source of information about the correspondence between 2 languages.
If the user's native language is Vietnamese, explain that kanji and Vietnamese have about 70% correspondence rate, and identify which modern Vietnamese words derived from Sino-Vietnamese (漢越語) that share the same origin as this kanji.
This is not the correspondence of meaning between 2 languages, but the correspondence of the origin of the kanji character between japanese and vietnamese. 
Do not force connections that don't exist. If you cannot find any source of information about the correspondence, omit this section.』

{headers['etymology']}
『Explain the origin and formation of the kanji character. Describe how the character was created and its historical development. Do not include this section if you cannot find any reliable source of information about the origin or formation of the kanji {kanji_character}.』

Please write the entire explanation in {language_name}, keeping the section headers as they are. Make it natural, educational, and easy to understand for learners."""

    return prompt