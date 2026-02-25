#!/usr/bin/env python3
"""
배경 제거 유틸리티 v1.0
일반 사진에서 배경을 AI로 자동 제거하여 투명 PNG로 저장

필요 패키지: pip install PyQt5 Pillow "rembg[cpu]"
첫 실행 시 AI 모델 자동 다운로드 (~170MB)
"""

import sys
import os
import io

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QListWidget, QListWidgetItem,
    QFileDialog, QProgressBar, QMessageBox, QFrame,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QObject
from PyQt5.QtGui import QPixmap, QImage

from PIL import Image


# ─── 배경 제거 스레드 ────────────────────────────────────────────────────────────
class RemoveThread(QThread):
    sig_progress = pyqtSignal(int, str)   # (진행률, 현재 파일명)
    sig_preview  = pyqtSignal(bytes)      # 첫 번째 결과 미리보기
    sig_done     = pyqtSignal(str, int)   # (저장 폴더, 완료 수)
    sig_error    = pyqtSignal(str)

    def __init__(self, paths: list, out_dir: str):
        super().__init__()
        self.paths   = paths
        self.out_dir = out_dir

    def run(self):
        try:
            from rembg import remove
        except ImportError:
            self.sig_error.emit('rembg 패키지가 없습니다.\npip install rembg 를 실행하세요.')
            return

        total = len(self.paths)
        first = True

        for i, src_path in enumerate(self.paths):
            fname = os.path.splitext(os.path.basename(src_path))[0] + '.png'
            self.sig_progress.emit(int(i / total * 100), fname)

            try:
                img    = Image.open(src_path).convert('RGBA')
                result = remove(img)

                # 미리보기용 (첫 번째만)
                if first:
                    buf = io.BytesIO()
                    result.save(buf, 'PNG')
                    self.sig_preview.emit(buf.getvalue())
                    first = False

                result.save(os.path.join(self.out_dir, fname), 'PNG')

            except Exception as e:
                print(f'[오류] {fname}: {e}')

        self.sig_progress.emit(100, '완료')
        self.sig_done.emit(self.out_dir, total)


# ─── 미리보기 위젯 (원본 / 결과 나란히) ────────────────────────────────────────
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

        self.img_label = QLabel()
        self.img_label.setAlignment(Qt.AlignCenter)
        self.img_label.setMinimumSize(340, 280)
        self.img_label.setStyleSheet('color: #555; font-size: 13px;')
        self.img_label.setText('—')
        vl.addWidget(self.img_label, 1)

    def set_image_from_path(self, path: str):
        pix = QPixmap(path)
        self._show(pix)

    def set_image_from_bytes(self, data: bytes):
        pix = QPixmap.fromImage(QImage.fromData(data))
        self._show(pix)

    def set_image_from_pil(self, pil_img):
        buf = io.BytesIO()
        pil_img.save(buf, 'PNG')
        self.set_image_from_bytes(buf.getvalue())

    def _show(self, pix: QPixmap):
        self.img_label.setPixmap(
            pix.scaled(self.img_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        )


# ─── 메인 윈도우 ─────────────────────────────────────────────────────────────────
class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self._thread  = None
        self._out_dir = None

        self.setWindowTitle('배경 제거 유틸리티  —  AI 자동 배경 제거')
        self.setMinimumSize(900, 580)
        self.setStyleSheet(
            "QMainWindow, QWidget { font-family: 'Malgun Gothic', Arial, sans-serif; }"
        )
        self._build_ui()

    # ── UI ───────────────────────────────────────────────────────────────────
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

        # 파일 목록
        lbl = QLabel('처리할 이미지 목록')
        lbl.setStyleSheet('font-weight: bold; font-size: 12px;')
        vl.addWidget(lbl)

        self.lst = QListWidget()
        self.lst.setStyleSheet(
            'font-size: 11px; border: 1px solid #ccc; border-radius: 4px;'
        )
        self.lst.currentRowChanged.connect(self._on_select)
        vl.addWidget(self.lst, 1)

        # 추가 / 제거 버튼
        row = QHBoxLayout()
        self.btn_add = self._btn('+ 이미지 추가', '#2980b9')
        self.btn_del = self._btn('- 제거',        '#7f8c8d')
        row.addWidget(self.btn_add)
        row.addWidget(self.btn_del)
        vl.addLayout(row)

        # 저장 폴더
        self.lbl_dir = QLabel('저장 폴더: 미선택')
        self.lbl_dir.setStyleSheet(
            'font-size: 10px; color: #666; border: 1px solid #ddd;'
            'border-radius: 3px; padding: 3px;'
        )
        self.lbl_dir.setWordWrap(True)
        vl.addWidget(self.lbl_dir)

        self.btn_dir = self._btn('저장 폴더 선택', '#8e44ad')
        vl.addWidget(self.btn_dir)

        # 실행 버튼
        self.btn_run = self._btn('배경 제거 시작', '#e74c3c')
        self.btn_run.setFixedHeight(46)
        self.btn_run.setEnabled(False)
        vl.addWidget(self.btn_run)

        # 연결
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

        # 미리보기 (원본 | 결과)
        row = QHBoxLayout()
        self.pane_orig   = PreviewPane('원본')
        self.pane_result = PreviewPane('배경 제거 결과')
        row.addWidget(self.pane_orig)
        row.addWidget(self.pane_result)
        vl.addLayout(row, 1)

        # 상태 레이블
        self.lbl_status = QLabel(
            '이미지를 추가하고 저장 폴더를 선택한 후 [배경 제거 시작]을 눌러주세요.\n'
            '※ 첫 실행 시 AI 모델 다운로드로 시간이 걸릴 수 있습니다.'
        )
        self.lbl_status.setAlignment(Qt.AlignCenter)
        self.lbl_status.setStyleSheet('color: #666; font-size: 11px;')
        vl.addWidget(self.lbl_status)

        # 진행 바
        self.prog = QProgressBar()
        self.prog.setVisible(False)
        self.prog.setFixedHeight(18)
        self.prog.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ccc; border-radius: 4px;
                text-align: center; font-size: 11px;
            }
            QProgressBar::chunk { background: #e74c3c; border-radius: 3px; }
        """)
        vl.addWidget(self.prog)

        return w

    def _btn(self, text, color):
        b = QPushButton(text)
        b.setFixedHeight(34)
        b.setStyleSheet(f"""
            QPushButton {{
                background: {color}; color: white;
                border: none; border-radius: 5px;
                font-size: 12px; font-weight: bold;
            }}
            QPushButton:hover    {{ background: {color}bb; }}
            QPushButton:disabled {{ background: #bdc3c7; }}
        """)
        return b

    # ── 로직 ─────────────────────────────────────────────────────────────────
    def _add_images(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, '이미지 선택', '',
            'Images (*.jpg *.jpeg *.png *.webp *.bmp)',
        )
        for p in paths:
            it = QListWidgetItem(os.path.basename(p))
            it.setData(Qt.UserRole, p)
            self.lst.addItem(it)
        self._refresh_run_btn()

    def _del_image(self):
        for it in self.lst.selectedItems():
            self.lst.takeItem(self.lst.row(it))
        self._refresh_run_btn()

    def _select_dir(self):
        d = QFileDialog.getExistingDirectory(self, '저장 폴더 선택')
        if d:
            self._out_dir = d
            short = d if len(d) < 35 else '...' + d[-32:]
            self.lbl_dir.setText(f'저장 폴더: {short}')
        self._refresh_run_btn()

    def _refresh_run_btn(self):
        self.btn_run.setEnabled(
            self.lst.count() > 0 and self._out_dir is not None
        )

    def _on_select(self, row):
        """목록에서 항목 선택 시 원본 미리보기."""
        if row < 0:
            return
        path = self.lst.item(row).data(Qt.UserRole)
        self.pane_orig.set_image_from_path(path)
        self.pane_result.img_label.setText('—')

    def _run(self):
        paths = [
            self.lst.item(i).data(Qt.UserRole)
            for i in range(self.lst.count())
        ]
        self.prog.setVisible(True)
        self.prog.setValue(0)
        self.btn_run.setEnabled(False)
        self.btn_add.setEnabled(False)
        self.btn_del.setEnabled(False)
        self.lbl_status.setText('AI 모델 로딩 중... (첫 실행 시 다운로드)')

        self._thread = RemoveThread(paths, self._out_dir)
        self._thread.sig_progress.connect(self._on_progress)
        self._thread.sig_preview.connect(self._on_preview)
        self._thread.sig_done.connect(self._on_done)
        self._thread.sig_error.connect(self._on_error)
        self._thread.start()

    def _on_progress(self, pct: int, fname: str):
        self.prog.setValue(pct)
        self.lbl_status.setText(f'처리 중: {fname}  ({pct}%)')

    def _on_preview(self, data: bytes):
        self.pane_result.set_image_from_bytes(data)

    def _on_done(self, out_dir: str, count: int):
        self.prog.setValue(100)
        self.prog.setVisible(False)
        self.btn_run.setEnabled(True)
        self.btn_add.setEnabled(True)
        self.btn_del.setEnabled(True)
        self.lbl_status.setText(f'완료: {count}장 저장  →  {out_dir}')
        QMessageBox.information(
            self, '완료',
            f'{count}장의 배경이 제거되어 PNG로 저장되었습니다.\n\n저장 위치:\n{out_dir}',
        )

    def _on_error(self, msg: str):
        self.prog.setVisible(False)
        self.btn_run.setEnabled(True)
        self.btn_add.setEnabled(True)
        self.btn_del.setEnabled(True)
        QMessageBox.critical(self, '오류', msg)


# ─── 진입점 ──────────────────────────────────────────────────────────────────
def main():
    app = QApplication(sys.argv)
    app.setApplicationName('배경 제거 유틸리티')
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
