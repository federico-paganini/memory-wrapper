import os
import shutil
import fitz  # pymupdf
from pathlib import Path
from datetime import datetime
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QScrollArea, QLabel, QProgressBar, QMessageBox
)
from PyQt6.QtGui import QPixmap, QImage, QIcon
from PyQt6.QtCore import Qt, pyqtSignal

from .styles import BTN_SAVE, BTN_CANCEL
from ..logger import get_logger

logger = get_logger(__name__)

MESES = {
    1: 'Enero', 2: 'Febrero', 3: 'Marzo',
    4: 'Abril', 5: 'Mayo', 6: 'Junio',
    7: 'Julio', 8: 'Agosto', 9: 'Septiembre',
    10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
}


class PreviewWindow(QMainWindow):
    """Report preview window.

    Opens immediately in a loading state (while the .PRN is still being written
    and the PDF generated), then swaps to the rendered pages via ``load_pdf``.
    """

    closed = pyqtSignal(object)  # emits self so the controller can drop its reference

    def __init__(self, icon_file: Path, output_base: Path):
        super().__init__()
        self._icon_file = icon_file
        self._output_base = output_base
        self._temp_pdf_path: Path | None = None
        self._setup_ui()
        self._show_loading()

    def _setup_ui(self):
        self.setWindowIcon(QIcon(str(self._icon_file)))
        self.setWindowTitle("Vista previa del reporte")
        self.setMinimumSize(900, 700)

        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Scroll area that holds either the loading indicator or the PDF pages.
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._pages_widget = QWidget()
        self._pages_layout = QVBoxLayout(self._pages_widget)
        self._pages_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._pages_layout.setSpacing(12)
        self._scroll.setWidget(self._pages_widget)
        layout.addWidget(self._scroll)

        # Persistent loading widgets, reused across states.
        self._status_label = QLabel()
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._progress = QProgressBar()
        self._progress.setRange(0, 0)  # indeterminate / busy
        self._progress.setFixedWidth(240)
        self._progress.setTextVisible(False)

        # Buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self._btn_save = QPushButton("Guardar PDF")
        self._btn_save.setFixedHeight(36)
        self._btn_save.setMinimumWidth(140)
        self._btn_save.clicked.connect(self._on_save)
        self._btn_save.setStyleSheet(BTN_SAVE)

        self._btn_cancel = QPushButton("Cancelar")
        self._btn_cancel.setFixedHeight(36)
        self._btn_cancel.setMinimumWidth(100)
        self._btn_cancel.clicked.connect(self.close)
        self._btn_cancel.setStyleSheet(BTN_CANCEL)

        btn_layout.addWidget(self._btn_cancel)
        btn_layout.addWidget(self._btn_save)
        layout.addLayout(btn_layout)

    def _clear_pages(self):
        while self._pages_layout.count():
            item = self._pages_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.setParent(None)

    def _show_loading(self):
        self._clear_pages()
        self._status_label.setText("Generando reporte…")
        self._pages_layout.addWidget(self._status_label)
        self._pages_layout.addWidget(
            self._progress, alignment=Qt.AlignmentFlag.AlignHCenter
        )
        self._btn_save.setEnabled(False)

    def load_pdf(self, temp_pdf_path: Path):
        """Swap the loading state for the rendered PDF pages."""
        self._temp_pdf_path = temp_pdf_path
        self._clear_pages()
        self._render_pdf()
        self._btn_save.setEnabled(True)

    def show_error(self, message: str):
        """Replace the loading state with an error message (fail loud)."""
        self._clear_pages()
        self._status_label.setText(f"Error al generar el reporte:\n{message}")
        self._pages_layout.addWidget(self._status_label)
        self._btn_save.setEnabled(False)

    def _render_pdf(self):
        doc = fitz.open(str(self._temp_pdf_path))
        for page in doc:
            mat = fitz.Matrix(2.0, 2.0)  # 2x zoom for crisp rendering
            pix = page.get_pixmap(matrix=mat)
            img = QImage(
                pix.samples, pix.width, pix.height, pix.stride,
                QImage.Format.Format_RGB888
            )
            label = QLabel()
            label.setPixmap(QPixmap.fromImage(img))
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._pages_layout.addWidget(label)
        doc.close()

    def _on_save(self):
        if self._temp_pdf_path is None:
            return

        fecha = datetime.now()
        output_dir = (
            self._output_base /
            fecha.strftime('%Y') /
            MESES[fecha.month]
        )
        output_dir.mkdir(parents=True, exist_ok=True)

        filename = f"Reporte {fecha.strftime('%d-%m-%Y')}.pdf"
        dest = output_dir / filename

        shutil.copy2(str(self._temp_pdf_path), dest)
        logger.info("Report saved to %s", dest)
        QMessageBox.information(self, "Listo", f"Reporte guardado en:\n{dest}")
        os.startfile(str(output_dir))
        self.close()

    def closeEvent(self, event):
        # Always remove the temp on close, saved or not.
        if self._temp_pdf_path and self._temp_pdf_path.exists():
            self._temp_pdf_path.unlink()
        self.closed.emit(self)
        event.accept()
