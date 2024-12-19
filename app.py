import sys
import os
import shutil
from pathlib import Path
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
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QDragEnterEvent, QDropEvent
from PySide6.QtCore import QFile, QTextStream
import breeze_pyside6

# Constants
CONFIG_DIR = os.path.expanduser("~/.config/Doc2X")
CONFIG_FILE = os.path.join(CONFIG_DIR, ".env")


class TranslateThread(QThread):
    output = Signal(str)
    finished = Signal()
    error = Signal(str)
    progress = Signal(int, int)  # current, total

    def __init__(self, file_path, config, translator_type):
        super().__init__()
        self.file_path = file_path
        self.config = config
        self.translator_type = translator_type

    def run(self):
        try:
            # Create custom print function to emit output
            def custom_print(text):
                self.output.emit(str(text))

            # Override print function
            import builtins

            original_print = builtins.print
            builtins.print = custom_print

            # Run translation
            from Main import get_translator, Process_MD
            from tqdm import tqdm

            # Override tqdm for progress updates
            def custom_tqdm(*args, **kwargs):
                total = kwargs.get("total", 0)
                tqdm_instance = tqdm(*args, **kwargs)

                # Avoid recursion by using a non-recursive update method
                def update_wrapper(n=1):
                    result = tqdm_instance._original_update(n)
                    self.progress.emit(tqdm_instance.n, total)
                    return result

                tqdm_instance._original_update = tqdm_instance.update
                tqdm_instance.update = update_wrapper
                return tqdm_instance

            import Split_MD

            Split_MD.tqdm = custom_tqdm

            print("Running translation...")

            # Get translator based on config
            translator = get_translator(self.translator_type)
            if self.file_path.endswith(".pdf"):
                from pdfdeal import Doc2X

                client = Doc2X(debug=True)
                md_text, _, flag = client.pdf2file(
                    pdf_file=self.file_path,
                    output_format="text",
                )
                if flag:
                    raise Exception("PDF conversion failed")

                output_md_path = os.path.join(
                    "Output", os.path.basename(self.file_path).split(".")[0] + ".md"
                )
                os.makedirs("Output", exist_ok=True)
                with open(output_md_path, "w") as f:
                    f.write(md_text[0])
                self.file_path = output_md_path

            Process_MD(
                md_file=self.file_path,
                translate=translator,
                thread=int(self.config.get("THREADS", 10)),
            )

            # Restore original print
            builtins.print = original_print
            self.finished.emit()

        except Exception as e:
            self.error.emit(str(e))


class FileDropWidget(QFrame):
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setFrameStyle(QFrame.Box | QFrame.Sunken)
        self.setMinimumHeight(100)

        layout = QVBoxLayout()
        self.label = QLabel("拖拽文件到这里或点击选择文件")
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
            self, "选择文件", "", "Markdown/PDF Files (*.md *.pdf)"
        )
        if file_path:
            self.file_path = file_path
            self.label.setText(os.path.basename(self.file_path))


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Doc2X Translator")
        self.setMinimumWidth(600)

        # Load or create config
        self.config = {}
        self.load_config()

        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)

        # File drop area
        self.file_drop = FileDropWidget()
        layout.addWidget(self.file_drop)

        # Doc2X API input
        api_layout = QHBoxLayout()
        api_layout.addWidget(QLabel("Doc2X API Key:"))
        self.api_input = QLineEdit()
        self.api_input.setText(self.config.get("DOC2X_APIKEY", ""))
        api_layout.addWidget(self.api_input)
        layout.addLayout(api_layout)

        # Translator selection
        translator_layout = QHBoxLayout()
        translator_layout.addWidget(QLabel("翻译器:"))
        self.translator_combo = QComboBox()
        self.translator_combo.addItems(
            ["deepseek", "deepl", "google", "deeplx", "openai", "ollama"]
        )
        self.translator_combo.setCurrentText("deepseek")
        self.translator_combo.currentTextChanged.connect(self.on_translator_changed)
        translator_layout.addWidget(self.translator_combo)
        layout.addLayout(translator_layout)

        # Translator settings
        self.translator_settings = QWidget()
        self.translator_settings_layout = QVBoxLayout(self.translator_settings)
        layout.addWidget(self.translator_settings)

        # Thread settings
        thread_layout = QHBoxLayout()
        thread_layout.addWidget(QLabel("线程数:"))
        self.thread_spin = QSpinBox()
        self.thread_spin.setRange(1, 100)
        self.thread_spin.setValue(int(self.config.get("THREADS", 10)))
        thread_layout.addWidget(self.thread_spin)
        layout.addLayout(thread_layout)

        # Test button
        self.test_btn = QPushButton("保存并测试")
        self.test_btn.clicked.connect(self.test_translator)
        layout.addWidget(self.test_btn)

        # Start button
        self.start_btn = QPushButton("开始翻译")
        self.start_btn.clicked.connect(self.start_translation)
        layout.addWidget(self.start_btn)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        # Output text
        self.output_text = QTextEdit()
        self.output_text.setReadOnly(True)
        self.output_text.hide()
        layout.addWidget(self.output_text)

        # Open folder button
        self.open_folder_btn = QPushButton("打开输出文件夹")
        self.open_folder_btn.clicked.connect(
            lambda: os.system(
                "xdg-open Output" if os.name == "posix" else "start Output"
            )
        )
        self.open_folder_btn.hide()
        layout.addWidget(self.open_folder_btn)

        # Show initial translator settings
        self.show_translator_settings(self.translator_combo.currentText())

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        key, value = line.split("=", 1)
                        self.config[key.strip()] = value.strip().strip('"')
        else:
            os.makedirs(CONFIG_DIR, exist_ok=True)
            if os.path.exists("example.env"):
                shutil.copy("example.env", CONFIG_FILE)
                self.load_config()

    def save_config(self):
        with open(CONFIG_FILE, "w") as f:
            for key, value in self.config.items():
                f.write(f'{key}="{value}"\n')

    def on_translator_changed(self, translator):
        # Update TRANSLATE_USE when translator changes
        self.config["TRANSLATE_USE"] = translator
        self.save_config()
        self.show_translator_settings(translator)

    def show_translator_settings(self, translator):
        # Clear previous settings
        while self.translator_settings_layout.count():
            item = self.translator_settings_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                while item.layout().count():
                    child = item.layout().takeAt(0)
                    if child.widget():
                        child.widget().deleteLater()

        # Add settings based on translator
        if translator == "deepl":
            self.add_setting("deepl_apikey", "DeepL API Key:")
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
            self.add_setting("openai_apikey", "OpenAI API Key:")
            self.add_setting("openai_baseurl", "Base URL:")
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
        # Save current config
        self.config["DOC2X_APIKEY"] = self.api_input.text()
        self.config["TRANSLATE_USE"] = self.translator_combo.currentText()
        self.config["THREADS"] = str(self.thread_spin.value())
        self.save_config()

        # Get translator
        from Main import get_translator

        # Show testing dialog
        from PySide6.QtWidgets import QMessageBox

        testing_dialog = QMessageBox()
        testing_dialog.setWindowTitle("测试翻译器")
        testing_dialog.setText("正在测试翻译器...")
        testing_dialog.setStandardButtons(QMessageBox.NoButton)
        testing_dialog.show()

        try:
            translator = get_translator(self.translator_combo.currentText())
            # Test translation
            test = translator("Hello, how are you?", "", "")
            if test == "Hello, how are you?":
                testing_dialog.done(0)
                QMessageBox.critical(self, "错误", "翻译器测试失败，请检查设置")
                return

            testing_dialog.done(0)
            QMessageBox.information(self, "成功", f"翻译器测试成功: {test}")

        except Exception as e:
            testing_dialog.done(0)
            QMessageBox.critical(self, "错误", f"翻译器测试失败: {str(e)}")

    def start_translation(self):
        if not self.file_drop.file_path:
            self.output_text.setText("请先选择文件")
            self.output_text.show()
            return

        # Save current config
        self.config["DOC2X_APIKEY"] = self.api_input.text()
        self.config["TRANSLATE_USE"] = self.translator_combo.currentText()
        self.config["THREADS"] = str(self.thread_spin.value())
        self.save_config()

        # Show output area and progress bar
        self.output_text.clear()
        self.output_text.show()
        self.progress_bar.show()
        self.progress_bar.setValue(0)

        # Create and start translation thread
        self.translate_thread = TranslateThread(
            self.file_drop.file_path, self.config, self.translator_combo.currentText()
        )
        self.translate_thread.output.connect(lambda x: self.output_text.append(x))
        self.translate_thread.finished.connect(self.on_translation_finished)
        self.translate_thread.error.connect(
            lambda x: self.output_text.append(f"Error: {x}")
        )
        self.translate_thread.progress.connect(self.update_progress)
        self.translate_thread.start()

    def update_progress(self, current, total):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)

    def on_translation_finished(self):
        self.open_folder_btn.show()
        self.progress_bar.hide()


if __name__ == "__main__":
    app = QApplication(sys.argv)

    # Set stylesheet based on system theme
    palette = app.palette()
    if palette.window().color().lightness() > 128:
        # Light theme
        file = QFile(":/light/stylesheet.qss")
    else:
        # Dark theme
        file = QFile(":/dark/stylesheet.qss")

    file.open(QFile.ReadOnly | QFile.Text)
    stream = QTextStream(file)
    app.setStyleSheet(stream.readAll())

    window = MainWindow()
    window.show()
    sys.exit(app.exec())
