#!/usr/bin/env python3
"""
배경 제거 유틸리티 v3.0
OpenCV GrabCut 방식 - 모델 다운로드 없음, DLL 문제 없음

필요 패키지: pip install PyQt5 Pillow opencv-python numpy
"""

import sys
import os
import io
import numpy as np

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QListWidget, QListWidgetItem,
    QFileDialog, QProgressBar, QMessageBox, QFrame, QSlider,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QPixmap, QImage

from PIL import Image


# ─── GrabCut 배경 제거 ────────────────────────────────────────────────────────
def remove_background(pil_img: Image.Image, margin_pct: float = 0.05) -> Image.Image:
    """
    OpenCV GrabCut으로 배경 제거.
    margin_pct: 가장자리에서 얼마나 안쪽을 피사체 영역으로 볼지 (0.0~0.3)
    """
    import cv2

    img_rgb = np.array(pil_img.convert('RGB'))
    img_bgr = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2BGR)
    h, w    = img_bgr.shape[:2]

    # 가장자리 여백 → 피사체 사각형
    mx = max(5, int(w * margin_pct))
    my = max(5, int(h * margin_pct))
    rect = (mx, my, w - mx * 2, h - my * 2)

    mask      = np.zeros((h, w), np.uint8)
    bgd_model = np.zeros((1, 65), np.float64)
    fgd_model = np.zeros((1, 65), np.float64)

    cv2.grabCut(img_bgr, mask, rect, bgd_model, fgd_model, 8, cv2.GC_INIT_WITH_RECT)

    # 0(배경확실), 2(배경추정) → 투명 / 1,3 → 불투명
    alpha = np.where((mask == 0) | (mask == 2), 0, 255).astype(np.uint8)

    # 마스크 정리 (모폴로지 - 노이즈 제거)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    alpha  = cv2.morphologyEx(alpha, cv2.MORPH_CLOSE, kernel, iterations=2)
    alpha  = cv2.GaussianBlur(alpha, (5, 5), 0)

    result = pil_img.convert('RGBA')
    result.putalpha(Image.fromarray(alpha))
    return result


# ─── 백그라운드 스레드 ────────────────────────────────────────────────────────
class RemoveThread(QThread):
    sig_progress = pyqtSignal(int, str)
    sig_preview  = pyqtSignal(bytes)
    sig_done     = pyqtSignal(str, int)
    sig_error    = pyqtSignal(str)

    def __init__(self, paths: list, out_dir: str, margin: float):
        super().__init__()
        self.paths   = paths
        self.out_dir = out_dir
        self.margin  = margin

    def run(self):
        try:
            import cv2
        except ImportError as e:
            self.sig_error.emit(f'opencv-python 패키지 오류:\n{e}\n\n실행_배경제거.bat 을 다시 실행하세요.')
            return

        total = len(self.paths)
        first = True

        for i, src_path in enumerate(self.paths):
            fname = os.path.splitext(os.path.basename(src_path))[0] + '.png'
            self.sig_progress.emit(int(i / total * 100), fname)

            try:
                img    = Image.open(src_path).convert('RGBA')
                result = remove_background(img, margin_pct=self.margin)

                if first:
                    buf = io.BytesIO()
                    result.save(buf, 'PNG')
                    self.sig_preview.emit(buf.getvalue())
                    first = False

                result.save(os.path.join(self.out_dir, fname), 'PNG')

            except Exception as e:
                self.sig_error.emit(f'처리 오류 ({fname}):\n{e}')
                return

        self.sig_progress.emit(100, '완료')
        self.sig_done.emit(self.out_dir, total)


# ─── 미리보기 패널 ────────────────────────────────────────────────────────────
class PreviewPane(QFrame):
    def __init__(self, label_text: str):
        super().__init__()
        self.setStyleSheet('QFrame { background: #1a1a1a; border-radius: 6px; }')
        vl = QVBoxLayout(self)
        vl.setContentsMargins(6, 6, 6, 6)
        vl.setSpacing(4)

        title = QLabel(label_text)
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet('color: #888; font-size: 11px;')
        vl.addWidget(title)

        self.img_label = QLabel('—')
        self.img_label.setAlignment(Qt.AlignCenter)
        self.img_label.setMinimumSize(340, 280)
        self.img_label.setStyleSheet('color: #555; font-size: 13px;')
        vl.addWidget(self.img_label, 1)

    def set_from_path(self, path: str):
        self._show(QPixmap(path))

    def set_from_bytes(self, data: bytes):
        self._show(QPixmap.fromImage(QImage.fromData(data)))

    def _show(self, pix: QPixmap):
        self.img_label.setPixmap(
            pix.scaled(self.img_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )


# ─── 메인 윈도우 ──────────────────────────────────────────────────────────────
class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self._thread  = None
        self._out_dir = None

        self.setWindowTitle('배경 제거 유틸리티  v3.0')
        self.setMinimumSize(960, 600)
        self.setStyleSheet(
            "QMainWindow, QWidget { font-family: 'Malgun Gothic', Arial, sans-serif; }"
        )
        self._build_ui()

    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        hl = QHBoxLayout(root)
        hl.setContentsMargins(10, 10, 10, 10)
        hl.setSpacing(10)
        hl.addWidget(self._build_left(),  0)
        hl.addWidget(self._build_right(), 1)

    def _build_left(self):
        w = QWidget()
        w.setFixedWidth(250)
        vl = QVBoxLayout(w)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.setSpacing(6)

        lbl = QLabel('처리할 이미지 목록')
        lbl.setStyleSheet('font-weight: bold; font-size: 12px;')
        vl.addWidget(lbl)

        self.lst = QListWidget()
        self.lst.setStyleSheet(
            'font-size: 11px; border: 1px solid #ccc; border-radius: 4px;'
        )
        self.lst.currentRowChanged.connect(self._on_select)
        vl.addWidget(self.lst, 1)

        row = QHBoxLayout()
        self.btn_add = self._btn('+ 이미지 추가', '#2980b9')
        self.btn_del = self._btn('- 제거',        '#7f8c8d')
        row.addWidget(self.btn_add)
        row.addWidget(self.btn_del)
        vl.addLayout(row)

        # 여백 조절 슬라이더
        vl.addWidget(QLabel('피사체 여백 조절 (값이 클수록 더 많이 자름):'))
        self.sld_margin = QSlider(Qt.Horizontal)
        self.sld_margin.setRange(1, 25)
        self.sld_margin.setValue(5)
        self.lbl_margin = QLabel('여백: 5%')
        self.sld_margin.valueChanged.connect(
            lambda v: self.lbl_margin.setText(f'여백: {v}%')
        )
        vl.addWidget(self.lbl_margin)
        vl.addWidget(self.sld_margin)

        self.lbl_dir = QLabel('저장 폴더: 미선택')
        self.lbl_dir.setStyleSheet(
            'font-size: 10px; color: #666; border: 1px solid #ddd;'
            'border-radius: 3px; padding: 3px;'
        )
        self.lbl_dir.setWordWrap(True)
        vl.addWidget(self.lbl_dir)

        self.btn_dir = self._btn('저장 폴더 선택', '#8e44ad')
        vl.addWidget(self.btn_dir)

        self.btn_run = self._btn('배경 제거 시작', '#e74c3c')
        self.btn_run.setFixedHeight(46)
        self.btn_run.setEnabled(False)
        vl.addWidget(self.btn_run)

        self.btn_add.clicked.connect(self._add_images)
        self.btn_del.clicked.connect(self._del_image)
        self.btn_dir.clicked.connect(self._select_dir)
        self.btn_run.clicked.connect(self._run)
        return w

    def _build_right(self):
        w = QWidget()
        vl = QVBoxLayout(w)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.setSpacing(8)

        row = QHBoxLayout()
        self.pane_orig   = PreviewPane('원본')
        self.pane_result = PreviewPane('배경 제거 결과')
        row.addWidget(self.pane_orig)
        row.addWidget(self.pane_result)
        vl.addLayout(row, 1)

        self.lbl_status = QLabel('이미지를 추가하고 저장 폴더를 선택한 후 [배경 제거 시작]을 눌러주세요.')
        self.lbl_status.setAlignment(Qt.AlignCenter)
        self.lbl_status.setStyleSheet('color: #666; font-size: 11px;')
        vl.addWidget(self.lbl_status)

        self.prog = QProgressBar()
        self.prog.setVisible(False)
        self.prog.setFixedHeight(18)
        self.prog.setStyleSheet("""
            QProgressBar { border:1px solid #ccc; border-radius:4px; text-align:center; font-size:11px; }
            QProgressBar::chunk { background:#e74c3c; border-radius:3px; }
        """)
        vl.addWidget(self.prog)
        return w

    def _btn(self, text, color):
        b = QPushButton(text)
        b.setFixedHeight(34)
        b.setStyleSheet(f"""
            QPushButton {{
                background:{color}; color:white;
                border:none; border-radius:5px;
                font-size:12px; font-weight:bold;
            }}
            QPushButton:hover    {{ background:{color}bb; }}
            QPushButton:disabled {{ background:#bdc3c7; }}
        """)
        return b

    def _add_images(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, '이미지 선택', '',
            'Images (*.jpg *.jpeg *.png *.webp *.bmp)',
        )
        for p in paths:
            it = QListWidgetItem(os.path.basename(p))
            it.setData(Qt.UserRole, p)
            self.lst.addItem(it)
        self._refresh_btn()

    def _del_image(self):
        for it in self.lst.selectedItems():
            self.lst.takeItem(self.lst.row(it))
        self._refresh_btn()

    def _select_dir(self):
        d = QFileDialog.getExistingDirectory(self, '저장 폴더 선택')
        if d:
            self._out_dir = d
            short = d if len(d) < 35 else '...' + d[-32:]
            self.lbl_dir.setText(f'저장 폴더: {short}')
        self._refresh_btn()

    def _refresh_btn(self):
        self.btn_run.setEnabled(self.lst.count() > 0 and self._out_dir is not None)

    def _on_select(self, row):
        if row < 0:
            return
        self.pane_orig.set_from_path(self.lst.item(row).data(Qt.UserRole))
        self.pane_result.img_label.setText('—')

    def _run(self):
        paths  = [self.lst.item(i).data(Qt.UserRole) for i in range(self.lst.count())]
        margin = self.sld_margin.value() / 100.0

        self.prog.setMaximum(0)
        self.prog.setVisible(True)
        self.btn_run.setEnabled(False)
        self.btn_add.setEnabled(False)
        self.lbl_status.setText('처리 중...')

        self._thread = RemoveThread(paths, self._out_dir, margin)
        self._thread.sig_progress.connect(self._on_progress)
        self._thread.sig_preview.connect(self._on_preview)
        self._thread.sig_done.connect(self._on_done)
        self._thread.sig_error.connect(self._on_error)
        self._thread.start()

    def _on_progress(self, pct: int, fname: str):
        self.prog.setMaximum(100)
        self.prog.setValue(pct)
        self.lbl_status.setText(f'처리 중: {fname}  ({pct}%)')

    def _on_preview(self, data: bytes):
        self.pane_result.set_from_bytes(data)

    def _on_done(self, out_dir: str, count: int):
        self.prog.setVisible(False)
        self.btn_run.setEnabled(True)
        self.btn_add.setEnabled(True)
        self.lbl_status.setText(f'완료: {count}장 저장  →  {out_dir}')
        QMessageBox.information(
            self, '완료',
            f'{count}장이 저장되었습니다.\n\n저장 위치:\n{out_dir}',
        )

    def _on_error(self, msg: str):
        self.prog.setVisible(False)
        self.btn_run.setEnabled(True)
        self.btn_add.setEnabled(True)
        QMessageBox.critical(self, '오류', msg)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName('배경 제거 유틸리티')
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
