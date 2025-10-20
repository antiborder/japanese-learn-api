def create_sentence_grammar_prompt(sentence_text: str, jlpt_level: str, language_name: str) -> str:
    """
    例文の文法解説生成用のプロンプトを作成
    
    Args:
        sentence_text: 例文テキスト（日本語）
        jlpt_level: JLPT級（例：'N5', 'N4', 'N3', 'N2', 'N1'）
        language_name: 言語名（例：'English', 'Vietnamese'）
    
    Returns:
        プロンプトテキスト
    """
    prompt = f"""You are a Japanese language teacher. Please provide a comprehensive grammar explanation of the Japanese sentence "{sentence_text}" in {language_name}.

This sentence is at {jlpt_level} level.

After receiving your response text, I will replace the full-width brackets 《》 【】 『』 ［］ in your response with HTML tags.
Therefore, please do not omit these brackets.
In particular, enclose headings with 【】, and enclose the text that follows with 『』.
Also, enclose Japanese words or sentences with 《》 because we will highlight them in the web application.
Do not include any extra text.

Make it natural, educational, and easy to understand for learners. Change lines before beginning of new sentences. Use bullet points with ⚫︎ as often as possible for users to read. Do not continue without changing lines.
Attention!!: Do not include any explanations that have not been verified as accurate. Do not return an answer without reliable source of information.

The explanation should focus on grammar points relevant to the {jlpt_level} level, including:
- Sentence structure
- Sentence patterns
- Fixed expressions
- Particles
- Auxiliary verbs
- Conjunctions
- Verb conjugations
- Adjective conjugations
- Adjectival noun conjugations

Please select up to 5 most important grammar points for the {jlpt_level} level and explain them in {language_name}.
Do not include honorifics (敬語) in the grammar points.
After one【】, only one 『』can follow, so include all the contents (bullet points) related to the grammar point in one 『』.
『Explanation of the first grammar point』


Please structure your explanation using the following format in {language_name}.:
【Sentence】
『《{sentence_text}》
meaning: translation in {language_name}』

【】
『Explanation of the first grammar point』

【】
『Explanation of the second grammar point』

【】
『Explanation of the third grammar point』

【】
『Explanation of the fourth grammar point』

【】
『Explanation of the fifth grammar point』

Please write the entire explanation in {language_name}, keeping the section headers as they are. Make it natural, educational, and easy to understand for learners."""

    return prompt
