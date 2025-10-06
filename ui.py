import io
import os
import tkinter as tk

import cairosvg
import customtkinter as ctk
from PIL import Image, ImageTk

from cover_downloader import CACHE_DIR, download_cover
from manager import AnimeManager

CARD_WIDTH = 150
CARD_HEIGHT = 200
CARDS_PER_ROW = 5
CARD_BG = "#1e1e1e"
CARD_HOVER_BG = "#2a2a2a"
CARD_BORDER_COLOR = "#444"
EPISODE_PANEL_WIDTH = 220  # Reduced by ~25%

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")


class HoverFrame(ctk.CTkFrame):
    def __init__(self, master=None, hover_color=None, **kwargs):
        self.hover_color = hover_color or CARD_HOVER_BG
        self.default_color = kwargs.get("fg_color", CARD_BG)
        super().__init__(master, **kwargs)
        self._widgets = []
        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)

    def add_widget(self, widget):
        self._widgets.append(widget)

    def on_enter(self, event):
        self.configure(fg_color=self.hover_color)
        for w in self._widgets:
            if hasattr(w, "configure"):
                w.configure(fg_color=self.hover_color)

    def on_leave(self, event):
        self.configure(fg_color=self.default_color)
        for w in self._widgets:
            if hasattr(w, "configure"):
                w.configure(fg_color=self.default_color)


class AnimeLibraryUI(ctk.CTk):
    def __init__(self, anime_dir: str):
        super().__init__()
        self.title("Anima Lite")
        self.geometry("1200x700")
        self.manager = AnimeManager(anime_dir)
        self.cover_images = {}

        self._setup_layout()
        self.load_anime_grid()

        self.bind_all("<KeyPress-q>", lambda e: self.stop_video())

    def _setup_layout(self):
        # Left frame
        self.left_frame = ctk.CTkFrame(self, corner_radius=0)
        self.left_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        # Right frame
        self.right_frame = ctk.CTkFrame(
            self, width=EPISODE_PANEL_WIDTH, corner_radius=0
        )
        self.right_frame.pack(side="right", fill="y", padx=10, pady=10)

        # Convert SVG to PNG in memory and resize
        favicon_png = cairosvg.svg2png(
            url=os.path.join(os.path.dirname(os.path.abspath(__file__)), "favicon.svg"),
            output_width=32,
            output_height=32,
        )
        favicon_img = Image.open(io.BytesIO(favicon_png))
        favicon_photo = ImageTk.PhotoImage(favicon_img)

        # Title label frame
        title_frame = ctk.CTkFrame(self.left_frame, fg_color="transparent")
        title_frame.pack(side="top", fill="x", pady=(0, 10))

        # Favicon label
        favicon_label = ctk.CTkLabel(title_frame, image=favicon_photo, text="")
        favicon_label.image = favicon_photo
        favicon_label.pack(side="left", padx=(0, 5))

        # Title text
        self.title_label = ctk.CTkLabel(
            title_frame,
            text="Anima Lite",
            font=ctk.CTkFont(size=32, weight="bold"),
            fg_color=None,
            text_color="#ff6600",
        )
        self.title_label.pack(side="left")

        # Scrollable canvas for anime grid
        self.canvas_frame = ctk.CTkFrame(self.left_frame, corner_radius=0)
        self.canvas_frame.pack(side="top", fill="both", expand=True)

        self.canvas = tk.Canvas(self.canvas_frame, bg="#121212", highlightthickness=0)
        self.scrollbar = ctk.CTkScrollbar(
            self.canvas_frame, orientation="vertical", command=self.canvas.yview
        )
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.grid_frame = ctk.CTkFrame(self.canvas, corner_radius=0)
        self.canvas.create_window((0, 0), window=self.grid_frame, anchor="nw")
        self.grid_frame.bind("<Configure>", self._on_frame_configure)

        # Episodes panel
        self.episode_label = ctk.CTkLabel(
            self.right_frame, text="Episodes", font=ctk.CTkFont(size=18, weight="bold")
        )
        self.episode_label.pack(side="top", pady=5)

        self.episode_canvas_frame = ctk.CTkFrame(self.right_frame, corner_radius=0)
        self.episode_canvas_frame.pack(side="top", fill="both", expand=True)

        self.episode_canvas = tk.Canvas(
            self.episode_canvas_frame, bg="#1e1e1e", highlightthickness=0
        )
        self.episode_scrollbar = ctk.CTkScrollbar(
            self.episode_canvas_frame,
            orientation="vertical",
            command=self.episode_canvas.yview,
        )
        self.episode_canvas.configure(yscrollcommand=self.episode_scrollbar.set)
        self.episode_scrollbar.pack(side="right", fill="y")
        self.episode_canvas.pack(side="left", fill="both", expand=True)

        self.episode_frame = ctk.CTkFrame(self.episode_canvas, corner_radius=0)
        self.episode_canvas.create_window(
            (0, 0), window=self.episode_frame, anchor="nw"
        )
        self.episode_frame.bind(
            "<Configure>",
            lambda e: self.episode_canvas.configure(
                scrollregion=self.episode_canvas.bbox("all")
            ),
        )

        # Resume button frame
        self.btn_frame = ctk.CTkFrame(
            self.right_frame, corner_radius=5, fg_color="transparent"
        )
        self.btn_frame.pack(side="top", pady=10)
        self.btn_resume = ctk.CTkButton(
            self.btn_frame,
            text="Resume Last Watched",
            fg_color="#ff8533",
            hover_color="#ffa366",
            width=EPISODE_PANEL_WIDTH,
            command=self.resume_last_watched,
        )
        self.btn_resume.pack(padx=5)

    def _on_frame_configure(self, event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def load_anime_grid(self):
        for widget in self.grid_frame.winfo_children():
            widget.destroy()

        row, col = 0, 0
        skip_downloading_covers = False

        for anime_name, anime_path in self.manager.anime_list:
            card_frame = HoverFrame(
                self.grid_frame,
                width=CARD_WIDTH,
                height=CARD_HEIGHT + 40,
                corner_radius=10,
                fg_color=CARD_BG,
                hover_color=CARD_HOVER_BG,
                border_width=1,
                border_color=CARD_BORDER_COLOR,
            )
            card_frame.grid(row=row, column=col, padx=10, pady=10)
            card_frame.grid_propagate(False)

            # Image
            image_frame = ctk.CTkFrame(
                card_frame, width=CARD_WIDTH, height=CARD_HEIGHT, fg_color="transparent"
            )
            image_frame.pack_propagate(False)
            image_frame.pack(side="top", fill="both")

            filename = anime_name.replace(" ", "_") + ".jpg"
            cover_path = os.path.join(CACHE_DIR, filename)
            if not skip_downloading_covers and not os.path.exists(cover_path):
                try:
                    result = download_cover(anime_name)
                    if result:
                        cover_path = result
                except Exception:
                    skip_downloading_covers = True
                    cover_path = None

            if cover_path and os.path.exists(cover_path):
                try:
                    img = Image.open(cover_path).convert("RGB")
                    img = img.resize(
                        (CARD_WIDTH, CARD_HEIGHT), Image.Resampling.LANCZOS
                    )
                    photo = ImageTk.PhotoImage(img)
                    img_label = ctk.CTkLabel(image_frame, image=photo, text="")
                    img_label.image = photo
                    self.cover_images[anime_name] = photo
                except Exception:
                    img_label = ctk.CTkLabel(
                        image_frame, text="🖼️", font=("Segoe UI", 48)
                    )
            else:
                img_label = ctk.CTkLabel(image_frame, text="🖼️", font=("Segoe UI", 48))

            img_label.pack(fill="both", expand=True)
            card_frame.add_widget(img_label)

            # Title
            title_label = ctk.CTkLabel(
                card_frame,
                text=anime_name,
                font=ctk.CTkFont(size=12),
                wraplength=CARD_WIDTH,
                justify="center",
            )
            title_label.pack(side="bottom", fill="x", pady=5)
            card_frame.add_widget(title_label)

            # Hover binding on all children
            for w in (card_frame, img_label, title_label):
                w.bind("<Enter>", card_frame.on_enter)
                w.bind("<Leave>", card_frame.on_leave)
                w.bind(
                    "<Button-1>",
                    lambda e, n=anime_name, p=anime_path: self.select_anime(n, p),
                )

            col += 1
            if col >= CARDS_PER_ROW:
                col = 0
                row += 1

    # Modern episode panel
    def select_anime(self, anime_name, anime_path):
        self.manager.select_anime(anime_name, anime_path)

        # Clear previous
        for widget in self.episode_frame.winfo_children():
            widget.destroy()

        for index, ep in enumerate(self.manager.current_episodes):
            lbl = ctk.CTkLabel(
                self.episode_frame,
                text=f"{index + 1}. {ep}",  # Add numbering
                font=ctk.CTkFont(size=12),
                anchor="w",
                padx=5,
                pady=3,
                corner_radius=5,
            )
            lbl.pack(fill="x", pady=2, padx=2)
            lbl.bind("<Enter>", lambda e, l=lbl: l.configure(fg_color="#2a2a2a"))
            lbl.bind("<Leave>", lambda e, l=lbl: l.configure(fg_color="#1e1e1e"))
            lbl.bind(
                "<Button-1>", lambda e, idx=index: self.manager.play_from_index(idx)
            )

        # Highlight last watched
        result = self.manager.resume_last_watched()
        if result:
            episode_file, _ = result
            for w in self.episode_frame.winfo_children():
                if w.cget("text") == episode_file:
                    w.configure(fg_color="#ff6600")

    def resume_last_watched(self):
        result = self.manager.resume_last_watched()
        if result:
            episode_file, index = result
            for w in self.episode_frame.winfo_children():
                if w.cget("text") == episode_file:
                    w.configure(fg_color="#ff6600")

    def stop_video(self):
        self.manager.player.stop()

    def on_close(self):
        self.stop_video()
        self.destroy()


if __name__ == "__main__":
    VIDEOS_DIR = "/home/moondip/Videos"
    os.makedirs(CACHE_DIR, exist_ok=True)
    app = AnimeLibraryUI(VIDEOS_DIR)
    app.protocol("WM_DELETE_WINDOW", app.on_close)
    app.mainloop()
