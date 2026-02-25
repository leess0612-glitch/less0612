#!/usr/bin/env python3
"""
배경 제거 유틸리티 v4.0
U2Net AI 모델 + onnxruntime 직접 사용
모델 파일: ~/.u2net/u2netp.onnx (모델다운로드.bat 으로 설치)
"""

import sys
import os
import io
import numpy as np

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QListWidget, QListWidgetItem,
    QFileDialog, QProgressBar, QMessageBox, QFrame,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QUrl
from PyQt5.QtGui import QPixmap, QImage

from PIL import Image


MODEL_PATH  = os.path.join(os.path.expanduser('~'), '.u2net', 'u2netp.onnx')
INPUT_SIZE  = 320
IMG_EXTS    = {'.jpg', '.jpeg', '.png', '.webp', '.bmp'}


# ─── 드래그앤드랍 지원 목록 위젯 ─────────────────────────────────────────────
class DropListWidget(QListWidget):
    files_dropped = pyqtSignal(list)

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)

    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dragMoveEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dropEvent(self, e):
        paths = []
        for url in e.mimeData().urls():
            p = url.toLocalFile()
            if os.path.splitext(p)[1].lower() in IMG_EXTS:
                paths.append(p)
        if paths:
            self.files_dropped.emit(paths)


# ─── U2Net AI 배경 제거 ───────────────────────────────────────────────────────
def remove_background(pil_img: Image.Image) -> Image.Image:
    import cv2
    import onnxruntime as ort

    orig_w, orig_h = pil_img.size

    # 전처리
    img = pil_img.convert('RGB').resize((INPUT_SIZE, INPUT_SIZE), Image.BILINEAR)
    arr = np.array(img, dtype=np.float32) / 255.0
    arr = (arr - np.array([0.485, 0.456, 0.406])) / np.array([0.229, 0.224, 0.225])
    arr = arr.transpose(2, 0, 1)[np.newaxis].astype(np.float32)

    # 추론
    sess = ort.InferenceSession(MODEL_PATH, providers=['CPUExecutionProvider'])
    out  = sess.run(None, {sess.get_inputs()[0].name: arr})[0][0, 0]

    # 마스크 정규화
    out = (out - out.min()) / (out.max() - out.min() + 1e-8)
    mask = (out * 255).astype(np.uint8)

    # 가장 큰 연결 덩어리만 남기기 (파편 제거)
    _, binary = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(binary, connectivity=8)
    if num_labels > 2:
        largest = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
        binary  = np.where(labels == largest, 255, 0).astype(np.uint8)
        # 원본 마스크에서 파편 영역을 0으로
        mask = cv2.bitwise_and(mask, binary)

    # 원본 크기로 복원
    mask_img = Image.fromarray(mask).resize((orig_w, orig_h), Image.BILINEAR)

    result = pil_img.convert('RGBA')
    result.putalpha(mask_img)
    return result


# ─── 백그라운드 스레드 ────────────────────────────────────────────────────────
class RemoveThread(QThread):
    sig_progress = pyqtSignal(int, str)
    sig_preview  = pyqtSignal(bytes)
    sig_done     = pyqtSignal(str, int)
    sig_error    = pyqtSignal(str)

    def __init__(self, paths: list, out_dir: str):
        super().__init__()
        self.paths   = paths
        self.out_dir = out_dir

    def run(self):
        if not os.path.exists(MODEL_PATH):
            self.sig_error.emit(
                f'모델 파일이 없습니다.\n{MODEL_PATH}\n\n모델다운로드.bat 을 먼저 실행하세요.'
            )
            return

        try:
            import onnxruntime as ort
        except ImportError as e:
            self.sig_error.emit(f'onnxruntime import 실패:\n{e}')
            return
        except Exception as e:
            self.sig_error.emit(f'onnxruntime 로드 오류:\n{e}')
            return

        total = len(self.paths)
        first = True

        for i, src_path in enumerate(self.paths):
            fname = os.path.splitext(os.path.basename(src_path))[0] + '.png'
            self.sig_progress.emit(int(i / total * 100), fname)
            try:
                img    = Image.open(src_path).convert('RGBA')
                result = remove_background(img)

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

        self.setWindowTitle('배경 제거 유틸리티  v4.0  (AI 모델)')
        self.setMinimumSize(900, 580)
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
        w.setFixedWidth(240)
        vl = QVBoxLayout(w)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.setSpacing(6)

        lbl = QLabel('처리할 이미지 목록')
        lbl.setStyleSheet('font-weight: bold; font-size: 12px;')
        vl.addWidget(lbl)

        self.lst = DropListWidget()
        self.lst.setStyleSheet(
            'font-size: 11px; border: 1px solid #ccc; border-radius: 4px;'
        )
        self.lst.currentRowChanged.connect(self._on_select)
        self.lst.files_dropped.connect(self._add_paths)
        vl.addWidget(self.lst, 1)

        row = QHBoxLayout()
        self.btn_add = self._btn('+ 이미지 추가', '#2980b9')
        self.btn_del = self._btn('- 제거',        '#7f8c8d')
        row.addWidget(self.btn_add)
        row.addWidget(self.btn_del)
        vl.addLayout(row)

        self.lbl_dir = QLabel('저장 폴더: 원본과 같은 폴더 (기본값)')
        self.lbl_dir.setStyleSheet(
            'font-size: 10px; color: #666; border: 1px solid #ddd;'
            'border-radius: 3px; padding: 3px;'
        )
        self.lbl_dir.setWordWrap(True)
        vl.addWidget(self.lbl_dir)

        row2 = QHBoxLayout()
        self.btn_dir   = self._btn('폴더 직접 지정', '#8e44ad')
        self.btn_reset_dir = self._btn('기본값으로', '#7f8c8d')
        row2.addWidget(self.btn_dir)
        row2.addWidget(self.btn_reset_dir)
        vl.addLayout(row2)

        self.btn_run = self._btn('배경 제거 시작', '#e74c3c')
        self.btn_run.setFixedHeight(46)
        self.btn_run.setEnabled(False)
        vl.addWidget(self.btn_run)

        self.btn_add.clicked.connect(self._add_images)
        self.btn_del.clicked.connect(self._del_image)
        self.btn_dir.clicked.connect(self._select_dir)
        self.btn_reset_dir.clicked.connect(self._reset_dir)
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
        self._add_paths(paths)

    def _add_paths(self, paths: list):
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
        paths = [self.lst.item(i).data(Qt.UserRole) for i in range(self.lst.count())]

        self.prog.setMaximum(0)
        self.prog.setVisible(True)
        self.btn_run.setEnabled(False)
        self.btn_add.setEnabled(False)
        self.lbl_status.setText('AI 처리 중...')

        self._thread = RemoveThread(paths, self._out_dir)
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
        self.lst.clear()                          # 완료 후 목록 자동 초기화
        self.pane_orig.img_label.setText('—')
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
