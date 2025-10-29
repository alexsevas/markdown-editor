# v0.1.1

# conda activate allpy311
# pip install PyQt5 PyQtWebEngine markdown chardet Pygments


# Подавление предупреждений о deprecated sipPyTypeDict
import warnings
import sys

warnings.filterwarnings("ignore", category=DeprecationWarning, message=".*sipPyTypeDict.*")

from PyQt5.QtWidgets import QApplication
from editor import MarkdownEditor


if __name__ == "__main__":
    app = QApplication(sys.argv)
    editor = MarkdownEditor(app)
    editor.show()

    sys.exit(app.exec_())