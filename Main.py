from dotenv import load_dotenv
import os
import sys
from Translates.OpenAI import openai_translate
from Translates.Ollama import ollama_translate
from Translates.DeepSeek import deepseek_translate
from Translates.DeepLX import deeplx_translate
from Translates.DeepL import deepl_translate
from Translates.Google import google_translate
from MD_Translate import Process_MD

load_dotenv()

# Get translator settings from environment variables
translate_use = os.getenv("TRANSLATE_USE")
threads = int(os.getenv("THREADS", 10))

# Get translator-specific settings
openai_apikey = os.getenv("openai_apikey")
openai_baseurl = os.getenv("openai_baseurl", "https://api.openai.com/v1")
openai_model = os.getenv("openai_model", "gpt-4o-mini")

ollama_baseurl = os.getenv("ollama_baseurl", "http://localhost:11434/v1")
ollama_model = os.getenv("ollama_model", "qwen2.5")

deepseek_api = os.getenv("deepseek_api")

deeplx_url = os.getenv("deeplx_url", "http://127.0.0.1:1188/translate")
deeplx_src = os.getenv("deeplx_src", "EN")
deeplx_dest = os.getenv("deeplx_dest", "ZH")

deepl_apikey = os.getenv("deepl_apikey")
deepl_dest = os.getenv("deepl_dest", "ZH")

# LLM common settings
temperature = float(os.getenv("temperature", 0.8))
system_prompt = os.getenv("system_prompt", "")
input_prompt = os.getenv("input", "")
extra_type = os.getenv("extra_type", "markdown")
llm_src = os.getenv("llm_src", "English")
llm_dest = os.getenv("llm_dest", "中文")


def get_translator():
    """Get translator based on environment variable or user selection"""
    if translate_use:
        return create_translator(translate_use)

    print("Please select a translator:")
    print("1. OpenAI")
    print("2. Ollama")
    print("3. DeepSeek")
    print("4. DeepLX")
    print("5. DeepL")
    print("6. Google")

    choice = input("Enter your choice (1-6): ")

    translators = {
        "1": "openai",
        "2": "ollama",
        "3": "deepseek",
        "4": "deeplx",
        "5": "deepl",
        "6": "google",
    }

    if choice not in translators:
        print("Invalid choice, using deepseek as default")
        return create_translator("deepseek")

    return create_translator(translators[choice])


def create_translator(name):
    """Create translator instance based on name"""
    if name == "openai":
        if not openai_apikey:
            print("Error: OpenAI API key not set")
            sys.exit(1)
        return openai_translate(
            api_key=openai_apikey,
            base_url=openai_baseurl,
            src=llm_src,
            dest=llm_dest,
            model=openai_model,
            tempterature=temperature,
            system_prompt=system_prompt if system_prompt else None,
            input_prompt=input_prompt if input_prompt else None,
            extra_type=extra_type,
        )
    elif name == "ollama":
        return ollama_translate(
            base_url=ollama_baseurl,
            src=llm_src,
            dest=llm_dest,
            model=ollama_model,
            tempterature=temperature,
            system_prompt=system_prompt if system_prompt else None,
            input_prompt=input_prompt if input_prompt else None,
            extra_type=extra_type,
        )
    elif name == "deepseek":
        if not deepseek_api:
            print("Error: DeepSeek API key not set")
            sys.exit(1)
        return deepseek_translate(
            api_key=deepseek_api,
            src=llm_src,
            dest=llm_dest,
            tempterature=temperature,
            system_prompt=system_prompt if system_prompt else None,
            input_prompt=input_prompt if input_prompt else None,
            extra_type=extra_type,
        )
    elif name == "deeplx":
        return deeplx_translate(base_url=deeplx_url, src=deeplx_src, dest=deeplx_dest)
    elif name == "deepl":
        if not deepl_apikey:
            print("Error: DeepL API key not set")
            sys.exit(1)
        return deepl_translate(api_key=deepl_apikey, dest=deepl_dest)
    elif name == "google":
        return google_translate(
            src=os.getenv("google_src", "en"), dest=os.getenv("google_dest", "zh-cn")
        )
    else:
        print(f"Unknown translator: {name}")
        sys.exit(1)


def main():
    # Get translator
    translator = get_translator()

    print("Testing translator...")
    test = translator("Hello, how are you?", "", "")
    if test == "Hello, how are you?":
        print("Translator test failed, please check your settings")
        sys.exit(1)
    print(f"Translator test successful: {test}")

    # Get file path from user
    file_path = input("Please enter the path to your markdown file: ")

    if not os.path.exists(file_path):
        print(f"Error: File {file_path} does not exist")
        sys.exit(1)

    if not file_path.endswith(".md"):
        print("Error: File must be a markdown file (.md)")
        sys.exit(1)

    # Process the file
    Process_MD(md_file=file_path, translate=translator, thread=threads)


if __name__ == "__main__":
    main()
