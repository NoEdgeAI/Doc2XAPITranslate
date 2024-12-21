import httpx
import json


def deepl_translate(api_key: str, dest: str = "ZH") -> callable:
    """Initialize and return the translate function using DeepL API

    Args:
        api_key: The DeepL API authentication key
        dest: Destination language code, defaults to "ZH"

    Returns:
        callable: The translate function that can be used for translation
    """

    def translate(text: str, prev_text: str, next_text: str) -> str:
        try:
            deepl_api = "https://api.deepl.com/v2/translate"
            headers = {
                "Authorization": f"DeepL-Auth-Key {api_key}",
                "Content-Type": "application/json",
            }
            data = {"text": [text], "target_lang": dest}
            post_data = json.dumps(data)
            response = httpx.post(
                url=deepl_api, headers=headers, data=post_data, timeout=10.0
            )
            if response.status_code != 200:
                raise Exception(f"HTTP request failed: {response.text}")
            result = json.loads(response.text)
            return result["translations"][0]["text"]
        except Exception as e:
            print(f"Error: {e}")
            return text

    return translate
