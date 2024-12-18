import re
from dataclasses import dataclass
from typing import List
import concurrent.futures
from googletrans import Translator as GoogleTranslator
from tqdm import tqdm


@dataclass
class Block:
    position: int
    sub_position: int = 1
    type: str = ""
    content: str = ""


def split_markdown(content: str) -> List[Block]:
    A = []
    pattern = re.compile(
        r"(?P<title>^#{1,6} .+?$)|"
        r"(?P<table><table[\s\S]*?<\/table>)|"
        r"(?P<block_formula>\$\$[\s\S]+?\$\$)|"
        r'(?P<img><img src="[^"]+"\/?>)|'
        r"(?P<link_img>!\[.*?\]\([^\)]+\))|"
        r"(?P<link>\[[^\]]+\]\([^\)]+\))",
        re.MULTILINE,
    )

    pos = 0
    for match in pattern.finditer(content):
        start, end = match.span()
        if start > pos:
            text = content[pos:start].strip()
            if text:
                A.append(Block(position=len(A) + 1, type="text", content=text))
        if match.group("title"):
            A.append(
                Block(position=len(A) + 1, type="title", content=match.group("title"))
            )
        elif match.group("table"):
            A.append(
                Block(position=len(A) + 1, type="table", content=match.group("table"))
            )
        elif match.group("block_formula"):
            A.append(
                Block(
                    position=len(A) + 1,
                    type="block_formula",
                    content=match.group("block_formula"),
                )
            )
        elif match.group("img"):
            A.append(
                Block(position=len(A) + 1, type="image", content=match.group("img"))
            )
        elif match.group("link_img"):
            A.append(
                Block(
                    position=len(A) + 1,
                    type="link_image",
                    content=match.group("link_img"),
                )
            )
        elif match.group("link"):
            A.append(
                Block(position=len(A) + 1, type="link", content=match.group("link"))
            )
        pos = end
    if pos < len(content):
        text = content[pos:].strip()
        if text:
            A.append(Block(position=len(A) + 1, type="text", content=text))
    return A


def split_text_blocks(A: List[Block]) -> List[Block]:
    end_punctuations = re.compile(r"[。？！.!?;；]")
    new_blocks = []
    for block in A:
        if block.type == "text":
            text = block.content
            start = 0
            while start < len(text):
                end = start + 512
                if end >= len(text):
                    end = len(text)
                else:
                    match = end_punctuations.search(text, end)
                    if match:
                        end = match.end()
                    else:
                        end = min(start + 1024, len(text))
                segment = text[start:end].strip()
                if segment:
                    new_blocks.append(
                        Block(
                            position=block.position,
                            sub_position=len(new_blocks) + 1,
                            type="text",
                            content=segment,
                        )
                    )
                start = end
        else:
            new_blocks.append(block)
    return new_blocks


def translate(text: str, prev_text: str, next_text: str) -> str:
    try:
        T = GoogleTranslator()
        return T.translate(text, src="en", dest="zh-cn").text
    except Exception as e:
        print(f"Error: {e}")
        return text


def replace_inline_formula(
    text: str, placeholder_counter: int, placeholders: dict
) -> str:
    inline_formula_pattern = re.compile(r"\$[^$]+\$")

    def replacer(match):
        nonlocal placeholder_counter
        placeholder = f"⚛️{placeholder_counter}⚛️"
        placeholders[placeholder] = match.group()
        placeholder_counter += 1
        return placeholder

    return inline_formula_pattern.sub(replacer, text)


def concurrent_translate(A: List[Block]) -> List[Block]:
    placeholders = {}
    placeholder_counter = 1

    def process_block(block: Block):
        nonlocal placeholder_counter
        if block.type in ["table", "block_formula", "image", "link_image", "link"]:
            return block
        elif block.type == "title":
            content = block.content.lstrip("#").strip()
            translated = translate(content, "", "")
            block.content = translated
            return block
        elif block.type == "text":
            prev_block = None
            next_block = None
            if block.sub_position > 1:
                for b in reversed(A[: A.index(block)]):
                    if (
                        b.position == block.position
                        and b.sub_position == block.sub_position - 1
                    ):
                        prev_block = b.content
                        break
            else:
                for b in reversed(A[: A.index(block)]):
                    if b.position == block.position - 1:
                        prev_block = b.content
                        break
            for b in A[A.index(block) + 1 :]:
                if (
                    b.position == block.position
                    and b.sub_position == block.sub_position + 1
                ):
                    next_block = b.content
                    break
                elif b.position == block.position + 1:
                    next_block = b.content
                    break
            translated_content = replace_inline_formula(
                block.content, placeholder_counter, placeholders
            )
            placeholder_counter += len(placeholders)
            translated = translate(
                translated_content, prev_block or "", next_block or ""
            )
            for placeholder, formula in placeholders.items():
                translated = translated.replace(placeholder, formula)
            if "⚛️" in translated:
                sentences = re.split(r"(?<=[。？！.!?;；])", block.content)
                translated_sentences = [translate(s, "", "") for s in sentences]
                translated = "".join(translated_sentences)
            block.content = translated
            return block
        return block

    total_blocks = len(A)
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        A = list(
            tqdm(
                executor.map(process_block, A),
                total=total_blocks,
                desc="Translating blocks",
                unit="block",
            )
        )
    return A


def combine_blocks(A: List[Block]) -> str:
    combined = []
    for block in A:
        combined.append(block.content)
    return "\n\n".join(combined)


def main(input_markdown: str) -> str:
    blocks = split_markdown(input_markdown)
    blocks = split_text_blocks(blocks)
    blocks = concurrent_translate(blocks)
    output_markdown = combine_blocks(blocks)
    return output_markdown


if __name__ == "__main__":
    with open(
        "Test/Liu-等---2024---Adv-Diffusion-Imperceptible-Adversarial-Face-Identity-Attack-.pdf-2024-12-18-14-34-50.md",
        "r",
        encoding="utf-8",
    ) as f:
        input_md = f.read()
    output_md = main(input_md)
    with open("Test/translated.md", "w", encoding="utf-8") as f:
        f.write(output_md)
