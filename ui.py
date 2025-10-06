import os
import tkinter as tk
from PIL import Image, ImageTk
import customtkinter as ctk

from cover_downloader import CACHE_DIR, download_cover
from manager import AnimeManager

CARD_WIDTH = 150
CARD_HEIGHT = 200
CARDS_PER_ROW = 5
CARD_BG = "#1e1e1e"
CARD_HOVER_BG = "#2a2a2a"
CARD_BORDER_COLOR = "#444"

class HoverFrame(ctk.CTkFrame):
    """CTkFrame with hover effect"""
    def __init__(self, master=None, hover_color=None, **kwargs):
        # Remove hover_color from kwargs before passing to super()
        self.hover_color = hover_color or "#2a2a2a"
        self.default_color = kwargs.get("fg_color", "#1e1e1e")
        super().__init__(master, **kwargs)

        self.bind("<Enter>", self.on_enter)
        self.bind("<Leave>", self.on_leave)
        self._widgets = []

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
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("dark-blue")

        self.title("Anime Library")
        self.geometry("1200x700")

        self.manager = AnimeManager(anime_dir)
        self.cover_images = {}

        self._setup_layout()
        self.load_anime_grid()

        self.bind_all("<KeyPress-q>", lambda e: self.stop_video())

    def _setup_layout(self):
        self.left_frame = ctk.CTkFrame(self, corner_radius=0)
        self.left_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)

        self.right_frame = ctk.CTkFrame(self, width=300, corner_radius=0)
        self.right_frame.pack(side="right", fill="y", padx=10, pady=10)

        self.title_label = ctk.CTkLabel(
            self.left_frame,
            text="Anime Library",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.title_label.pack(side="top", fill="x", pady=(0, 10))

        self.canvas_frame = ctk.CTkFrame(self.left_frame, corner_radius=0)
        self.canvas_frame.pack(side="top", fill="both", expand=True)

        self.canvas = tk.Canvas(self.canvas_frame, bg="#121212", highlightthickness=0)
        self.scrollbar = ctk.CTkScrollbar(self.canvas_frame, orientation="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.scrollbar.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.grid_frame = ctk.CTkFrame(self.canvas, corner_radius=0)
        self.canvas.create_window((0, 0), window=self.grid_frame, anchor="nw")
        self.grid_frame.bind("<Configure>", self._on_frame_configure)

        # Right Panel
        self.episode_label = ctk.CTkLabel(
            self.right_frame,
            text="Episodes",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.episode_label.pack(side="top", pady=5)

        self.episode_listbox = tk.Listbox(
            self.right_frame,
            width=40,
            font=("Segoe UI", 12),
            bg="#1e1e1e",
            fg="white",
            selectbackground="#ff6600",
        )
        self.episode_listbox.pack(side="top", fill="both", expand=True)
        self.episode_listbox.bind("<Double-Button-1>", self.on_episode_double_click)

        self.btn_resume = ctk.CTkButton(
            self.right_frame,
            text="Resume Last Watched",
            fg_color="#ff6600",
            hover_color="#ff8533",
            command=self.resume_last_watched,
        )
        self.btn_resume.pack(side="top", pady=10)

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
                border_color=CARD_BORDER_COLOR
            )
            card_frame.grid(row=row, column=col, padx=10, pady=10)
            card_frame.grid_propagate(False)

            # Image container
            image_frame = ctk.CTkFrame(card_frame, width=CARD_WIDTH, height=CARD_HEIGHT, fg_color="transparent")
            image_frame.pack_propagate(False)
            image_frame.pack(side="top", fill="both")

            # Load cover
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
                    img = img.resize((CARD_WIDTH, CARD_HEIGHT), Image.Resampling.LANCZOS)
                    photo = ImageTk.PhotoImage(img)
                    img_label = ctk.CTkLabel(image_frame, image=photo, text="")
                    img_label.image = photo
                    self.cover_images[anime_name] = photo
                except Exception:
                    img_label = ctk.CTkLabel(image_frame, text="🖼️", font=("Segoe UI", 48))
            else:
                img_label = ctk.CTkLabel(image_frame, text="🖼️", font=("Segoe UI", 48))

            img_label.pack(fill="both", expand=True)
            card_frame.add_widget(img_label)

            # Title container
            title_label = ctk.CTkLabel(
                card_frame,
                text=anime_name,
                font=ctk.CTkFont(size=12),
                wraplength=CARD_WIDTH,
                justify="center"
            )
            title_label.pack(side="bottom", fill="x", pady=5)
            card_frame.add_widget(title_label)

            # Click bindings
            for widget_item in (card_frame, img_label, title_label):
                widget_item.bind(
                    "<Button-1>",
                    lambda e, n=anime_name, p=anime_path: self.select_anime(n, p),
                )

            col += 1
            if col >= CARDS_PER_ROW:
                col = 0
                row += 1

    def select_anime(self, anime_name, anime_path):
        self.manager.select_anime(anime_name, anime_path)
        self.episode_listbox.delete(0, "end")
        for ep in self.manager.current_episodes:
            self.episode_listbox.insert("end", ep)

        result = self.manager.resume_last_watched()
        if result:
            episode_file, _ = result
            ep_index = self.manager.current_episodes.index(episode_file)
            self.episode_listbox.selection_clear(0, "end")
            self.episode_listbox.selection_set(ep_index)

    def on_episode_double_click(self, event):
        selection = self.episode_listbox.curselection()
        if not selection:
            return
        index = selection[0]
        self.manager.play_from_index(index)

    def resume_last_watched(self):
        result = self.manager.resume_last_watched()
        if result:
            episode_file, index = result
            self.episode_listbox.selection_clear(0, "end")
            self.episode_listbox.selection_set(index)

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
