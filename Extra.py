from pylatexenc.latexnodes import parsers
from pylatexenc.latexwalker import (
    LatexWalker,
    LatexMathNode,
    LatexEnvironmentNode,
    LatexGroupNode,
    LatexMacroNode,
    LatexCharsNode,
)
import re


# 假装这是一个翻译函数
def translate(text, src_lang="en", target_lang="zh"):
    char_count = len(text)
    return "译" * char_count


# 预设的特殊字符组
special_groups = [
    ("⚛️{}⚡", "🔮{}🎯"),
    ("∮{}∯", "∰{}∲"),
    ("⚔️{}⚔️", "🛡️{}🛡️"),
]


class LaTeXTranslator:
    def __init__(self, latex_code):
        self.latex_code = latex_code
        self.ast = self.parse_latex(latex_code)
        self.formula_placeholders = []
        self.current_group = 0  # 当前使用的特殊字符组索引

    def parse_latex(self, latex_string):
        latex_walker = LatexWalker(latex_string)
        nodelist, _ = latex_walker.parse_content(parsers.LatexGeneralNodesParser())
        return nodelist

    def traverse_ast(self, nodes):
        for node in nodes:
            self._traverse_node(node)

    def _traverse_node(self, node):
        if isinstance(node, LatexCharsNode):
            self.translate_text_node(node)
        elif isinstance(node, LatexMathNode):
            self.replace_math_node(node)
        elif isinstance(node, (LatexEnvironmentNode, LatexGroupNode)):
            self.traverse_ast(node.nodelist)
        elif isinstance(node, LatexMacroNode):
            if node.nodeargd and node.nodeargd.argnlist:
                for arg in node.nodeargd.argnlist:
                    if arg:
                        self.traverse_ast([arg])

    def replace_math_node(self, node):
        placeholder = f"<formula{len(self.formula_placeholders)}>"
        self.formula_placeholders.append((placeholder, node.latex_verbatim()))
        node.latex_verbatim = lambda: placeholder

    def translate_text_node(self, node):
        global special_groups
        text = node.chars.replace("\n", " ")
        # 尝试不同的特殊字符组
        for group in special_groups:
            placeholder_pattern = re.compile(r"<formula\d+>")
            # 替换公式为占位符
            placeholder = group[0]
            text_with_placeholder = placeholder_pattern.sub(placeholder, text)
            # 翻译文本
            translated_text = translate(text_with_placeholder)
            # 恢复公式占位符
            translated_text = translated_text.replace(placeholder, group[1])
            # 检查占位符是否被翻译
            if placeholder_pattern.search(translated_text):
                continue  # 尝试下一组特殊字符
            else:
                node.chars = translated_text
                return
        # 如果所有特殊字符组都无效，回退到纯文本翻译
        translated_text = translate(text)
        node.chars = translated_text

    def reconstruct_latex(self, nodes=None):
        if nodes is None:
            nodes = self.ast
        result = []
        for node in nodes:
            if isinstance(node, LatexCharsNode):
                result.append(node.chars)
            elif isinstance(node, LatexMathNode):
                result.append(node.latex_verbatim())
            elif isinstance(node, LatexEnvironmentNode):
                result.append(f"\\begin{{{node.environmentname}}}")
                result.extend(self.reconstruct_latex(node.nodelist))
                result.append(f"\\end{{{node.environmentname}}}")
            elif isinstance(node, LatexGroupNode):
                result.append("{")
                result.extend(self.reconstruct_latex(node.nodelist))
                result.append("}")
            elif isinstance(node, LatexMacroNode):
                result.append(f"\\{node.macroname}")
                if node.nodeargd and node.nodeargd.argnlist:
                    for arg in node.nodeargd.argnlist:
                        result.append("{")
                        result.extend(self.reconstruct_latex([arg]))
                        result.append("}")
        return "".join(result)

    def get_translated_latex(self):
        self.traverse_ast(self.ast)
        return self.reconstruct_latex()


if __name__ == "__main__":
    with open("Test/111.tex", "r", encoding="utf-8") as f:
        latex_code = f.read()
    translator = LaTeXTranslator(latex_code)
    translated_latex = translator.get_translated_latex()
    with open("Test/output.tex", "w", encoding="utf-8") as f:
        f.write(translated_latex)
