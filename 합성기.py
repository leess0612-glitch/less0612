#!/usr/bin/env python3
"""
이미지 합성기 v1.0
블로그 포스팅용 이미지 세트 자동 생성기
캔버스: 1800 × 1200 (3:2 비율)

필요 패키지: pip install PyQt5 Pillow
"""

import sys
import os
import random
import io

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget,
    QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QSlider,
    QListWidget, QListWidgetItem,
    QFileDialog, QGroupBox,
    QProgressBar, QMessageBox, QFrame,
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QPixmap, QImage

from PIL import Image, ImageEnhance

# ─── 상수 ──────────────────────────────────────────────────────────────────────
CANVAS_W = 1800
CANVAS_H = 1200
REP_MAX  = 700   # 대표이미지 최대 크기(px) — 가로 또는 세로 중 긴 쪽 기준

# 왼쪽 존 경계: 캔버스 폭의 0 ~ 33%
LEFT_ZONE_END   = 0.33
# 오른쪽 존 경계: 캔버스 폭의 67% ~ 100%
RIGHT_ZONE_START = 0.67


# ─── 합성 상태 모델 ─────────────────────────────────────────────────────────────
class ComposerState:
    """현재 세션의 이미지 풀 및 확정된 구성 값을 보관."""

    def __init__(self):
        self.reset()

    def reset(self):
        # 이미지 풀
        self.backgrounds    = []
        self.left_elements  = []
        self.right_elements = []
        self.rep_images     = []

        # 확정된 선택값
        self.current_bg    = None
        self.current_left  = None
        self.current_right = None
        self.left_pos      = (0, 0)
        self.right_pos     = (0, 0)

        # 슬라이더 연동값
        self.left_scale  = 0.5
        self.right_scale = 0.5
        self.saturation  = 1.0   # 1.0 = 원본
        self.brightness  = 1.0

        self.locked = False   # 랜덤 구성 후 True

    # ── 랜덤 선택 + 배치 ──────────────────────────────────────────────────────
    def randomize(self):
        """배경·장식 요소를 랜덤 선택하고 위치를 결정한다."""
        if self.backgrounds:
            self.current_bg = random.choice(self.backgrounds)
        if self.left_elements:
            self.current_left = random.choice(self.left_elements)
        if self.right_elements:
            self.current_right = random.choice(self.right_elements)

        self._place_elements()
        self.locked = True

    def _place_elements(self):
        """각 장식 요소의 좌표를 존(Zone) 안에서 랜덤 결정."""
        # 왼쪽 존: x = [0, CANVAS_W * LEFT_ZONE_END - 요소폭]
        if self.current_left:
            lw, lh = self._img_size(self.current_left, self.left_scale)
            max_x = max(0, int(CANVAS_W * LEFT_ZONE_END) - lw)
            max_y = max(0, CANVAS_H - lh)
            self.left_pos = (
                random.randint(0, max_x),
                random.randint(0, max_y),
            )

        # 오른쪽 존: x = [CANVAS_W * RIGHT_ZONE_START, CANVAS_W - 요소폭]
        if self.current_right:
            rw, rh = self._img_size(self.current_right, self.right_scale)
            min_x = int(CANVAS_W * RIGHT_ZONE_START)
            max_x = max(min_x, CANVAS_W - rw)
            max_y = max(0, CANVAS_H - rh)
            self.right_pos = (
                random.randint(min_x, max_x),
                random.randint(0, max_y),
            )

    # ── 유틸 ──────────────────────────────────────────────────────────────────
    def _img_size(self, path, scale):
        try:
            with Image.open(path) as img:
                return int(img.width * scale), int(img.height * scale)
        except Exception:
            return 200, 200

    # ── 합성 ──────────────────────────────────────────────────────────────────
    def compose(self, rep_path):
        """
        레이어 순서: 배경 → 왼쪽 장식 → 오른쪽 장식 → 대표이미지(최상단)
        채도·명도는 최종 합성 이미지에 일괄 적용.
        """
        canvas = Image.new('RGBA', (CANVAS_W, CANVAS_H), (220, 220, 220, 255))

        # 1. 배경
        if self.current_bg:
            try:
                bg = Image.open(self.current_bg).convert('RGBA')
                bg = bg.resize((CANVAS_W, CANVAS_H), Image.LANCZOS)
                canvas.paste(bg, (0, 0), bg)
            except Exception as e:
                print(f'[배경 오류] {e}')

        # 2. 왼쪽 장식
        if self.current_left:
            try:
                lw, lh = self._img_size(self.current_left, self.left_scale)
                img = Image.open(self.current_left).convert('RGBA')
                img = img.resize((lw, lh), Image.LANCZOS)
                lx = max(0, min(self.left_pos[0], CANVAS_W - lw))
                ly = max(0, min(self.left_pos[1], CANVAS_H - lh))
                canvas.paste(img, (lx, ly), img)
            except Exception as e:
                print(f'[왼쪽 요소 오류] {e}')

        # 3. 오른쪽 장식
        if self.current_right:
            try:
                rw, rh = self._img_size(self.current_right, self.right_scale)
                img = Image.open(self.current_right).convert('RGBA')
                img = img.resize((rw, rh), Image.LANCZOS)
                rx = max(0, min(self.right_pos[0], CANVAS_W - rw))
                ry = max(0, min(self.right_pos[1], CANVAS_H - rh))
                canvas.paste(img, (rx, ry), img)
            except Exception as e:
                print(f'[오른쪽 요소 오류] {e}')

        # 4. 대표이미지 (중앙 고정, 최상단)
        if rep_path:
            try:
                rep = Image.open(rep_path).convert('RGBA')
                rep.thumbnail((REP_MAX, REP_MAX), Image.LANCZOS)
                rx = (CANVAS_W - rep.width)  // 2
                ry = (CANVAS_H - rep.height) // 2
                canvas.paste(rep, (rx, ry), rep)
            except Exception as e:
                print(f'[대표이미지 오류] {e}')

        # 5. 채도 / 명도 적용
        result = canvas.convert('RGB')
        result = ImageEnhance.Color(result).enhance(self.saturation)
        result = ImageEnhance.Brightness(result).enhance(self.brightness)
        return result


# ─── 백그라운드 생성 스레드 ──────────────────────────────────────────────────────
class GenerateThread(QThread):
    sig_progress = pyqtSignal(int)
    sig_done     = pyqtSignal(str, int)

    def __init__(self, state: ComposerState, out_dir: str, start_idx: int):
        super().__init__()
        self.state     = state
        self.out_dir   = out_dir
        self.start_idx = start_idx

    def run(self):
        total = len(self.state.rep_images)
        for i, rep_path in enumerate(self.state.rep_images):
            img   = self.state.compose(rep_path)
            fname = f'{self.start_idx + i:03d}.png'
            img.save(os.path.join(self.out_dir, fname), 'PNG')
            self.sig_progress.emit(int((i + 1) / total * 100))
        self.sig_done.emit(self.out_dir, total)


# ─── 이미지 풀 위젯 ──────────────────────────────────────────────────────────────
class ImagePool(QWidget):
    """이미지 목록 등록/제거 위젯 (배경·장식·대표이미지에 재사용)."""

    def __init__(self, title: str, color: str):
        super().__init__()
        self.color = color
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(2)

        box = QGroupBox(title)
        box.setStyleSheet(f"""
            QGroupBox {{
                font-weight: bold;
                font-size: 12px;
                border: 2px solid {color};
                border-radius: 6px;
                margin-top: 8px;
                padding: 6px 4px 4px 4px;
                color: {color};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px;
            }}
        """)
        inner = QVBoxLayout(box)
        inner.setSpacing(3)
        inner.setContentsMargins(4, 2, 4, 4)

        self.lst = QListWidget()
        self.lst.setMaximumHeight(75)
        self.lst.setStyleSheet(
            'font-size: 11px; border: 1px solid #ddd; border-radius: 3px;'
        )
        inner.addWidget(self.lst)

        row = QHBoxLayout()
        self.btn_add = QPushButton('+ 추가')
        self.btn_del = QPushButton('- 제거')
        for b in (self.btn_add, self.btn_del):
            b.setStyleSheet(f"""
                QPushButton {{
                    padding: 3px 8px;
                    font-size: 11px;
                    border: 1px solid {color};
                    border-radius: 3px;
                    background: white;
                    color: {color};
                }}
                QPushButton:hover {{ background: {color}22; }}
            """)
            row.addWidget(b)
        inner.addLayout(row)
        root.addWidget(box)

        self.btn_add.clicked.connect(self._add)
        self.btn_del.clicked.connect(self._del)

    def _add(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, '이미지 선택', '',
            'Images (*.png *.jpg *.jpeg *.webp)',
        )
        for p in paths:
            it = QListWidgetItem(os.path.basename(p))
            it.setData(Qt.UserRole, p)
            self.lst.addItem(it)

    def _del(self):
        for it in self.lst.selectedItems():
            self.lst.takeItem(self.lst.row(it))

    def paths(self):
        return [self.lst.item(i).data(Qt.UserRole) for i in range(self.lst.count())]

    def clear(self):
        self.lst.clear()


# ─── 메인 윈도우 ─────────────────────────────────────────────────────────────────
class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.state        = ComposerState()
        self.out_dir      = None
        self.file_counter = 1
        self._gen_thread  = None

        # 슬라이더 debounce (연속 드래그 시 불필요한 재렌더 방지)
        self._preview_timer = QTimer(self)
        self._preview_timer.setSingleShot(True)
        self._preview_timer.timeout.connect(self._do_preview)

        self.setWindowTitle('이미지 합성기  —  1800 × 1200')
        self.setMinimumSize(1080, 740)
        self.setStyleSheet(
            "QMainWindow, QWidget { font-family: 'Malgun Gothic', Arial, sans-serif; }"
        )
        self._build_ui()

    # ── UI 구성 ───────────────────────────────────────────────────────────────
    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        hl = QHBoxLayout(root)
        hl.setContentsMargins(10, 10, 10, 10)
        hl.setSpacing(10)
        hl.addWidget(self._build_left_panel(),  0)
        hl.addWidget(self._build_right_panel(), 1)

    # ── 왼쪽 패널 (설정) ─────────────────────────────────────────────────────
    def _build_left_panel(self):
        w = QWidget()
        w.setFixedWidth(268)
        vl = QVBoxLayout(w)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.setSpacing(5)

        self.pool_bg    = ImagePool('배경 이미지',        '#8e44ad')
        self.pool_left  = ImagePool('왼쪽 장식 요소',     '#2980b9')
        self.pool_right = ImagePool('오른쪽 장식 요소',   '#27ae60')
        self.pool_rep   = ImagePool('대표 이미지 (세트)', '#e74c3c')

        for p in (self.pool_bg, self.pool_left, self.pool_right, self.pool_rep):
            vl.addWidget(p)

        vl.addWidget(self._build_size_group())
        vl.addWidget(self._build_color_group())
        vl.addStretch()
        return w

    def _build_size_group(self):
        box = QGroupBox('요소 크기 조절')
        box.setStyleSheet(self._group_css('#7f8c8d'))
        vl = QVBoxLayout(box)
        vl.setSpacing(3)
        vl.setContentsMargins(6, 4, 6, 6)

        self.lbl_ls = QLabel('왼쪽 크기: 50%')
        self.sld_ls = self._make_slider(10, 100, 50)
        self.sld_ls.valueChanged.connect(
            lambda v: self.lbl_ls.setText(f'왼쪽 크기: {v}%')
        )
        self.sld_ls.valueChanged.connect(self._on_slider_changed)

        self.lbl_rs = QLabel('오른쪽 크기: 50%')
        self.sld_rs = self._make_slider(10, 100, 50)
        self.sld_rs.valueChanged.connect(
            lambda v: self.lbl_rs.setText(f'오른쪽 크기: {v}%')
        )
        self.sld_rs.valueChanged.connect(self._on_slider_changed)

        for w in (self.lbl_ls, self.sld_ls, self.lbl_rs, self.sld_rs):
            vl.addWidget(w)
        return box

    def _build_color_group(self):
        box = QGroupBox('채도 / 명도 조절  (전체 이미지 적용)')
        box.setStyleSheet(self._group_css('#7f8c8d'))
        vl = QVBoxLayout(box)
        vl.setSpacing(3)
        vl.setContentsMargins(6, 4, 6, 6)

        self.lbl_sat = QLabel('채도: ±0%')
        self.sld_sat = self._make_slider(-50, 50, 0)
        self.sld_sat.valueChanged.connect(
            lambda v: self.lbl_sat.setText(f'채도: {v:+d}%')
        )
        self.sld_sat.valueChanged.connect(self._on_slider_changed)

        self.lbl_bri = QLabel('명도: ±0%')
        self.sld_bri = self._make_slider(-50, 50, 0)
        self.sld_bri.valueChanged.connect(
            lambda v: self.lbl_bri.setText(f'명도: {v:+d}%')
        )
        self.sld_bri.valueChanged.connect(self._on_slider_changed)

        for w in (self.lbl_sat, self.sld_sat, self.lbl_bri, self.sld_bri):
            vl.addWidget(w)
        return box

    def _group_css(self, color):
        return f"""
            QGroupBox {{
                font-weight: bold;
                font-size: 12px;
                border: 2px solid {color};
                border-radius: 6px;
                margin-top: 8px;
                padding: 6px 4px 4px 4px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px;
            }}
        """

    def _make_slider(self, mn, mx, val):
        s = QSlider(Qt.Horizontal)
        s.setRange(mn, mx)
        s.setValue(val)
        return s

    # ── 오른쪽 패널 (미리보기 + 버튼) ────────────────────────────────────────
    def _build_right_panel(self):
        w = QWidget()
        vl = QVBoxLayout(w)
        vl.setContentsMargins(0, 0, 0, 0)
        vl.setSpacing(8)

        # 미리보기 영역
        frame = QFrame()
        frame.setStyleSheet('QFrame { background: #1a1a1a; border-radius: 8px; }')
        fl = QVBoxLayout(frame)
        fl.setContentsMargins(8, 8, 8, 8)

        self.lbl_preview = QLabel(
            '이미지를 등록한 후\n[랜덤 구성] 버튼을 눌러주세요'
        )
        self.lbl_preview.setAlignment(Qt.AlignCenter)
        self.lbl_preview.setStyleSheet('color: #555; font-size: 14px;')
        self.lbl_preview.setMinimumSize(520, 340)
        fl.addWidget(self.lbl_preview)
        vl.addWidget(frame, 1)

        # 상태 텍스트
        self.lbl_status = QLabel('대기 중')
        self.lbl_status.setAlignment(Qt.AlignCenter)
        self.lbl_status.setStyleSheet('color: #555; font-size: 11px;')
        vl.addWidget(self.lbl_status)

        # 진행 바
        self.prog = QProgressBar()
        self.prog.setVisible(False)
        self.prog.setFixedHeight(18)
        self.prog.setStyleSheet("""
            QProgressBar {
                border: 1px solid #ccc;
                border-radius: 4px;
                text-align: center;
                font-size: 11px;
            }
            QProgressBar::chunk { background: #3498db; border-radius: 3px; }
        """)
        vl.addWidget(self.prog)

        # 버튼 행
        row = QHBoxLayout()
        self.btn_new  = self._make_btn('새로만들기', '#95a5a6')
        self.btn_rand = self._make_btn('랜덤 구성',  '#3498db')
        self.btn_gen  = self._make_btn('세트 생성',  '#e74c3c')
        self.btn_gen.setEnabled(False)

        for b in (self.btn_new, self.btn_rand, self.btn_gen):
            row.addWidget(b)
        vl.addLayout(row)

        # 버튼 연결
        self.btn_new.clicked.connect(self._new_project)
        self.btn_rand.clicked.connect(self._randomize)
        self.btn_gen.clicked.connect(self._generate)

        return w

    def _make_btn(self, text, color):
        b = QPushButton(text)
        b.setFixedHeight(42)
        b.setStyleSheet(f"""
            QPushButton {{
                background: {color};
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover    {{ background: {color}cc; }}
            QPushButton:disabled {{ background: #bdc3c7; color: #fff; }}
        """)
        return b

    # ── 핵심 로직 ─────────────────────────────────────────────────────────────
    def _sync_state(self):
        """슬라이더·풀 값을 state에 반영 (위치 재결정 없이)."""
        self.state.backgrounds    = self.pool_bg.paths()
        self.state.left_elements  = self.pool_left.paths()
        self.state.right_elements = self.pool_right.paths()
        self.state.rep_images     = self.pool_rep.paths()
        self.state.left_scale     = self.sld_ls.value()  / 100.0
        self.state.right_scale    = self.sld_rs.value()  / 100.0
        self.state.saturation     = 1.0 + self.sld_sat.value() / 100.0
        self.state.brightness     = 1.0 + self.sld_bri.value() / 100.0

    def _on_slider_changed(self):
        """슬라이더 변경 → 300ms 후 미리보기 갱신 (debounce)."""
        self._preview_timer.start(300)

    def _randomize(self):
        """배경·장식 요소 랜덤 선택 및 배치 → 미리보기."""
        self._sync_state()

        if not self.state.backgrounds:
            QMessageBox.warning(self, '경고', '배경 이미지를 먼저 등록하세요.')
            return
        if not self.state.rep_images:
            QMessageBox.warning(self, '경고', '대표 이미지를 먼저 등록하세요.')
            return

        self.state.randomize()
        self._do_preview()
        self.btn_gen.setEnabled(True)

        n = len(self.state.rep_images)
        self.lbl_status.setText(
            f'랜덤 구성 완료  —  대표이미지 {n}장 세트 생성 가능'
        )

    def _do_preview(self):
        """대표이미지 1번째 기준으로 미리보기 렌더링."""
        if not self.state.locked:
            return

        self._sync_state()
        reps = self.state.rep_images
        if not reps:
            return

        try:
            img = self.state.compose(reps[0])
            buf = io.BytesIO()
            img.save(buf, 'PNG')
            pix = QPixmap.fromImage(QImage.fromData(buf.getvalue()))
            self.lbl_preview.setPixmap(
                pix.scaled(
                    self.lbl_preview.size(),
                    Qt.KeepAspectRatio,
                    Qt.SmoothTransformation,
                )
            )
        except Exception as e:
            self.lbl_status.setText(f'미리보기 오류: {e}')

    def _generate(self):
        """대표이미지 전체를 순서대로 합성하여 저장."""
        self._sync_state()

        if not self.state.locked:
            QMessageBox.warning(self, '경고', '먼저 [랜덤 구성]을 실행하세요.')
            return
        if not self.state.rep_images:
            QMessageBox.warning(self, '경고', '대표 이미지가 없습니다.')
            return

        # 저장 폴더 선택 (세션 중 최초 1회)
        if not self.out_dir:
            d = QFileDialog.getExistingDirectory(self, '저장 폴더 선택')
            if not d:
                return
            self.out_dir = d

        self.prog.setVisible(True)
        self.prog.setValue(0)
        self.btn_gen.setEnabled(False)
        self.btn_rand.setEnabled(False)
        self.btn_new.setEnabled(False)
        self.lbl_status.setText('생성 중...')

        self._gen_thread = GenerateThread(
            self.state, self.out_dir, self.file_counter
        )
        self._gen_thread.sig_progress.connect(self.prog.setValue)
        self._gen_thread.sig_done.connect(self._on_generate_done)
        self._gen_thread.start()

    def _on_generate_done(self, out_dir: str, count: int):
        self.file_counter += count
        self.prog.setVisible(False)
        self.btn_gen.setEnabled(True)
        self.btn_rand.setEnabled(True)
        self.btn_new.setEnabled(True)
        self.lbl_status.setText(
            f'완료: {count}장 저장  |  다음 번호: {self.file_counter:03d}  |  폴더: {out_dir}'
        )
        QMessageBox.information(
            self, '세트 생성 완료',
            f'{count}장이 저장되었습니다.\n\n저장 위치:\n{out_dir}',
        )

    def _new_project(self):
        """모든 설정 초기화."""
        if QMessageBox.question(
            self, '새로만들기',
            '현재 설정을 모두 초기화하시겠습니까?\n(저장된 파일에는 영향 없음)',
            QMessageBox.Yes | QMessageBox.No,
        ) != QMessageBox.Yes:
            return

        self.state.reset()
        for p in (self.pool_bg, self.pool_left, self.pool_right, self.pool_rep):
            p.clear()

        self.lbl_preview.clear()
        self.lbl_preview.setText(
            '이미지를 등록한 후\n[랜덤 구성] 버튼을 눌러주세요'
        )
        self.sld_ls.setValue(50)
        self.sld_rs.setValue(50)
        self.sld_sat.setValue(0)
        self.sld_bri.setValue(0)
        self.btn_gen.setEnabled(False)
        self.out_dir      = None
        self.file_counter = 1
        self.lbl_status.setText('대기 중')

    # ── 창 리사이즈 시 미리보기 재조정 ───────────────────────────────────────
    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.state.locked:
            self._preview_timer.start(200)


# ─── 진입점 ──────────────────────────────────────────────────────────────────
def main():
    app = QApplication(sys.argv)
    app.setApplicationName('이미지 합성기')
    win = MainWindow()
    win.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
