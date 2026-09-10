"""Conan World Transfer — a calm, story-first front end for Conan Exiles Enhanced save ownership."""

from __future__ import annotations

import csv
import json
import os
import shutil
import sys
import time
from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import Qt, QSettings, QSize, QTimer
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPen, QPixmap
from PySide6.QtWidgets import (
    QApplication,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QCheckBox,
    QPushButton,
    QFileDialog,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QDialog,
    QDialogButtonBox,
    QHeaderView,
    QComboBox,
    QStackedWidget,
    QFrame,
    QScrollArea,
    QSizePolicy,
    QGraphicsDropShadowEffect,
    QButtonGroup,
    QAbstractButton,
)

import db_utils


def _bundle_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(getattr(sys, "_MEIPASS", Path(sys.executable).parent))
    return Path(__file__).resolve().parent


def _app_dir() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


BUNDLE_DIR = _bundle_dir()
APP_DIR = _app_dir()
ICON_PATH = BUNDLE_DIR / "icon.ico"

# Sand-and-bronze palette. Warm paper in light, deep ink in dark.
LIGHT = {
    "bg": "#f4efe6",
    "bg2": "#ebe4d6",
    "surface": "#fffaf2",
    "surface2": "#f7f1e6",
    "fg": "#1c1710",
    "muted": "#6f6558",
    "faint": "#9a8f80",
    "accent": "#9a4a16",
    "accent2": "#c46a2c",
    "accent_fg": "#fffaf2",
    "ok": "#3f6b4a",
    "warn": "#9a4a16",
    "danger": "#8f2d2d",
    "border": "#e0d6c4",
    "shadow": "#1c171018",
    "nav": "#fffaf2",
    "nav_active": "#f0e2cc",
    "input": "#fffdf8",
    "table": "#fffdf8",
    "alt": "#f3eadc",
    "sel": "#f0d9b8",
    "chip": "#efe4d2",
}

DARK = {
    "bg": "#12100e",
    "bg2": "#1a1714",
    "surface": "#1e1a16",
    "surface2": "#26211c",
    "fg": "#f3eadc",
    "muted": "#b3a494",
    "faint": "#7d7266",
    "accent": "#e08a45",
    "accent2": "#c46a2c",
    "accent_fg": "#1c1710",
    "ok": "#7dba88",
    "warn": "#e08a45",
    "danger": "#e07a7a",
    "border": "#3a322a",
    "shadow": "#00000055",
    "nav": "#1a1714",
    "nav_active": "#2c241c",
    "input": "#161310",
    "table": "#161310",
    "alt": "#1c1814",
    "sel": "#3d2c1c",
    "chip": "#2a241e",
}


def build_stylesheet(pal: dict) -> str:
    return f"""
    QWidget {{
        background: {pal['bg']};
        color: {pal['fg']};
        font-family: 'Segoe UI', 'Inter', 'SF Pro Text', 'Ubuntu', 'Noto Sans', sans-serif;
        font-size: 14px;
    }}
    QMainWindow, QDialog, QScrollArea, QStackedWidget {{
        background: {pal['bg']};
    }}
    QScrollArea {{ border: none; }}
    QScrollArea > QWidget > QWidget {{ background: transparent; }}

    QLabel {{ background: transparent; color: {pal['fg']}; }}
    QLabel#hero {{ font-size: 28px; font-weight: 650; letter-spacing: -0.4px; }}
    QLabel#title {{ font-size: 22px; font-weight: 650; letter-spacing: -0.3px; }}
    QLabel#subtitle {{ font-size: 15px; color: {pal['muted']}; }}
    QLabel#muted {{ color: {pal['muted']}; }}
    QLabel#faint {{ color: {pal['faint']}; font-size: 12px; }}
    QLabel#chip {{
        background: {pal['chip']};
        color: {pal['muted']};
        border-radius: 11px;
        padding: 3px 10px;
        font-size: 12px;
    }}
    QLabel#warn {{ color: {pal['warn']}; }}
    QLabel#ok {{ color: {pal['ok']}; }}
    QLabel#section {{
        font-size: 11px;
        font-weight: 700;
        letter-spacing: 1.2px;
        text-transform: uppercase;
        color: {pal['faint']};
    }}

    QFrame#card {{
        background: {pal['surface']};
        border: 1px solid {pal['border']};
        border-radius: 16px;
    }}
    QFrame#nav {{
        background: {pal['nav']};
        border-right: 1px solid {pal['border']};
    }}
    QFrame#topbar {{
        background: {pal['surface']};
        border-bottom: 1px solid {pal['border']};
    }}
    QFrame#hairline {{
        background: {pal['border']};
        max-height: 1px;
        min-height: 1px;
        border: none;
    }}

    QPushButton {{
        background: {pal['surface2']};
        color: {pal['fg']};
        border: 1px solid {pal['border']};
        border-radius: 10px;
        padding: 9px 16px;
        font-weight: 600;
    }}
    QPushButton:hover {{ background: {pal['alt']}; }}
    QPushButton:pressed {{ background: {pal['sel']}; }}
    QPushButton:disabled {{
        color: {pal['faint']};
        background: {pal['bg2']};
        border-color: {pal['border']};
    }}
    QPushButton#primary {{
        background: {pal['accent']};
        color: {pal['accent_fg']};
        border: 1px solid {pal['accent']};
    }}
    QPushButton#primary:hover {{ background: {pal['accent2']}; border-color: {pal['accent2']}; }}
    QPushButton#primary:disabled {{
        background: {pal['bg2']};
        color: {pal['faint']};
        border-color: {pal['border']};
    }}
    QPushButton#ghost {{
        background: transparent;
        border: 1px solid transparent;
        text-align: left;
        padding: 10px 14px;
        font-weight: 600;
        border-radius: 12px;
    }}
    QPushButton#ghost:hover {{ background: {pal['nav_active']}; }}
    QPushButton#ghost:checked {{
        background: {pal['nav_active']};
        border: 1px solid {pal['border']};
        color: {pal['accent']};
    }}
    QPushButton#story {{
        background: {pal['surface']};
        border: 1px solid {pal['border']};
        border-radius: 16px;
        text-align: left;
        padding: 18px 20px;
        font-weight: 600;
        font-size: 15px;
    }}
    QPushButton#story:hover {{
        border-color: {pal['accent']};
        background: {pal['surface2']};
    }}
    QPushButton#iconbtn {{
        min-width: 40px;
        max-width: 44px;
        min-height: 40px;
        border-radius: 12px;
        padding: 0;
        font-size: 16px;
    }}

    QLineEdit, QComboBox {{
        background: {pal['input']};
        color: {pal['fg']};
        border: 1px solid {pal['border']};
        border-radius: 10px;
        padding: 9px 12px;
        min-height: 20px;
        selection-background-color: {pal['sel']};
    }}
    QLineEdit:focus, QComboBox:focus {{
        border: 1px solid {pal['accent']};
    }}
    QComboBox::drop-down {{
        border: none;
        width: 28px;
    }}
    QComboBox QAbstractItemView {{
        background: {pal['surface']};
        color: {pal['fg']};
        border: 1px solid {pal['border']};
        selection-background-color: {pal['sel']};
        outline: none;
        padding: 4px;
    }}

    QCheckBox {{ color: {pal['fg']}; spacing: 8px; }}
    QCheckBox::indicator {{
        width: 18px; height: 18px;
        border-radius: 5px;
        border: 1px solid {pal['border']};
        background: {pal['input']};
    }}
    QCheckBox::indicator:checked {{
        background: {pal['accent']};
        border-color: {pal['accent']};
    }}
    QCheckBox::indicator:hover {{ border-color: {pal['accent']}; }}
    QCheckBox::indicator:disabled {{
        background: {pal['bg2']};
        border-color: {pal['border']};
    }}

    QTableWidget {{
        background: {pal['table']};
        alternate-background-color: {pal['alt']};
        color: {pal['fg']};
        border: 1px solid {pal['border']};
        border-radius: 12px;
        gridline-color: {pal['border']};
        selection-background-color: {pal['sel']};
        selection-color: {pal['fg']};
    }}
    QTableWidget::item {{ padding: 8px; }}
    QHeaderView::section {{
        background: {pal['surface2']};
        color: {pal['muted']};
        padding: 8px 10px;
        border: none;
        border-bottom: 1px solid {pal['border']};
        font-weight: 600;
        font-size: 12px;
    }}
    QTableCornerButton::section {{ background: {pal['surface2']}; border: none; }}

    QScrollBar:vertical {{
        background: transparent;
        width: 10px;
        margin: 4px;
    }}
    QScrollBar::handle:vertical {{
        background: {pal['border']};
        border-radius: 5px;
        min-height: 32px;
    }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
    QScrollBar:horizontal {{
        background: transparent;
        height: 10px;
        margin: 4px;
    }}
    QScrollBar::handle:horizontal {{
        background: {pal['border']};
        border-radius: 5px;
        min-width: 32px;
    }}
    QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width: 0; }}

    QToolTip {{
        background: {pal['surface']};
        color: {pal['fg']};
        border: 1px solid {pal['border']};
        padding: 6px 8px;
    }}
    """


def _char_label(c: dict) -> str:
    name = c.get("char_name") or str(c.get("id"))
    guild = c.get("guild_name")
    if guild:
        return f"{name}    ·    clan {guild}    ·    id {c.get('id')}"
    return f"{name}    ·    no clan    ·    id {c.get('id')}"


def _account_label(a: dict) -> str:
    user = a.get("user") or "(empty)"
    return f"Account {a.get('id')}  ·  {user}"


def _shadow(widget: QWidget, pal: dict) -> None:
    fx = QGraphicsDropShadowEffect(widget)
    fx.setBlurRadius(28)
    fx.setOffset(0, 8)
    fx.setColor(QColor(0, 0, 0, 28))
    widget.setGraphicsEffect(fx)


def card() -> QFrame:
    f = QFrame()
    f.setObjectName("card")
    return f


def vbox(parent=None, gap=12, m=0) -> QVBoxLayout:
    lay = QVBoxLayout(parent) if parent is not None else QVBoxLayout()
    lay.setSpacing(gap)
    if isinstance(m, tuple):
        lay.setContentsMargins(*m)
    else:
        lay.setContentsMargins(m, m, m, m)
    return lay


def hbox(parent=None, gap=10, m=0) -> QHBoxLayout:
    lay = QHBoxLayout(parent) if parent is not None else QHBoxLayout()
    lay.setSpacing(gap)
    if isinstance(m, tuple):
        lay.setContentsMargins(*m)
    else:
        lay.setContentsMargins(m, m, m, m)
    return lay


def label(text: str, name: str = "") -> QLabel:
    w = QLabel(text)
    if name:
        w.setObjectName(name)
    w.setWordWrap(True)
    return w


def primary_btn(text: str) -> QPushButton:
    b = QPushButton(text)
    b.setObjectName("primary")
    b.setCursor(Qt.PointingHandCursor)
    return b


def ghost_btn(text: str, checkable: bool = False) -> QPushButton:
    b = QPushButton(text)
    b.setObjectName("ghost")
    b.setCheckable(checkable)
    b.setCursor(Qt.PointingHandCursor)
    return b


class TransferApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Conan World Transfer")
        self.setMinimumSize(1080, 720)
        try:
            ico = QIcon(str(ICON_PATH))
            if not ico.isNull():
                self.setWindowIcon(ico)
        except Exception:
            pass

        self.settings = QSettings("ConanWorldTransfer", "ui")
        self.selected_item_keys = None
        self.selected_building_object_ids = None
        self.selected_thrall_ids = None
        self.current_theme = self.settings.value("theme", "light")
        self._building_ui()
        self.apply_theme(self.current_theme)
        db_guess = Path.cwd() / "game.db"
        if db_guess.exists():
            self.db_path.setText(str(db_guess))
            self.on_db_changed()

    # ── chrome ─────────────────────────────────────────────
    def _building_ui(self):
        root = hbox(self, gap=0, m=0)

        nav = QFrame()
        nav.setObjectName("nav")
        nav.setFixedWidth(248)
        nv = vbox(nav, gap=6, m=(18, 22, 18, 22))
        brand = label("World Transfer", "hero")
        brand.setStyleSheet("font-size: 20px;")
        tag = label("Conan Exiles saves", "faint")
        nv.addWidget(brand)
        nv.addWidget(tag)
        nv.addSpacing(18)
        nv.addWidget(label("Do this", "section"))

        self.nav_group = QButtonGroup(self)
        self.nav_group.setExclusive(True)
        self.btn_home = ghost_btn("Home", True)
        self.btn_nav_transfer = ghost_btn("Move belongings", True)
        self.btn_nav_handoff = ghost_btn("Give the world", True)
        self.btn_nav_look = ghost_btn("Look at the save", True)
        self.btn_nav_history = ghost_btn("History", True)
        self.btn_nav_restore = ghost_btn("Put it back", True)
        for i, b in enumerate(
            (
                self.btn_home,
                self.btn_nav_transfer,
                self.btn_nav_handoff,
                self.btn_nav_look,
                self.btn_nav_history,
                self.btn_nav_restore,
            )
        ):
            self.nav_group.addButton(b, i)
            nv.addWidget(b)
        self.btn_home.setChecked(True)
        nv.addStretch(1)

        self.btn_theme = QPushButton()
        self.btn_theme.setObjectName("iconbtn")
        self.btn_theme.setFixedSize(44, 44)
        self.btn_theme.setIconSize(QSize(22, 22))
        self.btn_theme.setCursor(Qt.PointingHandCursor)
        self.btn_theme.clicked.connect(self.toggle_theme)
        nv.addWidget(self.btn_theme, 0, Qt.AlignLeft)
        hint = label("Stop the server and the game before any write.", "faint")
        nv.addWidget(hint)

        right = QWidget()
        rv = vbox(right, gap=0, m=0)

        top = QFrame()
        top.setObjectName("topbar")
        tv = hbox(top, gap=10, m=(20, 14, 20, 14))
        tv.addWidget(label("Save file", "muted"))
        self.db_path = QLineEdit()
        self.db_path.setPlaceholderText("Choose game.db — usually in the server Saved folder")
        self.db_path.editingFinished.connect(self.on_db_changed)
        tv.addWidget(self.db_path, 1)
        browse = QPushButton("Browse")
        browse.setCursor(Qt.PointingHandCursor)
        browse.clicked.connect(self.browse_db)
        tv.addWidget(browse)
        rv.addWidget(top)

        self.lbl_db_warning = label("", "warn")
        self.lbl_db_warning.setContentsMargins(24, 8, 24, 0)
        rv.addWidget(self.lbl_db_warning)

        self.pages = QStackedWidget()
        self.page_home = self._page_home()
        self.page_transfer = self._page_transfer()
        self.page_handoff = self._page_handoff()
        self.page_look = self._page_look()
        self.page_history = self._page_history()
        self.page_restore = self._page_restore()
        for p in (
            self.page_home,
            self.page_transfer,
            self.page_handoff,
            self.page_look,
            self.page_history,
            self.page_restore,
        ):
            self.pages.addWidget(p)

        self.nav_group.idClicked.connect(self.pages.setCurrentIndex)
        rv.addWidget(self.pages, 1)
        root.addWidget(nav)
        root.addWidget(right, 1)

    def _wrap(self, inner: QWidget) -> QWidget:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        host = QWidget()
        lay = vbox(host, gap=16, m=(28, 24, 28, 28))
        lay.addWidget(inner)
        lay.addStretch(1)
        scroll.setWidget(host)
        return scroll

    # ── pages ──────────────────────────────────────────────
    def _page_home(self) -> QWidget:
        box = QWidget()
        lay = vbox(box, gap=14, m=0)
        lay.addWidget(label("What would you like to do?", "title"))
        lay.addWidget(
            label(
                "This tool only changes who owns things in a Conan Exiles save. "
                "It does not upload your world. Everything stays on this computer.",
                "subtitle",
            )
        )
        lay.addSpacing(8)

        stories = [
            (
                "Give this world to someone else",
                "Keep the same character, base, and followers. "
                "Retie the save to another person’s Funcom account so they can load it.",
                self.btn_nav_handoff,
            ),
            (
                "Move belongings between two characters",
                "Same save. Give one character the bags, buildings, or followers of another. "
                "Use this when both people already play on this world.",
                self.btn_nav_transfer,
            ),
            (
                "Just look — do not change anything",
                "See who is in the save, which Funcom account they belong to, "
                "and how many items, buildings, and followers they have.",
                self.btn_nav_look,
            ),
            (
                "Undo the last write",
                "Restore the automatic copy made before a transfer or handoff.",
                self.btn_nav_restore,
            ),
        ]
        for title, body, target in stories:
            b = QPushButton()
            b.setObjectName("story")
            b.setCursor(Qt.PointingHandCursor)
            inner = QVBoxLayout(b)
            inner.setContentsMargins(4, 2, 4, 2)
            t = QLabel(title)
            t.setStyleSheet("font-size: 16px; font-weight: 650; background: transparent;")
            d = QLabel(body)
            d.setWordWrap(True)
            d.setStyleSheet("color: palette(mid); background: transparent;")
            d.setObjectName("muted")
            inner.addWidget(t)
            inner.addWidget(d)
            b.clicked.connect(lambda _=False, btn=target: self._go(btn))
            lay.addWidget(b)

        note = label(
            "Before any write: close the dedicated server and the game client. "
            "A running Funcom process will overwrite these edits.",
            "faint",
        )
        lay.addWidget(note)
        return self._wrap(box)

    def _go(self, btn: QPushButton):
        btn.setChecked(True)
        self.pages.setCurrentIndex(self.nav_group.id(btn))

    def _page_transfer(self) -> QWidget:
        box = QWidget()
        lay = vbox(box, gap=14, m=0)
        lay.addWidget(label("Move belongings", "title"))
        lay.addWidget(
            label(
                "Give one character the carried items, buildings, or followers of another "
                "inside this same save.",
                "subtitle",
            )
        )

        who = card()
        g = vbox(who, gap=10, m=18)
        g.addWidget(label("Who", "section"))
        row = hbox(gap=12)
        col_s = vbox(gap=6)
        col_s.addWidget(label("From", "muted"))
        self.src_combo = QComboBox()
        self.src_combo.currentIndexChanged.connect(self.on_source_changed)
        col_s.addWidget(self.src_combo)
        col_t = vbox(gap=6)
        col_t.addWidget(label("To", "muted"))
        self.tgt_combo = QComboBox()
        col_t.addWidget(self.tgt_combo)
        row.addLayout(col_s, 1)
        row.addLayout(col_t, 1)
        g.addLayout(row)
        refresh = QPushButton("Refresh character list")
        refresh.clicked.connect(self.refresh_characters)
        g.addWidget(refresh, 0, Qt.AlignLeft)
        lay.addWidget(who)

        clan = card()
        cg = vbox(clan, gap=8, m=18)
        cg.addWidget(label("Clan property", "section"))
        self.cb_include_clan = QCheckBox(
            "Also move things the clan owns — not just this character"
        )
        self.cb_include_clan.setToolTip(
            "On official servers, placed followers often belong to the clan, not the person. "
            "Other clan members lose those assets if you move them."
        )
        self.cb_include_clan.toggled.connect(self.on_clan_toggled)
        self.cb_clan_to_target_guild = QCheckBox(
            "Keep those things as clan property under the new character’s clan"
        )
        self.cb_clan_to_target_guild.setEnabled(False)
        self.cb_clan_to_target_guild.setToolTip(
            "If off, clan buildings and followers become privately owned by the new character."
        )
        warn = label(
            "Turning this on takes shared clan property away from everyone else in that clan.",
            "warn",
        )
        cg.addWidget(self.cb_include_clan)
        cg.addWidget(self.cb_clan_to_target_guild)
        cg.addWidget(warn)
        lay.addWidget(clan)

        cats = card()
        kg = vbox(cats, gap=10, m=18)
        kg.addWidget(label("What to move", "section"))
        kg.addWidget(
            label(
                "Chests and crafting benches stay with the building. "
                "Only bags, hotbar, and worn gear count as carried items.",
                "muted",
            )
        )

        self.cb_items = QCheckBox("Carried items  (bags, armor, hotbar)")
        self.cb_buildings = QCheckBox("Buildings  (structures — chests move with them)")
        self.cb_thralls = QCheckBox("Followers and pets")
        self.lbl_items_count = label("(0)", "chip")
        self.lbl_buildings_count = label("(0)", "chip")
        self.lbl_thralls_count = label("(0)", "chip")
        self.btn_items_details = QPushButton("Choose which…")
        self.btn_buildings_details = QPushButton("Choose which…")
        self.btn_thralls_details = QPushButton("Choose which…")
        self.btn_items_details.clicked.connect(self.show_items_details)
        self.btn_buildings_details.clicked.connect(self.show_buildings_details)
        self.btn_thralls_details.clicked.connect(self.show_thralls_details)
        self.lbl_item_sel = label("All matching items", "faint")
        self.lbl_bld_sel = label("All matching buildings", "faint")
        self.lbl_thr_sel = label("All matching followers", "faint")

        for cb, chip, btn, sel in (
            (self.cb_items, self.lbl_items_count, self.btn_items_details, self.lbl_item_sel),
            (self.cb_buildings, self.lbl_buildings_count, self.btn_buildings_details, self.lbl_bld_sel),
            (self.cb_thralls, self.lbl_thralls_count, self.btn_thralls_details, self.lbl_thr_sel),
        ):
            row = hbox(gap=10)
            row.addWidget(cb, 1)
            row.addWidget(chip)
            row.addWidget(btn)
            kg.addLayout(row)
            kg.addWidget(sel)
            cb.toggled.connect(self.on_category_toggled)
        lay.addWidget(cats)

        actions = hbox(gap=10)
        self.btn_analyze = QPushButton("Preview — do not write yet")
        self.btn_analyze.clicked.connect(self.on_analyze)
        self.btn_transfer = primary_btn("Write the transfer")
        self.btn_transfer.clicked.connect(self.on_transfer)
        actions.addWidget(self.btn_analyze)
        actions.addWidget(self.btn_transfer)
        actions.addStretch(1)
        lay.addLayout(actions)

        self.table = self._make_table(["What", "In the save now", "Would change"])
        lay.addWidget(self.table)
        return self._wrap(box)

    def _page_handoff(self) -> QWidget:
        box = QWidget()
        lay = vbox(box, gap=14, m=0)
        lay.addWidget(label("Give the world to someone else", "title"))
        lay.addWidget(
            label(
                "The character, base, and followers stay as they are. "
                "Only the Funcom account that may load this save is changed.",
                "subtitle",
            )
        )

        keep = card()
        k = vbox(keep, gap=8, m=18)
        k.addWidget(label("Character to keep", "section"))
        self.handoff_char_combo = QComboBox()
        k.addWidget(self.handoff_char_combo)
        lay.addWidget(keep)

        files = card()
        f = vbox(files, gap=8, m=18)
        f.addWidget(label("Optional Siptah save", "section"))
        row = hbox()
        self.siptah_db_path = QLineEdit()
        self.siptah_db_path.setPlaceholderText("dlc_siptah.db — only if this world uses Siptah")
        row.addWidget(self.siptah_db_path, 1)
        b = QPushButton("Browse")
        b.clicked.connect(self.browse_siptah_db)
        row.addWidget(b)
        f.addLayout(row)
        self.cb_apply_siptah = QCheckBox("Apply the same account change to the Siptah file")
        self.cb_apply_siptah.setChecked(True)
        f.addWidget(self.cb_apply_siptah)
        lay.addWidget(files)

        acct = card()
        a = vbox(acct, gap=8, m=18)
        a.addWidget(label("The person who will own this save", "section"))
        a.addWidget(
            label(
                "They should launch Conan once so Game.ini contains their MasterAccountId. "
                "Typical path: ConanSandbox/Saved/Config/WindowsNoEditor/Game.ini",
                "muted",
            )
        )
        row = hbox()
        self.game_ini_path = QLineEdit()
        self.game_ini_path.setPlaceholderText("Person B’s Game.ini")
        row.addWidget(self.game_ini_path, 1)
        bi = QPushButton("Browse")
        bi.clicked.connect(self.browse_game_ini)
        row.addWidget(bi)
        a.addLayout(row)
        self.target_account_id = QLineEdit()
        self.target_account_id.setPlaceholderText("Master Account ID — filled from Game.ini when possible")
        a.addWidget(self.target_account_id)
        self.cb_remove_throwaway = QCheckBox(
            "Remove extra characters the new person created when they first opened this save"
        )
        self.cb_remove_throwaway.setChecked(True)
        a.addWidget(self.cb_remove_throwaway)
        lay.addWidget(acct)

        self.lbl_handoff_accounts = label("", "muted")
        lay.addWidget(self.lbl_handoff_accounts)

        actions = hbox(gap=10)
        self.btn_handoff_analyze = QPushButton("Preview — do not write yet")
        self.btn_handoff_analyze.clicked.connect(self.on_handoff_analyze)
        self.btn_handoff = primary_btn("Retie this save")
        self.btn_handoff.clicked.connect(self.on_handoff)
        actions.addWidget(self.btn_handoff_analyze)
        actions.addWidget(self.btn_handoff)
        actions.addStretch(1)
        lay.addLayout(actions)

        self.handoff_table = self._make_table(["What", "Plan", ""])
        lay.addWidget(self.handoff_table)
        return self._wrap(box)

    def _page_look(self) -> QWidget:
        box = QWidget()
        lay = vbox(box, gap=14, m=0)
        lay.addWidget(label("Look at the save", "title"))
        lay.addWidget(
            label("Nothing here writes to disk. Refresh after you choose a save file.", "subtitle")
        )
        row = hbox()
        refresh = QPushButton("Refresh")
        refresh.clicked.connect(self.refresh_inspector)
        row.addWidget(refresh)
        row.addStretch(1)
        lay.addLayout(row)
        self.look_chars = self._make_table(
            ["Character", "Id", "Clan", "Items", "Buildings", "Followers"]
        )
        self.look_accounts = self._make_table(["Account id", "Funcom user"])
        lay.addWidget(label("Characters", "section"))
        lay.addWidget(self.look_chars)
        lay.addWidget(label("Accounts", "section"))
        lay.addWidget(self.look_accounts)
        return self._wrap(box)

    def _page_history(self) -> QWidget:
        box = QWidget()
        lay = vbox(box, gap=14, m=0)
        lay.addWidget(label("History", "title"))
        lay.addWidget(
            label("A local diary of writes this app made on this computer.", "subtitle")
        )
        row = hbox()
        refresh = QPushButton("Refresh")
        refresh.clicked.connect(self.reload_history)
        export = QPushButton("Save a copy of the diary")
        export.clicked.connect(self.on_export_audit)
        row.addWidget(refresh)
        row.addWidget(export)
        row.addStretch(1)
        lay.addLayout(row)
        self.history_table = self._make_table(
            ["When", "Kind", "From", "To", "Note"]
        )
        lay.addWidget(self.history_table)
        return self._wrap(box)

    def _page_restore(self) -> QWidget:
        box = QWidget()
        lay = vbox(box, gap=14, m=0)
        lay.addWidget(label("Put it back", "title"))
        lay.addWidget(
            label(
                "Every write leaves a restore copy next to the save, named game.db.pre. "
                "This replaces the current file with that copy.",
                "subtitle",
            )
        )
        c = card()
        g = vbox(c, gap=10, m=18)
        g.addWidget(
            label(
                "The save in the bar at the top is the file that will be restored.",
                "muted",
            )
        )
        self.lbl_restore_hint = label("", "muted")
        g.addWidget(self.lbl_restore_hint)
        row = hbox()
        self.btn_restore_last = primary_btn("Restore the last copy of this save")
        self.btn_restore_last.clicked.connect(self.restore_current)
        pick = QPushButton("Choose a different backup…")
        pick.clicked.connect(self.on_revert_transfer)
        row.addWidget(self.btn_restore_last)
        row.addWidget(pick)
        row.addStretch(1)
        g.addLayout(row)
        lay.addWidget(c)
        return self._wrap(box)

    def _make_table(self, headers: List[str]) -> QTableWidget:
        t = QTableWidget(0, len(headers))
        t.setHorizontalHeaderLabels(headers)
        t.verticalHeader().setVisible(False)
        t.setAlternatingRowColors(True)
        t.setSelectionBehavior(QTableWidget.SelectRows)
        t.setSelectionMode(QTableWidget.SingleSelection)
        t.setShowGrid(False)
        t.verticalHeader().setDefaultSectionSize(32)
        t.horizontalHeader().setStretchLastSection(True)
        t.setMinimumHeight(180)
        return t

    # ── theme ──────────────────────────────────────────────
    def toggle_theme(self):
        self.apply_theme("dark" if self.current_theme == "light" else "light")

    def apply_theme(self, which: str):
        pal = DARK if which == "dark" else LIGHT
        app = QApplication.instance()
        if app:
            app.setStyleSheet(build_stylesheet(pal))
        self.current_theme = which
        self.settings.setValue("theme", which)
        to_dark = which == "light"
        self.btn_theme.setIcon(_make_theme_icon("moon" if to_dark else "sun", pal["accent"]))
        self.btn_theme.setToolTip("Switch to dark theme" if to_dark else "Switch to light theme")
        self.btn_theme.setAccessibleName(self.btn_theme.toolTip())
        # Re-tint muted labels that use object names (stylesheet handles most).
        for lab in self.findChildren(QLabel):
            if lab.objectName() == "muted":
                lab.setStyleSheet(f"color: {pal['muted']}; background: transparent;")
            elif lab.objectName() == "faint":
                lab.setStyleSheet(f"color: {pal['faint']}; background: transparent; font-size: 12px;")
            elif lab.objectName() == "warn":
                lab.setStyleSheet(f"color: {pal['warn']}; background: transparent;")

    # ── file / data ────────────────────────────────────────
    def browse_db(self):
        path, _ = QFileDialog.getOpenFileName(
            self,
            "Choose the world save (game.db)",
            str(Path.cwd()),
            "World save (*.db *.sqlite *.sqlite3);;All files (*)",
        )
        if path:
            self.db_path.setText(path)
            self.on_db_changed()

    def browse_siptah_db(self):
        start = str(Path(self.db_path.text()).parent) if self.db_path.text() else str(Path.cwd())
        path, _ = QFileDialog.getOpenFileName(
            self, "Choose dlc_siptah.db", start, "World save (*.db);;All files (*)"
        )
        if path:
            self.siptah_db_path.setText(path)

    def browse_game_ini(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Choose Person B’s Game.ini", str(Path.home()), "INI (*.ini);;All files (*)"
        )
        if path:
            self.game_ini_path.setText(path)
            acct = db_utils.parse_game_ini_master_account_id(path)
            if acct:
                self.target_account_id.setText(acct)
            else:
                QMessageBox.information(
                    self,
                    "No account id in that file",
                    "Could not find MasterAccountId. Ask them to launch Conan once, "
                    "or paste the id by hand.",
                )

    def on_db_changed(self):
        db = self.db_path.text().strip()
        self._clear_selections()
        self.lbl_db_warning.setText("")
        self._update_restore_hint()
        if not db or not os.path.exists(db):
            return
        warnings = []
        if db_utils.db_appears_in_use(db):
            warnings.append(
                "This save looks live (a lock or leftover write file). "
                "Close the dedicated server and the game before writing."
            )
        try:
            report = db_utils.schema_report(db)
            missing = report.get("missing_expected") or []
            if missing:
                warnings.append("This file is missing expected tables: " + ", ".join(missing))
            if not report.get("has_properties"):
                warnings.append("No properties table — follower transfer will do nothing.")
        except Exception as e:
            warnings.append(f"Could not read this file: {e}")
        parent = Path(db).parent
        siptah = parent / "dlc_siptah.db"
        if siptah.exists() and not self.siptah_db_path.text().strip():
            self.siptah_db_path.setText(str(siptah))
        self.lbl_db_warning.setText("  ".join(warnings))
        self.refresh_characters()
        self.populate_handoff_combo()
        self.update_handoff_accounts_label()
        self.refresh_inspector()

    def refresh_characters(self):
        self._populate_combo(self.src_combo)
        self._populate_combo(self.tgt_combo)
        self._sync_clan_controls(auto_enable_clan=False)
        self.update_category_counts()

    def _populate_combo(self, combo: QComboBox):
        db = self.db_path.text().strip()
        if not db or not os.path.exists(db):
            return
        previous = combo.currentData()
        combo.blockSignals(True)
        combo.clear()
        try:
            chars = db_utils.list_characters(db)
            if not chars:
                combo.addItem("No characters in this save", None)
            for c in chars:
                combo.addItem(_char_label(c), c)
            if previous:
                pid = previous.get("id") if isinstance(previous, dict) else previous
                for i in range(combo.count()):
                    data = combo.itemData(i)
                    if isinstance(data, dict) and data.get("id") == pid:
                        combo.setCurrentIndex(i)
                        break
        except Exception as e:
            QMessageBox.warning(self, "Could not list characters", str(e))
        combo.blockSignals(False)

    def populate_handoff_combo(self):
        self._populate_combo(self.handoff_char_combo)

    def update_handoff_accounts_label(self):
        db = self.db_path.text().strip()
        if not db or not os.path.exists(db):
            self.lbl_handoff_accounts.setText("")
            return
        try:
            accounts = db_utils.list_accounts(db)
            if not accounts:
                self.lbl_handoff_accounts.setText("This save has no account table.")
                return
            self.lbl_handoff_accounts.setText(
                "Accounts already in this save:  " + "   ·   ".join(_account_label(a) for a in accounts)
            )
        except Exception as e:
            self.lbl_handoff_accounts.setText(f"Could not read accounts: {e}")

    def _selected_character(self, combo: QComboBox) -> Optional[dict]:
        data = combo.currentData()
        return data if isinstance(data, dict) else None

    def get_selected_source_id(self):
        c = self._selected_character(self.src_combo)
        return int(c["id"]) if c else None

    def get_selected_target_id(self):
        c = self._selected_character(self.tgt_combo)
        return int(c["id"]) if c else None

    def include_clan(self) -> bool:
        return self.cb_include_clan.isChecked()

    def on_source_changed(self):
        self._clear_selections()
        self._sync_clan_controls(auto_enable_clan=False)
        self.update_category_counts()

    def on_clan_toggled(self):
        self.selected_building_object_ids = None
        self.selected_thrall_ids = None
        self.cb_clan_to_target_guild.setEnabled(self.cb_include_clan.isChecked())
        if not self.cb_include_clan.isChecked():
            self.cb_clan_to_target_guild.setChecked(False)
        self._refresh_subset_labels()
        self.update_category_counts()

    def _sync_clan_controls(self, auto_enable_clan: bool = False):
        src = self._selected_character(self.src_combo)
        has_guild = bool(src and src.get("guild"))
        self.cb_include_clan.setEnabled(has_guild)
        self.cb_include_clan.blockSignals(True)
        if not has_guild:
            self.cb_include_clan.setChecked(False)
            self.cb_clan_to_target_guild.setChecked(False)
        elif auto_enable_clan:
            self.cb_include_clan.setChecked(True)
        self.cb_include_clan.blockSignals(False)
        self.cb_clan_to_target_guild.setEnabled(self.cb_include_clan.isChecked())

    def on_category_toggled(self, _checked: bool = False):
        pass

    def _clear_selections(self):
        self.selected_item_keys = None
        self.selected_building_object_ids = None
        self.selected_thrall_ids = None
        self._refresh_subset_labels()

    def _refresh_subset_labels(self):
        def txt(sel, noun):
            if sel is None:
                return f"All matching {noun} will move"
            if len(sel) == 0:
                return f"None — this category will be skipped"
            return f"{len(sel)} selected {noun}"

        if hasattr(self, "lbl_item_sel"):
            self.lbl_item_sel.setText(txt(self.selected_item_keys, "items"))
            self.lbl_bld_sel.setText(txt(self.selected_building_object_ids, "buildings"))
            self.lbl_thr_sel.setText(txt(self.selected_thrall_ids, "followers"))

    def update_category_counts(self):
        db = self.db_path.text().strip()
        if not db or not os.path.exists(db):
            return
        source_id = self.get_selected_source_id()
        if source_id is None:
            return
        try:
            sim = db_utils.simulate_update_counts(
                db, source_id, ["all"], include_clan_assets=self.include_clan()
            )
            items = sim.get("items", 0)
            blds = sim.get("buildings", 0)
            thralls = sim.get("thralls", 0)
            self.lbl_items_count.setText(f"{items}")
            self.lbl_buildings_count.setText(f"{blds}")
            bits = []
            if sim.get("thralls_following"):
                bits.append(f"{sim['thralls_following']} on the wheel")
            if sim.get("thralls_clan"):
                bits.append(f"{sim['thralls_clan']} clan")
            if sim.get("thralls_personal"):
                bits.append(f"{sim['thralls_personal']} placed")
            extra = f"  ·  {', '.join(bits)}" if bits else ""
            self.lbl_thralls_count.setText(f"{thralls}{extra}")

            def apply_state(count, checkbox, details_btn):
                enabled = bool(count)
                checkbox.setEnabled(enabled)
                if not enabled:
                    checkbox.setChecked(False)
                if details_btn:
                    details_btn.setEnabled(enabled)

            apply_state(items, self.cb_items, self.btn_items_details)
            apply_state(blds, self.cb_buildings, self.btn_buildings_details)
            apply_state(thralls, self.cb_thralls, self.btn_thralls_details)
        except Exception:
            pass

    def _selected_categories(self) -> List[str]:
        cats = []
        if self.cb_items.isChecked():
            cats.append("items")
        if self.cb_buildings.isChecked():
            cats.append("buildings")
        if self.cb_thralls.isChecked():
            cats.append("thralls")
        return cats

    def _load_xref(self):
        candidate = Path(__file__).resolve().parents[1] / "item_xref"
        if candidate.exists():
            return db_utils.load_item_xref_file(str(candidate))
        return {}

    def _require_db_and_source(self):
        db = self.db_path.text().strip()
        if not db or not os.path.exists(db):
            QMessageBox.information(self, "Choose a save", "Pick a game.db file in the bar at the top.")
            return None, None
        source_id = self.get_selected_source_id()
        if source_id is None:
            QMessageBox.information(self, "Choose a character", "Select who the belongings come from.")
            return None, None
        return db, source_id

    def _confirm_db_not_live(self, db: str) -> bool:
        if not db_utils.db_appears_in_use(db):
            return True
        warn = QMessageBox(self)
        warn.setIcon(QMessageBox.Warning)
        warn.setWindowTitle("This save may still be open")
        warn.setText(
            "Close the Conan Exiles dedicated server and the game first.\n\n"
            "If a Funcom process is still running, it will overwrite these edits."
        )
        warn.setInformativeText("I have closed the server and the game.")
        warn.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        return warn.exec() == QMessageBox.Ok

    # ── details dialogs ────────────────────────────────────
    def _show_selection_dialog(self, rows, columns, title):
        dlg = QDialog(self)
        dlg.setWindowTitle(title)
        dlg.setMinimumSize(840, 460)
        v = vbox(dlg, gap=10, m=16)
        hint = label(
            "Checked rows move. Confirm with nothing checked to skip this category. "
            "Cancel leaves the previous choice (or everything, if you never chose).",
            "muted",
        )
        v.addWidget(hint)
        tbl = QTableWidget(0, 1 + len(columns))
        tbl.setHorizontalHeaderLabels(["Move"] + [c[0] for c in columns])
        tbl.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        tbl.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        tbl.verticalHeader().setVisible(False)
        tbl.setAlternatingRowColors(True)
        for r in rows:
            i = tbl.rowCount()
            tbl.insertRow(i)
            chk = QTableWidgetItem("")
            chk.setFlags(chk.flags() | Qt.ItemIsUserCheckable)
            chk.setCheckState(Qt.Unchecked)
            tbl.setItem(i, 0, chk)
            for col_i, (_header, key) in enumerate(columns, start=1):
                val = r.get(key)
                item = QTableWidgetItem("" if val is None else str(val))
                if col_i == 1:
                    item.setData(Qt.UserRole, r)
                tbl.setItem(i, col_i, item)
        v.addWidget(tbl)
        btn_row = hbox()
        btn_all = QPushButton("Check all")
        btn_none = QPushButton("Check none")
        btn_all.clicked.connect(lambda: self._set_all_checks(tbl, True))
        btn_none.clicked.connect(lambda: self._set_all_checks(tbl, False))
        btn_row.addWidget(btn_all)
        btn_row.addWidget(btn_none)
        btn_row.addStretch(1)
        v.addLayout(btn_row)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("Use this list")
        buttons.button(QDialogButtonBox.Cancel).setText("Cancel")
        v.addWidget(buttons)
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        if dlg.exec() != QDialog.Accepted:
            return None
        selected = []
        for r in range(tbl.rowCount()):
            it = tbl.item(r, 0)
            id_item = tbl.item(r, 1)
            if it and id_item and it.checkState() == Qt.Checked:
                payload = id_item.data(Qt.UserRole)
                selected.append(payload if isinstance(payload, dict) else None)
        return [p for p in selected if p is not None]

    @staticmethod
    def _set_all_checks(tbl: QTableWidget, checked: bool):
        state = Qt.Checked if checked else Qt.Unchecked
        for r in range(tbl.rowCount()):
            it = tbl.item(r, 0)
            if it:
                it.setCheckState(state)

    def show_items_details(self):
        db, source_id = self._require_db_and_source()
        if source_id is None:
            return
        rows = db_utils.list_items_for_owner(db, source_id, self._load_xref())
        if not rows:
            QMessageBox.information(self, "No carried items", "Nothing in bags, armor, or hotbar.")
            return
        picked = self._show_selection_dialog(
            rows,
            [
                ("Slot", "item_id"),
                ("Where", "inv_label"),
                ("Name", "template_name"),
                ("Template", "template_id"),
            ],
            "Choose carried items",
        )
        if picked is None:
            return
        self.selected_item_keys = [
            (int(r["item_id"]), r.get("inv_type")) for r in picked if r.get("item_id") is not None
        ]
        self._refresh_subset_labels()

    def show_buildings_details(self):
        db, source_id = self._require_db_and_source()
        if source_id is None:
            return
        rows = db_utils.list_buildings_for_owner(
            db, source_id, self._load_xref(), include_clan_assets=self.include_clan()
        )
        if not rows:
            QMessageBox.information(self, "No buildings", "No structures found for this person.")
            return
        for r in rows:
            r["kind"] = "clan" if r.get("owned_by_guild") else "personal"
            r["info"] = r.get("class") or ""
        picked = self._show_selection_dialog(
            rows,
            [
                ("Object", "object_id"),
                ("Kind", "kind"),
                ("Name", "template_name"),
                ("Class", "info"),
            ],
            "Choose buildings",
        )
        if picked is None:
            return
        self.selected_building_object_ids = [int(r["object_id"]) for r in picked]
        self._refresh_subset_labels()

    def show_thralls_details(self):
        db, source_id = self._require_db_and_source()
        if source_id is None:
            return
        rows = db_utils.list_thralls_for_owner(
            db, source_id, include_clan_assets=self.include_clan()
        )
        if not rows:
            QMessageBox.information(
                self,
                "No followers",
                "None on the follower wheel and none placed in the world for this person.",
            )
            return
        for r in rows:
            r["kind"] = r.get("kind") or ("clan" if r.get("owned_by_guild") else "placed")
        picked = self._show_selection_dialog(
            rows,
            [
                ("Actor", "follower_id"),
                ("Kind", "kind"),
                ("Class", "class"),
                ("Where", "coords"),
            ],
            "Choose followers",
        )
        if picked is None:
            return
        self.selected_thrall_ids = [int(r["follower_id"]) for r in picked]
        self._refresh_subset_labels()

    # ── transfer actions ───────────────────────────────────
    def _fill_results_table(self, before: dict, transferred: dict):
        rows = [
            ("Carried items", "item_inventory"),
            ("Item details", "item_properties"),
            ("Buildings (personal)", "buildings_personal"),
            ("Buildings (clan)", "buildings_clan"),
            ("Buildings (all)", "buildings"),
            ("Followers (personal)", "thralls_personal"),
            ("Followers (clan)", "thralls_clan"),
            ("Followers (all)", "thralls"),
        ]
        self.table.setRowCount(0)
        for label_s, key in rows:
            b = before.get(key, 0)
            t = transferred.get(key, 0)
            if b == 0 and t == 0 and key not in ("item_inventory", "buildings", "thralls"):
                continue
            i = self.table.rowCount()
            self.table.insertRow(i)
            self.table.setItem(i, 0, QTableWidgetItem(label_s))
            self.table.setItem(i, 1, QTableWidgetItem(str(b)))
            self.table.setItem(i, 2, QTableWidgetItem(str(t)))

    def on_analyze(self):
        db, source_id = self._require_db_and_source()
        if source_id is None:
            return
        cats = self._selected_categories()
        if not cats:
            QMessageBox.information(self, "Pick something to move", "Tick at least one category.")
            return
        sim = db_utils.simulate_update_counts(
            db, source_id, cats, include_clan_assets=self.include_clan()
        )
        zeros = {k: 0 for k in sim}
        self._fill_results_table(sim, zeros)
        QMessageBox.information(
            self,
            "Preview ready",
            "Nothing was written. The table shows what exists now. "
            "Write the transfer only when this looks right.",
        )

    def show_pretransfer_summary(self, counts, selected_items, selected_buildings, selected_thralls) -> bool:
        dlg = QDialog(self)
        dlg.setWindowTitle("Please confirm")
        dlg.setMinimumSize(560, 400)
        v = vbox(dlg, gap=10, m=18)
        v.addWidget(label("This will be written to disk", "title"))
        tbl = QTableWidget(0, 2)
        tbl.setHorizontalHeaderLabels(["What", "How many"])
        tbl.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        tbl.verticalHeader().setVisible(False)
        names = {
            "item_inventory": "Carried items",
            "item_properties": "Item details",
            "buildings_personal": "Personal buildings",
            "buildings_clan": "Clan buildings",
            "buildings": "Buildings total",
            "thralls_personal": "Personal followers",
            "thralls_clan": "Clan followers",
            "thralls": "Followers total",
        }
        for k, pretty in names.items():
            i = tbl.rowCount()
            tbl.insertRow(i)
            tbl.setItem(i, 0, QTableWidgetItem(pretty))
            tbl.setItem(i, 1, QTableWidgetItem(str(counts.get(k, 0))))
        v.addWidget(tbl)

        def subset_text(sel, noun):
            if sel is None:
                return f"all matching {noun}"
            return f"{len(sel)} selected {noun}"

        v.addWidget(
            label(
                f"Subset: {subset_text(selected_items, 'items')}, "
                f"{subset_text(selected_buildings, 'buildings')}, "
                f"{subset_text(selected_thralls, 'followers')}.",
                "muted",
            )
        )
        if self.include_clan():
            v.addWidget(
                label(
                    "Clan include is on. Shared clan buildings and followers will move "
                    "unless you narrowed the list.",
                    "warn",
                )
            )
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("Write it")
        buttons.button(QDialogButtonBox.Cancel).setText("Not yet")
        v.addWidget(buttons)
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        return dlg.exec() == QDialog.Accepted

    def on_transfer(self):
        db, source_id = self._require_db_and_source()
        if source_id is None:
            return
        target_id = self.get_selected_target_id()
        if target_id is None:
            QMessageBox.information(self, "Choose who receives them", "Select the character on the right.")
            return
        if source_id == target_id:
            QMessageBox.information(self, "Need two people", "From and To must be different characters.")
            return
        cats = self._selected_categories()
        if not cats:
            QMessageBox.information(self, "Pick something to move", "Tick at least one category.")
            return
        if not self._confirm_db_not_live(db):
            return
        try:
            pre_path = db_utils.create_pre_backup(db)
        except Exception as e:
            QMessageBox.critical(self, "Could not make a restore copy", str(e))
            return
        stamped = db + f".bak_{int(time.time())}"
        try:
            shutil.copy2(pre_path, stamped)
        except Exception:
            stamped = pre_path

        sim = db_utils.simulate_update_counts(
            db, source_id, cats, include_clan_assets=self.include_clan()
        )
        sel_items = self.selected_item_keys
        sel_buildings = self.selected_building_object_ids
        sel_thralls = self.selected_thrall_ids
        if not self.show_pretransfer_summary(sim, sel_items, sel_buildings, sel_thralls):
            return

        include_clan = self.include_clan()
        to_guild = include_clan and self.cb_clan_to_target_guild.isChecked()
        before_source = db_utils.counts_for_owner(db, source_id, include_clan)
        before_target = db_utils.counts_for_owner(db, target_id, include_clan)
        success, changed, msg = db_utils.perform_transfer(
            db,
            source_id,
            target_id,
            cats,
            dry_run=False,
            item_keys=sel_items,
            building_object_ids=sel_buildings,
            thrall_ids=sel_thralls,
            include_clan_assets=include_clan,
            clan_assets_to_target_guild=to_guild,
            pre_backup_path=pre_path,
        )
        after_source = db_utils.counts_for_owner(db, source_id, include_clan)
        after_target = db_utils.counts_for_owner(db, target_id, include_clan)
        if not success:
            QMessageBox.critical(self, "The write did not finish", msg)
            return

        self._fill_results_table(sim, changed)
        QMessageBox.information(
            self,
            "Transfer finished",
            f"The save was updated.\n\nRestore copy: {pre_path}\nExtra copy: {stamped}",
        )
        self._clear_selections()
        self.update_category_counts()
        self._update_restore_hint()
        self.refresh_inspector()

        record = {
            "timestamp": int(time.time()),
            "db_path": str(db),
            "pre_transfer_backup": pre_path,
            "source_id": source_id,
            "target_id": target_id,
            "categories": cats,
            "item_ids": sel_items or [],
            "building_object_ids": sel_buildings or [],
            "thrall_ids": sel_thralls or [],
            "changed_json": changed,
            "message": msg,
            "before_source": before_source,
            "after_source": after_source,
            "before_target": before_target,
            "after_target": after_target,
            "include_clan_assets": include_clan,
            "clan_assets_to_target_guild": to_guild,
        }
        try:
            db_utils.write_audit_csv(str(APP_DIR / "transfers_audit.csv"), record)
        except Exception as e:
            db_utils._log(f"Audit log write failed: {e}")
        self.reload_history()

    # ── handoff ────────────────────────────────────────────
    def _selected_handoff_char_id(self) -> Optional[int]:
        c = self._selected_character(self.handoff_char_combo)
        return int(c["id"]) if c else None

    def _handoff_db_paths(self) -> List[str]:
        paths = [self.db_path.text().strip()]
        siptah = self.siptah_db_path.text().strip()
        if self.cb_apply_siptah.isChecked() and siptah and os.path.isfile(siptah):
            paths.append(siptah)
        return paths

    def _require_handoff_inputs(self):
        db = self.db_path.text().strip()
        if not db or not os.path.exists(db):
            QMessageBox.information(self, "Choose a save", "Pick a game.db file in the bar at the top.")
            return None
        char_id = self._selected_handoff_char_id()
        if char_id is None:
            QMessageBox.information(self, "Choose a character", "Select the character to keep.")
            return None
        target = self.target_account_id.text().strip()
        if not target:
            QMessageBox.information(
                self,
                "Need the new person’s account",
                "Browse their Game.ini or paste their Master Account ID.",
            )
            return None
        return db, char_id, target

    def _fill_handoff_results_table(self, sim: dict):
        self.handoff_table.setRowCount(0)
        rows = [
            ("Account now", sim.get("source_account_user_before", "")),
            ("Account after", sim.get("target_account_user_after", "")),
            ("Rewrite account name", "yes" if sim.get("will_rebind_account_user") else "no"),
            ("Point the character at an existing account", "yes" if sim.get("will_repoint_player_id") else "no"),
            (
                "Extra characters to remove",
                ", ".join(str(x) for x in sim.get("characters_to_remove", [])) or "none",
            ),
        ]
        assets = sim.get("asset_counts") or {}
        for key, pretty in (("items", "Carried items"), ("buildings", "Buildings"), ("thralls", "Followers")):
            rows.append((f"{pretty} (unchanged)", str(assets.get(key, 0))))
        for lab, val in rows:
            i = self.handoff_table.rowCount()
            self.handoff_table.insertRow(i)
            self.handoff_table.setItem(i, 0, QTableWidgetItem(lab))
            self.handoff_table.setItem(i, 1, QTableWidgetItem(str(val)))
            self.handoff_table.setItem(i, 2, QTableWidgetItem(""))

    def show_handoff_summary(self, sim: dict) -> bool:
        dlg = QDialog(self)
        dlg.setWindowTitle("Please confirm")
        dlg.setMinimumSize(560, 420)
        v = vbox(dlg, gap=10, m=18)
        v.addWidget(label("The world stays. Only the account changes.", "title"))
        tbl = QTableWidget(0, 2)
        tbl.setHorizontalHeaderLabels(["What", "Plan"])
        tbl.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        tbl.verticalHeader().setVisible(False)
        fields = [
            ("Character to keep", sim.get("source_char_id")),
            ("Account now", sim.get("source_account_user_before")),
            ("Account after", sim.get("target_account_user_after")),
            ("Rewrite account name", sim.get("will_rebind_account_user")),
            ("Point at existing account", sim.get("will_repoint_player_id")),
            ("Remove extra characters", sim.get("characters_to_remove")),
        ]
        assets = sim.get("asset_counts") or {}
        fields.extend(
            [
                ("Items stay put", assets.get("items", 0)),
                ("Buildings stay put", assets.get("buildings", 0)),
                ("Followers stay put", assets.get("thralls", 0)),
            ]
        )
        for k, val in fields:
            i = tbl.rowCount()
            tbl.insertRow(i)
            tbl.setItem(i, 0, QTableWidgetItem(str(k)))
            tbl.setItem(i, 1, QTableWidgetItem(str(val)))
        v.addWidget(tbl)
        dbs = self._handoff_db_paths()
        if len(dbs) > 1:
            v.addWidget(label("Also applied to: " + ", ".join(Path(p).name for p in dbs), "muted"))
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.button(QDialogButtonBox.Ok).setText("Retie the save")
        buttons.button(QDialogButtonBox.Cancel).setText("Not yet")
        v.addWidget(buttons)
        buttons.accepted.connect(dlg.accept)
        buttons.rejected.connect(dlg.reject)
        return dlg.exec() == QDialog.Accepted

    def on_handoff_analyze(self):
        req = self._require_handoff_inputs()
        if not req:
            return
        db, char_id, target = req
        sim = db_utils.simulate_save_handoff(
            db,
            char_id,
            target,
            remove_character_ids=None if self.cb_remove_throwaway.isChecked() else [],
        )
        if sim.get("errors"):
            QMessageBox.critical(self, "Could not plan the handoff", "\n".join(sim["errors"]))
            return
        self._fill_handoff_results_table(sim)
        QMessageBox.information(
            self,
            "Preview ready",
            "Nothing was written. Belongings stay on this character. "
            "Only the Funcom account linkage would change.",
        )

    def on_handoff(self):
        req = self._require_handoff_inputs()
        if not req:
            return
        db, char_id, target = req
        paths = self._handoff_db_paths()
        if not self._confirm_db_not_live(db):
            return
        sim = db_utils.simulate_save_handoff(
            db,
            char_id,
            target,
            remove_character_ids=None if self.cb_remove_throwaway.isChecked() else [],
        )
        if sim.get("errors"):
            QMessageBox.critical(self, "Could not plan the handoff", "\n".join(sim["errors"]))
            return
        if not self.show_handoff_summary(sim):
            return

        if len(paths) == 1:
            try:
                pre_path = db_utils.create_pre_backup(db)
            except Exception as e:
                QMessageBox.critical(self, "Could not make a restore copy", str(e))
                return
            stamped = db + f".bak_{int(time.time())}"
            try:
                shutil.copy2(pre_path, stamped)
            except Exception:
                stamped = pre_path
            ok, changed, msg = db_utils.perform_save_handoff(
                db,
                char_id,
                target,
                remove_character_ids=None if self.cb_remove_throwaway.isChecked() else [],
                pre_backup_path=pre_path,
            )
        else:
            ok, changed, msg = db_utils.perform_save_handoff_multi(
                paths,
                char_id,
                target,
                remove_character_ids=None if self.cb_remove_throwaway.isChecked() else [],
            )
            pre_path = (changed.get("databases") or {}).get(db, {}).get("backup", db + ".pre")
            stamped = pre_path

        if not ok:
            QMessageBox.critical(self, "The write did not finish", msg)
            return

        self._fill_handoff_results_table(sim)
        self.update_handoff_accounts_label()
        self.refresh_characters()
        self.populate_handoff_combo()
        self.refresh_inspector()
        self._update_restore_hint()
        QMessageBox.information(
            self,
            "The save is now tied to the new account",
            f"Restore copy: {pre_path}\nExtra copy: {stamped}",
        )
        record = {
            "timestamp": int(time.time()),
            "operation": "save_handoff",
            "db_paths": paths,
            "pre_transfer_backup": pre_path,
            "source_char_id": char_id,
            "target_account_user": target,
            "remove_character_ids": sim.get("characters_to_remove", []),
            "changed": changed,
            "simulation": sim,
            "message": msg,
        }
        try:
            db_utils.write_handoff_audit_csv(str(APP_DIR / "transfers_audit.csv"), record)
        except Exception as e:
            db_utils._log(f"Handoff audit write failed: {e}")
        self.reload_history()

    # ── inspect / history / restore ────────────────────────
    def refresh_inspector(self):
        db = self.db_path.text().strip()
        self.look_chars.setRowCount(0)
        self.look_accounts.setRowCount(0)
        if not db or not os.path.exists(db):
            return
        try:
            chars = db_utils.list_characters(db)
            for c in chars:
                counts = db_utils.counts_for_owner(db, c["id"], include_clan_assets=bool(c.get("guild")))
                i = self.look_chars.rowCount()
                self.look_chars.insertRow(i)
                vals = [
                    c.get("char_name") or "",
                    c.get("id"),
                    c.get("guild_name") or "—",
                    counts.get("items", 0),
                    counts.get("buildings", 0),
                    counts.get("thralls", 0),
                ]
                for col, val in enumerate(vals):
                    self.look_chars.setItem(i, col, QTableWidgetItem(str(val)))
        except Exception:
            pass
        try:
            for a in db_utils.list_accounts(db):
                i = self.look_accounts.rowCount()
                self.look_accounts.insertRow(i)
                self.look_accounts.setItem(i, 0, QTableWidgetItem(str(a.get("id"))))
                self.look_accounts.setItem(i, 1, QTableWidgetItem(str(a.get("user") or "")))
        except Exception:
            pass

    def _load_audit_records(self):
        audit = APP_DIR / "transfers_audit.csv"
        if not audit.exists():
            return []
        recs = []
        try:
            with open(audit, "r", encoding="utf-8") as f:
                for r in csv.DictReader(f):
                    recs.append(r)
        except Exception:
            return []
        return recs

    def reload_history(self):
        self.history_table.setRowCount(0)
        for r in self._load_audit_records():
            i = self.history_table.rowCount()
            self.history_table.insertRow(i)
            ts = r.get("timestamp", "")
            try:
                when = time.strftime("%Y-%m-%d %H:%M", time.localtime(int(ts)))
            except Exception:
                when = str(ts)
            kind = r.get("operation") or "transfer"
            src = r.get("source_id") or r.get("source_char_id") or ""
            tgt = r.get("target_id") or r.get("target_account_user") or ""
            note = r.get("message") or ""
            for col, val in enumerate((when, kind, src, tgt, note)):
                self.history_table.setItem(i, col, QTableWidgetItem(str(val)))

    def on_export_audit(self):
        audit = APP_DIR / "transfers_audit.csv"
        if not audit.exists():
            QMessageBox.information(self, "Nothing to export", "No diary has been written yet.")
            return
        path, _ = QFileDialog.getSaveFileName(
            self, "Save a copy of the diary", str(Path.home() / "world-transfer-diary.csv"), "CSV (*.csv)"
        )
        if not path:
            return
        try:
            shutil.copy2(str(audit), path)
            QMessageBox.information(self, "Saved", f"Copied to {path}")
        except Exception as e:
            QMessageBox.critical(self, "Could not copy", str(e))

    def _update_restore_hint(self):
        db = self.db_path.text().strip()
        if not db:
            self.lbl_restore_hint.setText("Choose a save in the bar at the top.")
            return
        pre = db + ".pre"
        if os.path.exists(pre):
            self.lbl_restore_hint.setText(f"A restore copy is ready:\n{pre}")
        else:
            self.lbl_restore_hint.setText(
                "No automatic restore copy sits next to this file yet. "
                "One is created the first time this app writes."
            )

    def restore_current(self):
        db = self.db_path.text().strip()
        if not db or not os.path.exists(db):
            QMessageBox.information(self, "Choose a save", "Pick the file to restore in the bar at the top.")
            return
        backup = db_utils.find_pre_backup(db)
        if not backup:
            QMessageBox.information(
                self,
                "No automatic copy",
                "There is no game.db.pre next to this file. Use “Choose a different backup”.",
            )
            return
        ok = QMessageBox.question(
            self,
            "Restore this save?",
            f"Replace\n{db}\n\nwith\n{backup}",
        )
        if ok != QMessageBox.StandardButton.Yes:
            return
        success, msg = db_utils.revert_transfer(db, backup)
        if success:
            QMessageBox.information(self, "Restored", msg)
            self.on_db_changed()
        else:
            QMessageBox.critical(self, "Could not restore", msg)

    def on_revert_transfer(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Choose the save to restore", str(APP_DIR), "Saves (*.db);;All files (*)"
        )
        if not path:
            return
        backup = db_utils.find_pre_backup(path)
        if not backup:
            backup, _ = QFileDialog.getOpenFileName(
                self,
                "Choose the restore copy",
                str(Path(path).parent),
                "Copies (*.pre *.db);;All files (*)",
            )
            if not backup:
                return
        ok = QMessageBox.question(self, "Restore this save?", f"Replace\n{path}\n\nwith\n{backup}")
        if ok != QMessageBox.StandardButton.Yes:
            return
        success, msg = db_utils.revert_transfer(path, backup)
        if success:
            QMessageBox.information(self, "Restored", msg)
            if path == self.db_path.text().strip():
                self.on_db_changed()
        else:
            QMessageBox.critical(self, "Could not restore", msg)


def _make_theme_icon(kind: str, color: str) -> QIcon:
    pm = QPixmap(64, 64)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    col = QColor(color)
    p.translate(32, 32)
    if kind == "moon":
        p.setPen(Qt.NoPen)
        p.setBrush(col)
        p.drawEllipse(-14, -16, 36, 36)
        p.setCompositionMode(QPainter.CompositionMode_Clear)
        p.drawEllipse(-2, -22, 36, 36)
    else:
        p.setPen(Qt.NoPen)
        p.setBrush(col)
        p.drawEllipse(-10, -10, 20, 20)
        p.setPen(QPen(col, 3.5, Qt.SolidLine, Qt.RoundCap))
        for _ in range(8):
            p.drawLine(0, -16, 0, -24)
            p.rotate(45)
    p.end()
    return QIcon(pm)


def _make_app_icon() -> QIcon:
    pm = QPixmap(64, 64)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setBrush(QColor("#9a4a16"))
    p.setPen(Qt.NoPen)
    p.drawRoundedRect(4, 4, 56, 56, 16, 16)
    p.setPen(QColor("#fffaf2"))
    font = QFont("Segoe UI", 22, QFont.Bold)
    p.setFont(font)
    p.drawText(pm.rect(), Qt.AlignCenter, "W")
    p.end()
    return QIcon(pm)


if __name__ == "__main__":
    if sys.platform == "win32":
        try:
            import ctypes

            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
                "conanexiles.worldtransfer.tool"
            )
        except Exception:
            pass

    app = QApplication(sys.argv)
    app.setApplicationName("Conan World Transfer")
    ico = _make_app_icon()
    if ICON_PATH.exists():
        file_ico = QIcon(str(ICON_PATH))
        if not file_ico.isNull():
            ico = file_ico
    app.setWindowIcon(ico)
    w = TransferApp()
    w.setWindowIcon(ico)
    w.show()
    sys.exit(app.exec())
