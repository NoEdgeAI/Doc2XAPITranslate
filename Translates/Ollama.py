from openai import OpenAI
import json


def ollama_translate(
    api_key: str = "ollama",
    base_url: str = "http://localhost:11434/v1",
    src: str = "English",
    dest: str = "中文",
    model="qwen2.5",
    tempterature=0.8,
    system_prompt: str = None,
    input_prompt: str = None,
    extra_type="markdown",
) -> callable:
    """Initialize and return the translate function

    Args:
        api_key: The openai API authentication key
        src: Source language code, defaults to "English"
        dest: Destination language code, defaults to "中文"
        extra_type: How to extract translated text from LLM response, defaults to "json"
                   "json": Extract from JSON format with key "translated"
                   "markdown": Extract text wrapped in ```
                   Otherwise use raw response text

    Returns:
        callable: The translate function that can be used for translation
    """
    if system_prompt is None:
        system_prompt = f"You are a specialized language model trained in translating Markdown documents while preserving their formatting. Your task is to translate a given Markdown text from {src} to {dest}."
    if input_prompt is None:
        input_prompt = """
Here are the key elements for this task:
1. Previous text (for context):
<previous_text>
{{prev_text}}
</previous_text>
2. The language to translate into:
<destination_language>
{{dest}}
</destination_language>
3. The Markdown text to translate:
<markdown_text>
{{text}}
</markdown_text>
Instructions:
1. Read through the Markdown text carefully.
2. Identify all Markdown formatting elements (e.g., headers, bold, italic, links, lists).
3. Translate only the text content, leaving all Markdown syntax unchanged.
4. Ensure that the meaning and tone of the original text are preserved in the translation.
5. Pay attention to any context provided by the previous text, if available.
Before providing your final translation, wrap your analysis in <translation_analysis> tags:
- List all Markdown elements present in the text, counting them (e.g., 1. Header, 2. Bold text, 3. Italic text, etc.).
- Identify any culturally specific terms or idioms that might need special attention in translation.
- Note any areas where the sentence structure might need to be significantly altered in the target language.
- Consider how the previous text (if provided) might influence the translation.
- Plan how to maintain the original text's structure and meaning in the target language.
It's OK for this section to be quite long.
After your analysis, provide the translated Markdown text. Remember:
- Do NOT modify any existing Markdown commands.
- Ensure that your translation accurately reflects the content and style of the original text.
Format your output and only give as follows:
```
[Your translated Markdown text here, preserving all original Markdown formatting]
```
Please proceed with your analysis and translation.
"""

    if "{{text}}" not in input_prompt:
        raise ValueError("input_prompt must contain {{text}} placeholder")

    def translate(text: str, prev_text: str, next_text: str) -> str:
        try:
            client = OpenAI(api_key=api_key, base_url=base_url)
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": input_prompt.replace("{{prev_text}}", prev_text)
                        .replace("{{dest}}", dest)
                        .replace("{{text}}", text)
                        .replace("{{next_text}}", next_text),
                    },
                ],
                temperature=tempterature,
                stream=False,
            )
            result = response.choices[0].message.content

            if extra_type == "json":
                try:
                    return json.loads(result)["translated"]
                except Exception as e:
                    print(f"Having trouble extracting JSON: {e}")
                    return result
            elif extra_type == "markdown":
                try:
                    return result.split("```")[1]
                except Exception as e:
                    print(f"Having trouble extracting markdown: {e}")
                    return result
            return result
        except Exception as e:
            print(f"Error: {e}")
            return text

    return translate
