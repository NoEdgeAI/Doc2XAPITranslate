import sys
import os
import shutil
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QSpinBox,
    QPushButton,
    QFileDialog,
    QTextEdit,
    QFrame,
    QProgressBar,
    QDialog,
    QPlainTextEdit,
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtCore import QFile, QTextStream
import breeze_pyside6
import builtins
from Main import get_translator, Process_MD
from tqdm import tqdm
import Split_MD
import asyncio
from pdfdeal.Doc2X.ConvertV2 import upload_pdf, uid_status
from PySide6.QtWidgets import QMessageBox
from pdfdeal.file_tools import md_replace_imgs
from file_tool import fix_image_size
import traceback
import signal

# 常量
CONFIG_DIR = os.path.expanduser("~/.config/Doc2X")
CONFIG_FILE = os.path.join(CONFIG_DIR, ".env")


# 设置环境变量
def set_translator_env(translator_type, config):
    if translator_type == "deepl":
        os.environ["deepl_apikey"] = config.get("deepl_apikey", "")
        os.environ["deepl_dest"] = config.get("deepl_dest", "")
    elif translator_type == "google":
        os.environ["google_src"] = config.get("google_src", "")
        os.environ["google_dest"] = config.get("google_dest", "")
    elif translator_type == "deeplx":
        os.environ["deeplx_url"] = config.get("deeplx_url", "")
        os.environ["deeplx_src"] = config.get("deeplx_src", "")
        os.environ["deeplx_dest"] = config.get("deeplx_dest", "")
    elif translator_type == "deepseek":
        os.environ["deepseek_api"] = config.get("deepseek_api", "")
        # LLM专属设置
        os.environ["temperature"] = config.get("temperature", "0.8")
        os.environ["system_prompt"] = config.get("system_prompt", "")
        os.environ["input"] = config.get("input", "")
        os.environ["extra_type"] = config.get("extra_type", "markdown")
        os.environ["llm_src"] = config.get("llm_src", "English")
        os.environ["llm_dest"] = config.get("llm_dest", "中文")
    elif translator_type == "openai":
        os.environ["openai_apikey"] = config.get("openai_apikey", "")
        os.environ["openai_baseurl"] = config.get("openai_baseurl", "")
        os.environ["openai_model"] = config.get("openai_model", "")
        # LLM专属设置
        os.environ["temperature"] = config.get("temperature", "0.8")
        os.environ["system_prompt"] = config.get("system_prompt", "")
        os.environ["input"] = config.get("input", "")
        os.environ["extra_type"] = config.get("extra_type", "markdown")
        os.environ["llm_src"] = config.get("llm_src", "English")
        os.environ["llm_dest"] = config.get("llm_dest", "中文")
    elif translator_type == "ollama":
        os.environ["ollama_baseurl"] = config.get("ollama_baseurl", "")
        os.environ["ollama_model"] = config.get("ollama_model", "")
        # LLM专属设置
        os.environ["temperature"] = config.get("temperature", "0.8")
        os.environ["system_prompt"] = config.get("system_prompt", "")
        os.environ["input"] = config.get("input", "")
        os.environ["extra_type"] = config.get("extra_type", "markdown")
        os.environ["llm_src"] = config.get("llm_src", "English")
        os.environ["llm_dest"] = config.get("llm_dest", "中文")


class LLMSettingsDialog(QDialog):
    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.config = config
        self.setWindowTitle("LLM 设置")
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)

        # 温度
        temp_layout = QHBoxLayout()
        temp_layout.addWidget(QLabel("温度:"))
        self.temp_input = QLineEdit()
        self.temp_input.setText(self.config.get("temperature", "0.8"))
        temp_layout.addWidget(self.temp_input)
        layout.addLayout(temp_layout)

        # 系统提示
        layout.addWidget(QLabel("系统提示:"))
        self.system_input = QPlainTextEdit()
        self.system_input.setPlainText(self.config.get("system_prompt", ""))
        self.system_input.setPlaceholderText("留空则使用默认值(通用翻译提示词)。")
        layout.addWidget(self.system_input)

        # 输入提示
        layout.addWidget(QLabel("输入提示:"))
        self.input_prompt = QPlainTextEdit()
        self.input_prompt.setPlaceholderText(
            "可使用 {{prev_text}}, {{text}}, {{next_text}}, {{dest}} 作为变量，其中 {{text}} 为必选。留空则使用默认值(通用翻译提示词)。"
        )
        self.input_prompt.setPlainText(self.config.get("input", ""))
        layout.addWidget(self.input_prompt)

        # 变量说明和复制按钮
        variable_layout = QVBoxLayout()
        variable_layout.addWidget(QLabel("变量说明:"))

        prev_text_btn = QPushButton("复制 {{prev_text}} - 要翻译文本的前文")
        prev_text_btn.clicked.connect(lambda: self.copy_to_clipboard("{{prev_text}}"))
        variable_layout.addWidget(prev_text_btn)

        text_btn = QPushButton("复制 {{text}} - 要翻译的文本")
        text_btn.clicked.connect(lambda: self.copy_to_clipboard("{{text}}"))
        variable_layout.addWidget(text_btn)

        next_text_btn = QPushButton("复制 {{next_text}} - 要翻译文本的后文")
        next_text_btn.clicked.connect(lambda: self.copy_to_clipboard("{{next_text}}"))
        variable_layout.addWidget(next_text_btn)

        dest_btn = QPushButton("复制 {{dest}} - 翻译目标语言")
        dest_btn.clicked.connect(lambda: self.copy_to_clipboard("{{dest}}"))
        variable_layout.addWidget(dest_btn)

        layout.addLayout(variable_layout)

        # 额外类型
        extra_layout = QHBoxLayout()
        extra_layout.addWidget(QLabel("翻译文本提取方式:"))
        self.extra_combo = QComboBox()
        self.extra_combo.addItems(["json", "markdown", "direct"])
        self.extra_combo.setCurrentText(self.config.get("extra_type", "markdown"))
        extra_layout.addWidget(self.extra_combo)
        layout.addLayout(extra_layout)

        # 源语言
        src_layout = QHBoxLayout()
        src_layout.addWidget(QLabel("源语言:"))
        self.src_input = QLineEdit()
        self.src_input.setText(self.config.get("llm_src", "English"))
        src_layout.addWidget(self.src_input)
        layout.addLayout(src_layout)

        # 目标语言
        dest_layout = QHBoxLayout()
        dest_layout.addWidget(QLabel("目标语言:"))
        self.dest_input = QLineEdit()
        self.dest_input.setText(self.config.get("llm_dest", "中文"))
        dest_layout.addWidget(self.dest_input)
        layout.addLayout(dest_layout)

        # 按钮
        button_layout = QHBoxLayout()
        save_btn = QPushButton("保存")
        save_btn.clicked.connect(self.accept)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)
        layout.addLayout(button_layout)

    def copy_to_clipboard(self, text):
        clipboard = QApplication.clipboard()
        clipboard.setText(text)

    def get_settings(self):
        return {
            "temperature": self.temp_input.text(),
            "system_prompt": self.system_input.toPlainText(),
            "input": self.input_prompt.toPlainText(),
            "extra_type": self.extra_combo.currentText(),
            "llm_src": self.src_input.text(),
            "llm_dest": self.dest_input.text(),
        }


class TranslateThread(QThread):
    output = Signal(str)
    finished = Signal()
    error = Signal(str)
    progress = Signal(int, int)  # 当前，总计

    def __init__(self, file_path, config, translator_type):
        super().__init__()
        self.file_path = file_path
        self.config = config
        self.translator_type = translator_type
        self.is_running = True

    def run(self):
        try:
            # 设置环境变量
            set_translator_env(self.translator_type, self.config)

            # 创建自定义打印函数以发出输出
            def custom_print(text):
                if not self.is_running:
                    return
                self.output.emit(str(text))

            # 覆盖打印函数
            original_print = builtins.print
            builtins.print = custom_print

            # 覆盖 tqdm 以更新进度
            def custom_tqdm(*args, **kwargs):
                total = kwargs.get("total", 0)
                kwargs["disable"] = True
                tqdm_instance = tqdm(*args, **kwargs)

                # 使用非递归更新方法避免递归
                def update_wrapper(n=1):
                    if not self.is_running:
                        return
                    result = tqdm_instance._original_update(n)
                    self.progress.emit(tqdm_instance.n, total)
                    return result

                tqdm_instance._original_update = tqdm_instance.update
                tqdm_instance.update = update_wrapper
                return tqdm_instance

            Split_MD.tqdm = custom_tqdm

            print("正在运行翻译...")

            # 根据配置获取翻译器
            translator = get_translator(self.translator_type)
            if self.file_path.endswith(".pdf"):

                async def process_pdf(file_path, apikey):
                    if not self.is_running:
                        return
                    print("正在上传 PDF...")
                    uid = await upload_pdf(apikey=apikey, pdffile=file_path)
                    print("正在处理 PDF...")
                    while True and self.is_running:
                        process, status, texts, locations = await uid_status(
                            apikey=apikey, uid=uid
                        )
                        self.progress.emit(process, 100)
                        if process == 100:
                            return texts
                        await asyncio.sleep(3)

                apikey = self.config.get("DOC2X_APIKEY", "sk-xxx")
                md_texts = asyncio.run(process_pdf(self.file_path, apikey))
                if not self.is_running:
                    return
                md_text = "\n".join(md_texts)
                # 预处理 PDF 转换的 markdown 文本

                output_md_path = os.path.join(
                    "Output",
                    ".".join(os.path.basename(self.file_path).split(".")[:-1]) + ".md",
                )
                os.makedirs("Output", exist_ok=True)
                with open(output_md_path, "w", encoding="utf-8") as f:
                    f.write(md_text)
                self.file_path = output_md_path
            print("开始下载图片（如果有）...")
            if not self.is_running:
                return
            md_replace_imgs(mdfile=self.file_path, replace="local", threads=10)
            print("开始修复图片大小以解决 pandoc 中图片尺寸问题:")
            if not self.is_running:
                return
            img_dir = os.path.dirname(self.file_path)
            img_folder = (
                ".".join(os.path.basename(self.file_path).split(".")[:-1]) + "_img"
            )
            fix_image_size(os.path.join(img_dir, img_folder))
            print("翻译中...")
            if not self.is_running:
                return
            self.progress.emit(0, 100)
            try:
                Process_MD(
                    md_file=self.file_path,
                    translate=translator,
                    thread=int(self.config.get("THREADS", 10)),
                )
            except Exception as e:
                print(f"翻译失败: {e}")
                print(traceback.format_exc())

            # 恢复原始打印
            builtins.print = original_print
            if self.is_running:
                self.finished.emit()

        except Exception as e:
            if self.is_running:
                self.error.emit(str(e))

    def stop(self):
        self.is_running = False


class FileDropWidget(QFrame):
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setFrameStyle(QFrame.Box | QFrame.Sunken)
        self.setMinimumHeight(100)

        layout = QVBoxLayout()
        self.label = QLabel("拖拽文件到这里或点击选择文件(.md/.pdf)")
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)

        self.file_path = None
        self.setLayout(layout)

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        if files:
            self.file_path = files[0]
            self.label.setText(os.path.basename(self.file_path))

    def mousePressEvent(self, event):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "选择文件", "", "Markdown/PDF 文件 (*.md *.pdf)"
        )
        if file_path:
            self.file_path = file_path
            self.label.setText(os.path.basename(self.file_path))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("翻译")
        self.setMinimumWidth(600)

        # 加载或创建配置
        self.config = {}
        self.load_config()

        # 主窗口和布局
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # 文件拖放区域
        self.file_drop = FileDropWidget()
        layout.addWidget(self.file_drop)

        # Doc2X API 输入
        api_layout = QHBoxLayout()
        api_layout.addWidget(QLabel("Doc2X API 密钥:"))
        self.api_input = QLineEdit()
        self.api_input.setText(self.config.get("DOC2X_APIKEY", ""))
        api_layout.addWidget(self.api_input)
        layout.addLayout(api_layout)

        # 翻译器选择
        translator_layout = QHBoxLayout()
        translator_layout.addWidget(QLabel("翻译器:"))
        self.translator_combo = QComboBox()
        self.translator_combo.addItems(
            ["deepseek", "deepl", "google", "deeplx", "openai", "ollama"]
        )
        self.translator_combo.setCurrentText("deepseek")
        self.translator_combo.currentTextChanged.connect(self.on_translator_changed)
        translator_layout.addWidget(self.translator_combo)

        # 添加 LLM 设置按钮
        self.llm_settings_btn = QPushButton("LLM 设置")
        self.llm_settings_btn.clicked.connect(self.show_llm_settings)
        translator_layout.addWidget(self.llm_settings_btn)

        layout.addLayout(translator_layout)

        # 翻译器设置
        self.translator_settings = QWidget()
        self.translator_settings_layout = QVBoxLayout(self.translator_settings)
        layout.addWidget(self.translator_settings)

        # 线程设置
        thread_layout = QHBoxLayout()
        thread_layout.addWidget(QLabel("线程数:"))
        self.thread_spin = QSpinBox()
        self.thread_spin.setRange(1, 100)
        self.thread_spin.setValue(int(self.config.get("THREADS", 10)))
        thread_layout.addWidget(self.thread_spin)
        layout.addLayout(thread_layout)

        # 测试按钮
        self.test_btn = QPushButton("测试翻译器")
        self.test_btn.clicked.connect(self.test_translator)
        layout.addWidget(self.test_btn)

        # 开始按钮
        self.start_btn = QPushButton("开始翻译")
        self.start_btn.clicked.connect(self.start_translation)
        layout.addWidget(self.start_btn)

        # 进度条
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        # 输出文本
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.setMinimumHeight(200)  # 设置最小高度为 200
        self.output_text.hide()
        layout.addWidget(self.output_text)

        # 打开文件夹按钮
        self.open_folder_btn = QPushButton("打开输出文件夹")
        self.open_folder_btn.clicked.connect(
            lambda: os.system(
                "xdg-open Output" if os.name == "posix" else "start Output"
            )
        )
        self.open_folder_btn.hide()
        layout.addWidget(self.open_folder_btn)

        # 显示初始翻译器设置
        self.show_translator_settings(self.translator_combo.currentText())

    def show_llm_settings(self):
        dialog = LLMSettingsDialog(self.config, self)
        if dialog.exec():
            settings = dialog.get_settings()
            self.config.update(settings)
            self.save_config()

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        key, value = line.split("=", 1)
                        self.config[key.strip()] = value.strip().strip('"')
        else:
            os.makedirs(CONFIG_DIR, exist_ok=True)
            if os.path.exists("./example.env"):
                shutil.copy("./example.env", CONFIG_FILE)
                self.load_config()

    def save_config(self):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            for key, value in self.config.items():
                f.write(f'{key}="{value}"\n')

    def on_translator_changed(self, translator):
        # 当翻译器更改时更新 TRANSLATE_USE
        self.config["TRANSLATE_USE"] = translator
        self.save_config()
        self.show_translator_settings(translator)

        # 根据翻译器类型显示/隐藏 LLM 设置按钮
        self.llm_settings_btn.setVisible(translator in ["deepseek", "openai", "ollama"])

    def show_translator_settings(self, translator):
        # 清除之前的设置
        while self.translator_settings_layout.count():
            item = self.translator_settings_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                while item.layout().count():
                    child = item.layout().takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()

        # 根据翻译器添加设置
        if translator == "deepl":
            self.add_setting("deepl_apikey", "DeepL API 密钥:")
            self.add_setting("deepl_dest", "目标语言:")
        elif translator == "google":
            self.add_setting("google_src", "源语言:")
            self.add_setting("google_dest", "目标语言:")
        elif translator == "deeplx":
            self.add_setting("deeplx_url", "DeepLX URL:")
            self.add_setting("deeplx_src", "源语言:")
            self.add_setting("deeplx_dest", "目标语言:")
        elif translator == "deepseek":
            self.add_setting("deepseek_api", "DeepSeek API:")
        elif translator == "openai":
            self.add_setting("openai_apikey", "OpenAI API 密钥:")
            self.add_setting("openai_baseurl", "基础 URL:")
            self.add_setting("openai_model", "模型:")
        elif translator == "ollama":
            self.add_setting("ollama_baseurl", "Ollama URL:")
            self.add_setting("ollama_model", "模型:")

    def add_setting(self, key, label):
        layout = QHBoxLayout()
        layout.addWidget(QLabel(label))
        input_field = QLineEdit()
        input_field.setText(self.config.get(key, ""))
        input_field.textChanged.connect(lambda text, k=key: self.update_config(k, text))
        layout.addWidget(input_field)
        self.translator_settings_layout.addLayout(layout)

    def update_config(self, key, value):
        self.config[key] = value
        self.save_config()

    def test_translator(self):
        # 保存当前配置
        self.config["DOC2X_APIKEY"] = self.api_input.text()
        self.config["TRANSLATE_USE"] = self.translator_combo.currentText()
        self.config["THREADS"] = str(self.thread_spin.value())
        self.save_config()

        class TranslatorTestThread(QThread):
            success = Signal(str)
            failure = Signal(str)

            def __init__(self, translator_type):
                super().__init__()
                self.translator_type = translator_type

            def run(self):
                try:
                    translator = get_translator(self.translator_type)
                    test = translator("Hello, how are you?", "", "")
                    if test == "Hello, how are you?":
                        self.failure.emit("翻译器测试失败，请检查设置。")
                    else:
                        self.success.emit(f"翻译器测试成功: {test}")
                except Exception as e:
                    self.failure.emit(str(e))

        translator_type = self.translator_combo.currentText()
        set_translator_env(translator_type, self.config)
        self.output_text.append("提示: 正在测试翻译器，这可能需要一些时间..")
        self.output_text.show()

        self.test_thread = TranslatorTestThread(translator_type)
        self.test_thread.success.connect(
            lambda message: QMessageBox.information(self, "成功", message)
        )
        self.test_thread.failure.connect(
            lambda error: QMessageBox.critical(self, "错误", error)
        )
        self.test_thread.finished.connect(self.test_thread.deleteLater)
        self.test_thread.start()

    def start_translation(self):
        if not self.file_drop.file_path:
            self.output_text.setText("请先选择文件")
            self.output_text.show()
            return

        # 保存当前配置
        self.config["DOC2X_APIKEY"] = self.api_input.text()
        self.config["TRANSLATE_USE"] = self.translator_combo.currentText()
        self.config["THREADS"] = str(self.thread_spin.value())
        self.save_config()

        # 翻译期间禁用按钮和输入框
        self.set_buttons_and_inputs_enabled(False)

        # 显示输出区域和进度条
        self.output_text.clear()
        self.output_text.show()
        self.progress_bar.show()
        self.progress_bar.setValue(0)

        # 创建并启动翻译线程
        self.translate_thread = TranslateThread(
            self.file_drop.file_path, self.config, self.translator_combo.currentText()
        )
        self.translate_thread.output.connect(lambda x: self.output_text.append(x))
        self.translate_thread.finished.connect(self.on_translation_finished)
        self.translate_thread.error.connect(
            lambda x: self.output_text.append(f"错误: {x}")
        )
        self.translate_thread.progress.connect(self.update_progress)
        self.translate_thread.start()

    def update_progress(self, current, total):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)

    def on_translation_finished(self):
        self.open_folder_btn.show()
        self.progress_bar.hide()
        # 翻译后重新启用按钮和输入框
        self.set_buttons_and_inputs_enabled(True)

    def set_buttons_and_inputs_enabled(self, enabled):
        self.test_btn.setEnabled(enabled)
        self.start_btn.setEnabled(enabled)
        self.api_input.setEnabled(enabled)
        self.translator_combo.setEnabled(enabled)
        self.thread_spin.setEnabled(enabled)
        self.file_drop.setEnabled(enabled)
        self.llm_settings_btn.setEnabled(enabled)

    def closeEvent(self, event):
        # 强制终止所有进程
        os.kill(os.getpid(), signal.SIGTERM)
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # 根据系统主题设置样式表
    palette = app.palette()
    if palette.window().color().lightness() > 128:
        # 浅色主题
        file = QFile(":/light/stylesheet.qss")
    else:
        # 深色主题
        file = QFile(":/dark/stylesheet.qss")

    file.open(QFile.ReadOnly | QFile.Text)
    stream = QTextStream(file)
    app.setStyleSheet(stream.readAll())

    window = MainWindow()
    window.show()
    sys.exit(app.exec())
