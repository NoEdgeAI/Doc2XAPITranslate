import re
from markdown_it import MarkdownIt
from googletrans import Translator as google

# class Translator:
#     """
#     翻译器类，用于将文本翻译为目标语言。
#     """

#     def __init__(self):
#         # 初始化翻译器
#         pass

#     def translate(self, text, dest):
#         """
#         将文本翻译为目标语言。
#         """
#         # 这里只是示例，实际应用需要调用翻译 API
#         translated = "翻译"
#         return translated


# # 初始化翻译器
# translator = Translator()


class Translator:
    """
    翻译器类，用于将文本翻译为目标语言。
    """

    def __init__(self):
        # 初始化翻译器
        pass

    def translate(self, text, dest):
        """
        将文本翻译为目标语言。
        """
        translator = google()
        gtext = translator.translate(text, dest=dest)
        return gtext.text


translator = Translator()


# 预设特殊字符组
special_groups = [
    ("⚛️{}⚡", "⚛️{}⚡"),  # 使用相同的特殊字符组
]


def translate_text(text):
    """
    使用翻译器将文本翻译为目标语言。
    """
    try:
        translated = translator.translate(text=text, dest="zh-cn")
        return translated
    except Exception as e:
        print(f"翻译错误: {e}")
        return text


def replace_special_groups(text, group):
    """
    替换文本中的公式部分为特殊字符形式。
    """
    pattern, replacement = group
    formula_count = 0

    def replace_func(m):
        nonlocal formula_count
        formula_count += 1
        return replacement.format(formula_count)

    return re.sub(r"\\\((.*?)\\\)", replace_func, text)


def restore_special_groups(text, group):
    """
    将特殊字符形式的公式还原为 LaTeX 公式。
    """
    pattern, replacement = group
    # 构建正则表达式模式，匹配数字
    escaped_pattern = r"⚛️(\d+)⚡"
    return re.sub(escaped_pattern, r"\\(\1\\)", text)


def process_inline(text):
    """
    处理包含行内公式的纯文本，进行翻译。
    """
    original_text = text
    for group in special_groups:
        # 替换公式为特殊字符形式
        text = replace_special_groups(text, group)
        # 翻译文本
        translated = translate_text(text)
        # 还原特殊字符为公式
        translated = restore_special_groups(translated, group)
        # 检查是否成功翻译
        if translated != text:
            return translated
        else:
            text = original_text
    # 如果所有特殊字符组都未能成功翻译，则分开翻译
    parts = re.split(r"(\\\(.*?\\\))", original_text)
    translated_parts = []
    for part in parts:
        if part.startswith("\\(") and part.endswith("\\)"):
            # 保留公式不变
            translated_parts.append(part)
        else:
            # 翻译纯文本部分
            translated_parts.append(translate_text(part))
    return "".join(translated_parts)


def process_markdown(markdown_text):
    """
    解析并翻译 Markdown 文本。
    """
    md = MarkdownIt()
    tokens = md.parse(markdown_text)

    def process_tokens(tokens):
        for token in tokens:
            if token.type == "inline":
                process_inline_token(token)
            elif token.children:
                process_tokens(token.children)

    def process_inline_token(token):
        for child in token.children:
            if child.type == "text":
                content = child.content
                # 检查是否包含行内公式
                inline_formulas = re.findall(r"\\\(.*?\\\)", content)
                if inline_formulas:
                    # 处理包含行内公式的文本
                    translated_content = process_inline(content)
                else:
                    # 纯文本直接翻译
                    translated_content = translate_text(content)
                child.content = translated_content
            elif child.type == "math_inline":
                # 跳过行内公式
                continue
            elif child.children:
                process_tokens(child.children)

    process_tokens(tokens)

    # 渲染翻译后的 tokens
    md_translated = MarkdownIt()
    translated_text = md_translated.renderer.render(tokens, md.options, {})
    return translated_text


if __name__ == "__main__":
    # 示例 Markdown 文本
    with open(
        "Test/Liu-等---2024---Adv-Diffusion-Imperceptible-Adversarial-Face-Identity-Attack-.pdf-2024-12-16-19-31-56.md",
        "r",
        encoding="utf-8",
    ) as f:
        markdown_text = f.read()
    translated_markdown = process_markdown(markdown_text)
    with open("Test/zh.md", "w", encoding="utf-8") as f:
        f.write(translated_markdown)
