#!/usr/bin/env python3
"""
AJ Tech Downloader
------------------
A clean, free, no-key video & audio downloader for any platform supported by
yt-dlp (YouTube, TikTok, Instagram, Facebook, Douyin, and 1000+ sites).

Single videos, audio-only MP3, full playlists, and concurrent downloads.
No activation. No license key. No account required.

Built by AJ Tech.
"""

import os
import sys
import threading
import queue
import tkinter as tk
from tkinter import filedialog, messagebox

import customtkinter as ctk
import yt_dlp

APP_NAME = "AJ Tech Downloader"

# ---------------------------------------------------------------------------
# Resource / ffmpeg helpers
# ---------------------------------------------------------------------------
def resource_base():
    if getattr(sys, "frozen", False):
        return getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    return os.path.dirname(os.path.abspath(__file__))


def asset(name):
    return os.path.join(resource_base(), name)


def find_ffmpeg_dir():
    base = resource_base()
    exe = "ffmpeg.exe" if os.name == "nt" else "ffmpeg"
    for folder in (base, os.path.join(base, "ffmpeg"), os.path.join(base, "bin")):
        if os.path.isfile(os.path.join(folder, exe)):
            return folder
    return None


def default_download_dir():
    home = os.path.expanduser("~")
    dl = os.path.join(home, "Downloads")
    return dl if os.path.isdir(dl) else home


QUALITY_PRESETS = {
    "Best (up to 4K)":  "bestvideo*+bestaudio/best",
    "1080p":            "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
    "720p":             "bestvideo[height<=720]+bestaudio/best[height<=720]",
    "480p":             "bestvideo[height<=480]+bestaudio/best[height<=480]",
    "Audio only (MP3)": "bestaudio/best",
}

PLATFORMS = ["YouTube", "TikTok", "Instagram", "Facebook", "Douyin", "Many More"]

GREEN = "#1faa59"
GREEN_DARK = "#0f7a3d"


class StopRequested(Exception):
    pass


# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("green")

        self.title(APP_NAME)
        self.geometry("980x620")
        self.minsize(900, 580)

        # window icon
        try:
            ico = asset("panda_icon.ico")
            if os.path.isfile(ico):
                self.iconbitmap(ico)
        except Exception:
            pass

        # state
        self.msg_queue = queue.Queue()
        self.stop_event = threading.Event()
        self.is_downloading = False
        self.ffmpeg_dir = find_ffmpeg_dir()
        self.folder_var = tk.StringVar(value=default_download_dir())
        self.quality_var = tk.StringVar(value="Best (up to 4K)")
        self.concurrent = 3
        self.counts = {"done": 0, "active": 0, "failed": 0, "total": 0}
        self._logo_img = None

        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._build_sidebar()
        self._build_main()
        self._show_page("download")

        self.after(120, self._drain_queue)

    # ---- sidebar ----------------------------------------------------------
    def _build_sidebar(self):
        side = ctk.CTkFrame(self, width=220, corner_radius=0)
        side.grid(row=0, column=0, sticky="nsew")
        side.grid_rowconfigure(6, weight=1)

        # logo + title
        head = ctk.CTkFrame(side, fg_color="transparent")
        head.grid(row=0, column=0, padx=16, pady=(20, 24), sticky="w")
        try:
            from PIL import Image
            logo_path = asset("panda_logo.png")
            if os.path.isfile(logo_path):
                self._logo_img = ctk.CTkImage(Image.open(logo_path), size=(40, 40))
                ctk.CTkLabel(head, image=self._logo_img, text="").grid(row=0, column=0, padx=(0, 10))
        except Exception:
            pass
        ctk.CTkLabel(head, text="AJ Tech", font=ctk.CTkFont(size=18, weight="bold")
                     ).grid(row=0, column=1, sticky="w")

        self.nav_buttons = {}
        items = [("dashboard", "  Dashboard"), ("download", "  Download"),
                 ("activity", "  Activity Log"), ("settings", "  Settings")]
        for i, (key, label) in enumerate(items, start=1):
            b = ctk.CTkButton(side, text=label, anchor="w", height=42,
                              fg_color="transparent", text_color=("gray10", "gray90"),
                              hover_color=("gray80", "gray25"),
                              command=lambda k=key: self._show_page(k))
            b.grid(row=i, column=0, padx=12, pady=4, sticky="ew")
            self.nav_buttons[key] = b

        # theme toggle
        self.theme_switch = ctk.CTkSwitch(side, text="Dark Theme",
                                          command=self._toggle_theme)
        self.theme_switch.grid(row=7, column=0, padx=20, pady=20, sticky="w")

    def _toggle_theme(self):
        ctk.set_appearance_mode("dark" if self.theme_switch.get() else "light")

    def _show_page(self, key):
        for k, b in self.nav_buttons.items():
            b.configure(fg_color=GREEN if k == key else "transparent",
                        text_color=("white" if k == key else ("gray10", "gray90")))
        for k, frame in self.pages.items():
            frame.grid_remove()
        self.pages[key].grid(row=0, column=0, sticky="nsew")

    # ---- main area --------------------------------------------------------
    def _build_main(self):
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.grid(row=0, column=1, sticky="nsew", padx=24, pady=20)
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self.pages = {
            "download": self._page_download(container),
            "activity": self._page_activity(container),
            "settings": self._page_settings(container),
            "dashboard": self._page_dashboard(container),
        }

    # ---- download page ----------------------------------------------------
    def _page_download(self, parent):
        page = ctk.CTkFrame(parent, fg_color="transparent")
        page.grid_columnconfigure(0, weight=1)

        top = ctk.CTkFrame(page, fg_color="transparent")
        top.grid(row=0, column=0, sticky="ew")
        top.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(top, text="Downloads", font=ctk.CTkFont(size=26, weight="bold")
                     ).grid(row=0, column=0, sticky="w")
        self.counter_label = ctk.CTkLabel(top, text=self._counter_text(),
                                          font=ctk.CTkFont(size=13))
        self.counter_label.grid(row=0, column=1, sticky="e")

        # platform chips
        chips = ctk.CTkFrame(page, fg_color="transparent")
        chips.grid(row=1, column=0, sticky="w", pady=(12, 6))
        for i, p in enumerate(PLATFORMS):
            ctk.CTkLabel(chips, text=p, fg_color=("gray85", "gray25"),
                         corner_radius=14, padx=12, pady=4,
                         font=ctk.CTkFont(size=12)).grid(row=0, column=i, padx=4)

        # paste box
        ctk.CTkLabel(page, text="Paste links here, one per line...",
                     text_color=("gray40", "gray60")).grid(row=2, column=0, sticky="w", pady=(10, 2))
        self.url_box = ctk.CTkTextbox(page, height=170, font=ctk.CTkFont(family="Consolas", size=13))
        self.url_box.grid(row=3, column=0, sticky="ew")
        self.url_box.bind("<KeyRelease>", lambda e: self._update_link_count())

        row4 = ctk.CTkFrame(page, fg_color="transparent")
        row4.grid(row=4, column=0, sticky="ew", pady=(4, 0))
        row4.grid_columnconfigure(0, weight=1)
        self.link_count_label = ctk.CTkLabel(row4, text="0 links detected",
                                             text_color=("gray40", "gray60"))
        self.link_count_label.grid(row=0, column=0, sticky="w")
        ctk.CTkButton(row4, text="Clear Input", width=110, fg_color="transparent",
                      border_width=1, text_color=("gray10", "gray90"),
                      command=self._clear_input).grid(row=0, column=1, sticky="e")

        # controls
        ctrl = ctk.CTkFrame(page)
        ctrl.grid(row=5, column=0, sticky="ew", pady=(14, 0))
        ctrl.grid_columnconfigure(3, weight=1)

        ctk.CTkLabel(ctrl, text="Quality").grid(row=0, column=0, padx=(14, 6), pady=14)
        ctk.CTkOptionMenu(ctrl, variable=self.quality_var,
                          values=list(QUALITY_PRESETS.keys()), width=170
                          ).grid(row=0, column=1, pady=14)

        ctk.CTkLabel(ctrl, text="Concurrent").grid(row=0, column=2, padx=(20, 6))
        spin = ctk.CTkFrame(ctrl, fg_color="transparent")
        spin.grid(row=0, column=3, sticky="w")
        ctk.CTkButton(spin, text="-", width=30, command=lambda: self._bump_conc(-1)).grid(row=0, column=0)
        self.conc_value = ctk.CTkLabel(spin, text="3", width=30)
        self.conc_value.grid(row=0, column=1, padx=6)
        ctk.CTkButton(spin, text="+", width=30, command=lambda: self._bump_conc(1)).grid(row=0, column=2)

        self.stop_btn = ctk.CTkButton(ctrl, text="Stop", width=90, fg_color="gray50",
                                      hover_color="gray40", command=self._stop, state="disabled")
        self.stop_btn.grid(row=0, column=4, padx=(10, 6), pady=14)
        self.start_btn = ctk.CTkButton(ctrl, text="START DOWNLOAD", width=180,
                                       font=ctk.CTkFont(weight="bold"), command=self._start)
        self.start_btn.grid(row=0, column=5, padx=(0, 14), pady=14)

        # folder + progress
        bottom = ctk.CTkFrame(page)
        bottom.grid(row=6, column=0, sticky="ew", pady=(14, 0))
        bottom.grid_columnconfigure(1, weight=1)
        ctk.CTkButton(bottom, text="Choose Folder", width=130,
                      command=self._choose_folder).grid(row=0, column=0, padx=14, pady=14)
        self.folder_label = ctk.CTkLabel(bottom, textvariable=self.folder_var,
                                         text_color=("gray40", "gray60"))
        self.folder_label.grid(row=0, column=1, sticky="w")

        self.progress = ctk.CTkProgressBar(page)
        self.progress.set(0)
        self.progress.grid(row=7, column=0, sticky="ew", pady=(14, 4))
        self.status_label = ctk.CTkLabel(page, text="Ready.", text_color=("gray40", "gray60"))
        self.status_label.grid(row=8, column=0, sticky="w")

        if self.ffmpeg_dir is None:
            self._log("Note: ffmpeg not found locally. The packaged .exe bundles it "
                      "automatically; running from source needs ffmpeg on PATH for "
                      "MP3 and high-res merging.")
        return page

    # ---- activity page ----------------------------------------------------
    def _page_activity(self, parent):
        page = ctk.CTkFrame(parent, fg_color="transparent")
        page.grid_columnconfigure(0, weight=1)
        page.grid_rowconfigure(1, weight=1)
        ctk.CTkLabel(page, text="Activity Log", font=ctk.CTkFont(size=26, weight="bold")
                     ).grid(row=0, column=0, sticky="w", pady=(0, 12))
        self.log_box = ctk.CTkTextbox(page, font=ctk.CTkFont(family="Consolas", size=12))
        self.log_box.grid(row=1, column=0, sticky="nsew")
        self.log_box.configure(state="disabled")
        return page

    # ---- settings page ----------------------------------------------------
    def _page_settings(self, parent):
        page = ctk.CTkFrame(parent, fg_color="transparent")
        page.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(page, text="Settings", font=ctk.CTkFont(size=26, weight="bold")
                     ).grid(row=0, column=0, sticky="w", pady=(0, 16))

        card = ctk.CTkFrame(page)
        card.grid(row=1, column=0, sticky="ew")
        card.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(card, text="Default save folder").grid(row=0, column=0, padx=16, pady=14, sticky="w")
        ctk.CTkButton(card, text="Change", width=100, command=self._choose_folder
                      ).grid(row=0, column=2, padx=16)
        ctk.CTkLabel(card, textvariable=self.folder_var, text_color=("gray40", "gray60")
                     ).grid(row=0, column=1, sticky="w")

        ctk.CTkLabel(card, text="Default quality").grid(row=1, column=0, padx=16, pady=14, sticky="w")
        ctk.CTkOptionMenu(card, variable=self.quality_var, values=list(QUALITY_PRESETS.keys())
                          ).grid(row=1, column=1, sticky="w")

        about = ctk.CTkFrame(page)
        about.grid(row=2, column=0, sticky="ew", pady=16)
        ctk.CTkLabel(about, text=f"{APP_NAME}", font=ctk.CTkFont(size=16, weight="bold")
                     ).grid(row=0, column=0, padx=16, pady=(14, 2), sticky="w")
        ctk.CTkLabel(about, text="Free • No key • No account. Powered by yt-dlp.",
                     text_color=("gray40", "gray60")).grid(row=1, column=0, padx=16, pady=(0, 14), sticky="w")
        return page

    # ---- dashboard page ---------------------------------------------------
    def _page_dashboard(self, parent):
        page = ctk.CTkFrame(parent, fg_color="transparent")
        page.grid_columnconfigure((0, 1, 2), weight=1)
        ctk.CTkLabel(page, text="Dashboard", font=ctk.CTkFont(size=26, weight="bold")
                     ).grid(row=0, column=0, columnspan=3, sticky="w", pady=(0, 16))
        self.dash_cards = {}
        for i, (key, title) in enumerate([("done", "Completed"), ("failed", "Failed"),
                                          ("total", "Total")]):
            c = ctk.CTkFrame(page)
            c.grid(row=1, column=i, padx=8, sticky="ew")
            val = ctk.CTkLabel(c, text="0", font=ctk.CTkFont(size=34, weight="bold"))
            val.grid(row=0, column=0, padx=24, pady=(20, 4))
            ctk.CTkLabel(c, text=title, text_color=("gray40", "gray60")
                         ).grid(row=1, column=0, padx=24, pady=(0, 20))
            self.dash_cards[key] = val
        ctk.CTkLabel(page, text="Paste your links on the Download page to get started.",
                     text_color=("gray40", "gray60")).grid(row=2, column=0, columnspan=3,
                                                            sticky="w", pady=20)
        return page

    # ---- helpers ----------------------------------------------------------
    def _counter_text(self):
        c = self.counts
        return f"✔ {c['done']}   ⬇ {c['active']}   ✖ {c['failed']}   |   Total: {c['total']}"

    def _refresh_counters(self):
        self.counter_label.configure(text=self._counter_text())
        if hasattr(self, "dash_cards"):
            self.dash_cards["done"].configure(text=str(self.counts["done"]))
            self.dash_cards["failed"].configure(text=str(self.counts["failed"]))
            self.dash_cards["total"].configure(text=str(self.counts["total"]))

    def _bump_conc(self, delta):
        self.concurrent = max(1, min(5, self.concurrent + delta))
        self.conc_value.configure(text=str(self.concurrent))

    def _update_link_count(self):
        n = len([u for u in self.url_box.get("1.0", "end").splitlines() if u.strip()])
        self.link_count_label.configure(text=f"{n} links detected")

    def _clear_input(self):
        self.url_box.delete("1.0", "end")
        self._update_link_count()

    def _choose_folder(self):
        folder = filedialog.askdirectory(initialdir=self.folder_var.get() or os.getcwd())
        if folder:
            self.folder_var.set(folder)

    def _log(self, text):
        if not hasattr(self, "log_box"):
            return
        self.log_box.configure(state="normal")
        self.log_box.insert("end", text + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")

    # ---- download orchestration ------------------------------------------
    def _start(self):
        if self.is_downloading:
            return
        urls = [u.strip() for u in self.url_box.get("1.0", "end").splitlines() if u.strip()]
        if not urls:
            messagebox.showwarning(APP_NAME, "Please paste at least one link.")
            return
        out_dir = self.folder_var.get().strip()
        os.makedirs(out_dir, exist_ok=True)

        self.is_downloading = True
        self.stop_event.clear()
        self.counts = {"done": 0, "active": 0, "failed": 0, "total": len(urls)}
        self._refresh_counters()
        self.progress.set(0)
        self.start_btn.configure(state="disabled", text="DOWNLOADING...")
        self.stop_btn.configure(state="normal")
        self._log(f"Queued {len(urls)} item(s) with {self.concurrent} concurrent worker(s).")

        threading.Thread(target=self._supervise,
                         args=(urls, out_dir, self.quality_var.get(), self.concurrent),
                         daemon=True).start()

    def _stop(self):
        self.stop_event.set()
        self.status_label.configure(text="Stopping...")
        self._log("Stop requested - finishing current items then halting.")

    def _supervise(self, urls, out_dir, quality_label, workers):
        work_q = queue.Queue()
        for u in urls:
            work_q.put(u)

        threads = []
        for _ in range(min(workers, len(urls))):
            t = threading.Thread(target=self._worker,
                                 args=(work_q, out_dir, quality_label), daemon=True)
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

        self.msg_queue.put(("done", None))

    def _worker(self, work_q, out_dir, quality_label):
        fmt = QUALITY_PRESETS.get(quality_label, "best")
        is_audio = quality_label == "Audio only (MP3)"

        while not self.stop_event.is_set():
            try:
                url = work_q.get_nowait()
            except queue.Empty:
                return

            self.msg_queue.put(("active", +1))
            opts = {
                "format": fmt,
                "outtmpl": os.path.join(out_dir, "%(title)s [%(id)s].%(ext)s"),
                "noplaylist": False,
                "ignoreerrors": True,
                "quiet": True,
                "no_warnings": True,
                "progress_hooks": [self._hook],
            }
            if self.ffmpeg_dir:
                opts["ffmpeg_location"] = self.ffmpeg_dir
            if is_audio:
                opts["postprocessors"] = [{"key": "FFmpegExtractAudio",
                                           "preferredcodec": "mp3", "preferredquality": "192"}]
            else:
                opts["merge_output_format"] = "mp4"

            try:
                with yt_dlp.YoutubeDL(opts) as ydl:
                    ydl.download([url])
                self.msg_queue.put(("done_one", url))
            except StopRequested:
                self.msg_queue.put(("log", f"Stopped: {url}"))
            except Exception as e:  # noqa: BLE001
                self.msg_queue.put(("failed_one", f"{url} :: {e}"))
            finally:
                self.msg_queue.put(("active", -1))

    def _hook(self, d):
        if self.stop_event.is_set():
            raise StopRequested()
        if d.get("status") == "downloading":
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            done = d.get("downloaded_bytes", 0)
            if total:
                self.msg_queue.put(("progress", done / total))
            name = os.path.basename(d.get("filename", ""))
            spd = d.get("speed")
            spd_txt = f"{spd/1024/1024:.1f} MB/s" if spd else ""
            self.msg_queue.put(("status", f"Downloading {name}  {spd_txt}"))
        elif d.get("status") == "finished":
            self.msg_queue.put(("progress", 1.0))
            self.msg_queue.put(("status", "Merging / processing..."))

    # ---- queue pump -------------------------------------------------------
    def _drain_queue(self):
        try:
            while True:
                kind, payload = self.msg_queue.get_nowait()
                if kind == "progress":
                    self.progress.set(payload)
                elif kind == "status":
                    self.status_label.configure(text=payload)
                elif kind == "log":
                    self._log(payload)
                elif kind == "active":
                    self.counts["active"] = max(0, self.counts["active"] + payload)
                    self._refresh_counters()
                elif kind == "done_one":
                    self.counts["done"] += 1
                    self._refresh_counters()
                    self._log(f"Done: {payload}")
                elif kind == "failed_one":
                    self.counts["failed"] += 1
                    self._refresh_counters()
                    self._log(f"Failed: {payload}")
                elif kind == "done":
                    self.is_downloading = False
                    self.start_btn.configure(state="normal", text="START DOWNLOAD")
                    self.stop_btn.configure(state="disabled")
                    self.progress.set(0)
                    msg = "Stopped." if self.stop_event.is_set() else "All downloads finished."
                    self.status_label.configure(text=msg)
                    self._log(msg)
        except queue.Empty:
            pass
        self.after(120, self._drain_queue)


if __name__ == "__main__":
    App().mainloop()
