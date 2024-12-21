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
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(T.translate(text, src=src, dest=dest))
            loop.close()
            return result.text
        except Exception as e:
            print(f"Error: {e}")
            return text

    return translate
