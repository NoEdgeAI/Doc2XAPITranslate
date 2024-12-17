import re
from googletrans import Translator as GoogleTranslator
import concurrent.futures
from tqdm import tqdm


class Translator:
    """
    翻译器类，用于将Markdown文本翻译为目标语言，同时保留特定的Markdown格式。
    """

    def __init__(self, src="auto", dest="zh-cn"):
        self.translator = GoogleTranslator()
        self.src = src
        self.dest = dest
        self.placeholder_counter = 1
        self.placeholder_mapping = {}

    def _create_placeholder(self):
        placeholder = f"⚛️{self.placeholder_counter}⚡"
        self.placeholder_counter += 1
        return placeholder

    def _preserve_pattern(self, text, pattern, placeholder_pattern):
        placeholders = []

        def replacer(match):
            placeholder = self._create_placeholder()
            placeholders.append((placeholder, match.group(0)))
            return placeholder

        text = re.sub(pattern, replacer, text)
        self.placeholder_mapping.update(placeholders)
        return text

    def preserve_display_formulas(self, text):
        pattern = re.compile(r"\$\$(.*?)\$\$", re.DOTALL)
        return self._preserve_pattern(text, pattern, r"⚛️{}\d+⚡")

    def preserve_inline_formulas(self, text):
        pattern = re.compile(r"\$(.*?)\$", re.DOTALL)
        return self._preserve_pattern(text, pattern, r"⚛️{}\d+⚡")

    def preserve_links(self, text):
        pattern = re.compile(r"\[.*?\]\((.*?)\)")
        return self._preserve_pattern(text, pattern, r"⚛️{}\d+⚡")

    def preserve_images(self, text):
        pattern = re.compile(r"!\[.*?\]\((.*?)\)")
        return self._preserve_pattern(text, pattern, r"⚛️{}\d+⚡")

    def preserve_html_tags(self, text):
        pattern = re.compile(r"<.*?>")
        return self._preserve_pattern(text, pattern, r"⚛️{}\d+⚡")

    def preserve_tables(self, text):
        pattern = re.compile(r"\|.*?\|.*?\|.*?\n(\|.*?\|.*?\|.*?\n)+", re.MULTILINE)
        return self._preserve_pattern(text, pattern, r"⚛️{}\d+⚡")

    def split_text_into_chunks(self, text, max_chunk_size=512):
        chunks = []
        current_chunk = ""
        sentences = re.split(r"(?<=[.!?])\s+", text)
        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= max_chunk_size:
                current_chunk += sentence
            else:
                chunks.append(current_chunk)
                current_chunk = sentence
        if current_chunk:
            chunks.append(current_chunk)
        return chunks

    def translate_chunks(self, chunks):
        translated_chunks = []
        #! Wait to change
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [
                executor.submit(self._translate_single_chunk, chunk) for chunk in chunks
            ]

            for future in tqdm(
                concurrent.futures.as_completed(futures),
                total=len(chunks),
                desc="翻译进度",
            ):
                try:
                    translated = future.result()
                    translated_chunks.append(translated)
                except Exception as e:
                    print(f"Failed to translate chunk: {e}")
                    # 如果翻译失败,将对应的原始文本添加到结果中
                    chunk_index = futures.index(future)
                    translated_chunks.append(chunks[chunk_index])

        # 按原始顺序排序结果
        sorted_chunks = [None] * len(chunks)
        for i, future in enumerate(futures):
            sorted_chunks[i] = translated_chunks[futures.index(future)]

        return sorted_chunks

    def _translate_single_chunk(self, chunk):
        try:
            return self.translator.translate(chunk, src=self.src, dest=self.dest).text
        except Exception as e:
            raise e

    def restore_placeholders(self, text):
        for placeholder, original in self.placeholder_mapping.items():
            text = text.replace(placeholder, original)
        return text

    def translate_text(self, text):
        """
        翻译文本，同时处理Markdown格式。
        """
        # 保留不翻译的元素
        text = self.preserve_display_formulas(text)
        text = self.preserve_inline_formulas(text)
        text = self.preserve_links(text)
        text = self.preserve_images(text)
        text = self.preserve_html_tags(text)
        text = self.preserve_tables(text)

        # 拆分需要翻译的文本成块
        chunks = self.split_text_into_chunks(text)

        # 翻译每个块
        translated_chunks = self.translate_chunks(chunks)

        # 组合翻译后的块
        translated_text = "".join(translated_chunks)

        # 恢复不翻译的元素
        translated_text = self.restore_placeholders(translated_text)

        return translated_text


translator = Translator(src="en", dest="zh-cn")
with open(
    "Test/Liu-等---2024---Adv-Diffusion-Imperceptible-Adversarial-Face-Identity-Attack-.pdf-2024-12-16-19-31-56.md",
    "r",
) as f:
    markdown_text = f.read()
translated_text = translator.translate_text(markdown_text)
with open("Test/translated.md", "w") as f:
    f.write(translated_text)
