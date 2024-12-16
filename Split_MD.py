import re
from googletrans import Translator as GoogleTranslator


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
        for chunk in chunks:
            try:
                translated = self.translator.translate(
                    chunk, src=self.src, dest=self.dest
                ).text
            except Exception as e:
                # 如果翻译失败，返回原始文本
                translated = chunk
            translated_chunks.append(translated)
        return translated_chunks

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
markdown_text = """
# Example Title

This is an example containing an inline formula: $F\\left( \\cdot \\right)$ and a display formula:

$$
E = mc^2
$$

Here is a [link](https://example.com) and an image:

<img src="https://cdn.noedgeai.com/01938a5f-d42c-718d-ae8a-ed76877e1886_4.jpg?x=448&y=147&w=900&h=660"/>

| Header1 | Header2 |
|---------|---------|
| Cell1   | Cell2   |

<!-- Media -->

<table>
  <tr>
    <td>Method</td>
    <td>ASR (↑)</td>
    <td>FID (↓)</td>
    <td>PSNR (↑)</td>
  </tr>
  <tr>
    <td>Adv-Diffusion</td>
    <td>53.43</td>
    <td>15.34</td>
    <td>22.01</td>
  </tr>
  <tr>
    <td>w/o Adaptive Strength</td>
    <td>71.11</td>
    <td>62.37</td>
    <td>12.62</td>
  </tr>
  <tr>
    <td>w/o Mask</td>
    <td>59.11</td>
    <td>55.23</td>
    <td>13.22</td>
  </tr>
</table>

Table 3: Ablation study experimental results with several metrics.

<div>This is an HTML tag</div>
"""

translated_text = translator.translate_text(markdown_text)
with open("Test/translated.md", "w") as f:
    f.write(translated_text)
