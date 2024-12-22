from Split_MD import process_markdown
import pypandoc
import os
import time


def Process_MD(
    md_file: str, translate: callable, thread: int = 10, output_path: str = "./Output"
):
    print(f"Processing markdown file: {md_file}")
    with open(md_file, "r", encoding="utf-8") as f:
        input_md = f.read()
    output_md = process_markdown(
        input_markdown=input_md, translate=translate, thread=thread
    )
    output_md_path = os.path.join(
        output_path,
        ".".join(os.path.basename(md_file).split(".")[:-1])
        + "_translated_"
        + time.strftime("%Y%m%d_%H%M%S")
        + ".md",
    )
    os.makedirs(output_path, exist_ok=True)
    with open(output_md_path, "w", encoding="utf-8") as f:
        f.write(output_md)

    print(f"Translated markdown saved to {output_path}")
    print("Trying ranslating markdown to docx...")
    try:
        output_docx_path = output_md_path.replace(".md", ".docx")
        reference_docx = os.path.abspath("reference.docx")
        extra_args = [f"--resource-path={output_path}"]
        if os.path.exists(reference_docx):
            extra_args.append(f"--reference-doc={reference_docx}")
        pypandoc.convert_file(
            output_md_path,
            "docx",
            outputfile=output_docx_path,
            extra_args=extra_args,
        )
        print(f"Translated docx saved to {output_docx_path}")
    except Exception as e:
        print(f"Error converting markdown to docx: {e}")
