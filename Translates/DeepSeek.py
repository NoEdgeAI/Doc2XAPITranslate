from openai import OpenAI
import json


def deepseek_translate(
    api_key: str, src: str = "English", dest: str = "中文", extra_type="json"
) -> callable:
    """Initialize and return the translate function

    Args:
        api_key: The DeepSeek API authentication key
        src: Source language code, defaults to "English"
        dest: Destination language code, defaults to "中文"
        extra_type: How to extract translated text from LLM response, defaults to "json"
                   "json": Extract from JSON format with key "translated"
                   "markdown": Extract text wrapped in ```
                   Otherwise use raw response text

    Returns:
        callable: The translate function that can be used for translation
    """

    def translate(text: str, prev_text: str, next_text: str) -> str:
        try:
            client = OpenAI(api_key=api_key, base_url="https://api.deepseek.com")
            response = client.chat.completions.create(
                model="deepseek-chat",
                messages=[
                    {
                        "role": "system",
                        "content": f"You are a translator. Translate from {src} to {dest}. "
                        + (
                            "Return in JSON format with key 'translated'"
                            if extra_type == "json"
                            else "Wrap translated text with ```"
                            if extra_type == "markdown"
                            else "Return translated text directly"
                        ),
                    },
                    {"role": "user", "content": text},
                ],
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
