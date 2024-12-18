from googletrans import Translator


def google_translate(src: str = "en", dest: str = "zh-cn") -> callable:
    """Initialize and return the translate function

    Args:
        src: Source language code, defaults to "en"
        dest: Destination language code, defaults to "zh-cn"

    Returns:
        callable: The translate function that can be used for translation
    """

    def translate(text: str, prev_text: str, next_text: str) -> str:
        try:
            T = Translator()
            return T.translate(text, src=src, dest=dest).text
        except Exception as e:
            print(f"Error: {e}")
            return text

    return translate
