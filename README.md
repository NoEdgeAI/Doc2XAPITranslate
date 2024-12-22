# Trans-PolyDocs

🚧 目前项目还处于完善阶段，暂不可用 🚧

🚧 Project under development, not ready for use yet 🚧

[English](README_EN.md) | 中文

快速将Makdown文档或PDF文档(由Doc2X进行转换)翻译为Markdown/Word，同时保留原有公式/表格/图片格式。

内置支持 DeepSeek，OpenAI，Ollama，Google翻译(由[py-googletrans](https://github.com/ssut/py-googletrans)提供)，DeepL，DeeLX翻译。

| 主界面                                             | LLM设置                                                       | 多种翻译器                                                             |
| ---------------------------------------------------- | -------------------------------------------------------------- | -------------------------------------------------------------------- |
| 拖入或点击导入Markdown/PDF文件，支持自动切换深色模式 | 针对LLM的细化配置，更高自定义空间 | 支持多种翻译器 |
| <img src="https://github.com/user-attachments/assets/4a56614e-03cd-400f-a7bd-abf1907d0bd1"/>| <img src="https://github.com/user-attachments/assets/748ab2bf-181a-47f1-876f-5219f3a8df56"/>| <img src="https://github.com/user-attachments/assets/c4de4326-f245-4f77-bfe2-587e039c2887"/>     |

## 运行GUI

> [!IMPORTANT]
> 如您希望将翻译后的文档以Word形式输出，请安装`pandoc`后运行程序。
>
> Windows:
> 
>[下载安装包安装](https://pandoc.org/installing.html)或在Powershell中输入`winget install --source winget --exact --id JohnMacFarlane.Pandoc`或
>
> MacOS:终端中运行`brew install pandoc`
>
> Ubuntu/Debian:终端中运行`sudo apt install pandoc`
>
> Arch/Manjaro:`sudo pacman -S pandoc-cli`

### 预编译程序

您可以点击右侧`releases`下载预编译好的程序使用，下载最新版本您对应操作系统的版本，**解压压缩包**后运行使用。

### 从源码运行

## CLI程序

如您想使用CLI程序，请首先复制样例环境变量：

```bash
cp example.env .env
```

随后根据`.env`中的内容

运行`Main.py`进行

## 打包

使用pyinstaller进行打包。使用`pip install pyinstaller`进行安装。

### Linux/MacOS

```bash
pyinstaller -w --onefile --add-data "reference.docx:." --add-data "example.env:." -i icon.png app.py
```

### Windows

```bash
pyinstaller -w --onefile --add-data "reference.docx;." --add-data "example.env;." -i icon.png app.py
```