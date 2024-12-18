import httpx
import json


def deeplx_translate(
    base_url="http://127.0.0.1:1188/translate", src: str = "EN", dest: str = "ZH"
) -> callable:
    """Initialize and return the translate function using DeepLX API

    Args:
        base_url: The base URL of the DeepLX API, defaults to "http://127.0.0.1:1188/translate"
        src: Source language code, defaults to "EN"
        dest: Destination language code, defaults to "ZH"

    Returns:
        callable: The translate function that can be used for translation
    """

    def translate(text: str, prev_text: str, next_text: str) -> str:
        try:
            deeplx_api = base_url
            data = {"text": text, "source_lang": src, "target_lang": dest}
            post_data = json.dumps(data)
            response = httpx.post(url=deeplx_api, data=post_data, timeout=10.0)
            if response.status_code != 200:
                raise Exception(f"HTTP request failed: {response.text}")
            result = json.loads(response.text)
            return result["data"]
        except Exception as e:
            print(f"Error: {e}")
            return text

    return translate
