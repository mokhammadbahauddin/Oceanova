# Simpan file ini sebagai gui.py

import customtkinter as ctk
from collections import deque
import os
import pygame
from PIL import Image
try:
    from visualizer import VisualizerEngine
    from ui_components import AudioVisualizer, FullscreenVisualizer
    VISUALIZER_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Visualizer not available: {e}")
    VISUALIZER_AVAILABLE = False

try:
    from backend import MusicPlayer, Song, DoublyLinkedList
except ImportError:
    print("Error: File 'backend.py' tidak ditemukan.")
    print("Pastikan 'backend.py' berada di folder yang sama dengan 'gui.py'.")
    exit()

try:
    from mutagen.mp3 import MP3
    from mutagen.oggvorbis import OggVorbis
    from mutagen.wave import WAVE
    from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB, TCON
except ImportError:
    print("Error: Library 'mutagen' tidak ditemukan. Harap instal: pip install mutagen")
    exit()

try:
    from PIL import Image
except ImportError:
    print("Error: Library 'Pillow' tidak ditemukan. Harap instal: pip install Pillow")
    exit()

ctk.set_appearance_mode("dark")
# --- PERBAIKAN: Kembali ke tema default untuk menghindari error ---
ctk.set_default_color_theme("blue")


# =============================================================================
# JENDELA UTAMA (USER VIEW)
# =============================================================================
class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        # --- PALET WARNA TEMA BARU ---
        self.COLOR_PALETTE = {
            "window_bg": "#161616",
            "sidebar_bg": "#212121",
            "content_bg": "#1E1A3D",
            "right_sidebar_bg": "#212121",
            "player_bg": "#212121",
            "card_bg": "#303030",
            "card_hover": "#424242",
            "text_primary": "#DCDEE7",
            "text_secondary": "#DCDEE7",
            "accent_pink": "#5FAEF8",
            "accent_blue": "#5FAEF8",
            "accent_purple": "#6A55F5"
        }

        # --- Terapkan warna BG utama ke jendela ---
        self.configure(fg_color=self.COLOR_PALETTE["window_bg"])

        pygame.init()
        if VISUALIZER_AVAILABLE:
            self.visualizer_engine = VisualizerEngine()
            self.visualizer_engine.start()
            print("✅ Visualizer Engine started")
        else:
            self.visualizer_engine = None

        self.title("Oceanova")
        self.geometry("1400x900")
        try:
            self.iconbitmap("logo.ico")  # Ganti "logo.ico" dengan nama file Anda
        except Exception as e:
            print(f"Peringatan: File logo 'logo.ico' tidak ditemukan atau rusak. Menggunakan ikon default. Error: {e}")
            pass  # Lanjutkan tanpa crash

        self.player = MusicPlayer()
        self.add_to_playlist_window = None
        self.username_var = ctk.StringVar(value=self.player.username)
        self.last_seek_time = 0.0
        self.is_slider_seeking = False
        self.current_genre_filter = "All"
        self.genre_buttons = {}
        self.admin_file_path_var = ctk.StringVar(value="Belum ada file dipilih")
        self.admin_image_path_var = ctk.StringVar(value="Belum ada gambar dipilih")
        self.admin_detected_duration = 0

        self.admin_edit_image_path_var = ctk.StringVar(value="Pilih gambar baru (opsional)")
        self.loaded_song_id_to_edit = None

        self.default_art_image_small = self.load_image_safe(None, (80, 80), is_placeholder=True)
        self.default_art_image_large = self.load_image_safe(None, (400, 400), is_placeholder=True)
        self.default_art_image_history = self.load_image_safe(None, (40, 40), is_placeholder=True)
        self.default_art_image_card = self.load_image_safe(None, (150, 150), is_placeholder=True)

        # Konfigurasi grid utama
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)
        self.default_art_image_card = self.load_image_safe(None, (150, 150), is_placeholder=True)

        # --- BARU: Variabel untuk Animasi "Now Playing" ---
        self.np_anim_dots = 0  # Menyimpan jumlah titik (0, 1, 2, atau 3)
        self.np_animation_running = False  # Status untuk memulai/menghentikan loop



        # ------------------------------------------------
        # --- Variabel Lirik ---
        self.current_lyrics = None  # Data lirik {waktu: teks}
        self.current_lyric_times = []  # List waktu untuk pencarian cepat
        self.current_lyric_text = "..."  # Teks yang sedang tampil


        # Konfigurasi grid utama
        self.grid_columnconfigure(1, weight=1)
        # 1. Sidebar Kiri (Kolom 0, Baris 0-2)
        self.sidebar_frame = ctk.CTkFrame(self, width=200, corner_radius=0, fg_color=self.COLOR_PALETTE["sidebar_bg"])
        self.sidebar_frame.grid(row=0, column=0, rowspan=3, sticky="nsw")
        self.sidebar_frame.grid_rowconfigure(9, weight=1)

        self.logo_label = ctk.CTkLabel(self.sidebar_frame, text="Oceanova",
                                       font=ctk.CTkFont(size=20, weight="bold"),
                                       text_color=self.COLOR_PALETTE["text_primary"])
        self.logo_label.grid(row=0, column=0, padx=20, pady=20)

        ctk.CTkLabel(self.sidebar_frame, text="Home", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color="#FDECEE").grid(row=1, column=0, padx=20, pady=(10, 0),
                                                sticky="w")
        self.dashboard_button = ctk.CTkButton(self.sidebar_frame, height=40, text="📊    Dashboard",
                                              font=ctk.CTkFont(size=20, weight="bold"), command=self.show_dashboard,
                                              fg_color="transparent", hover_color=self.COLOR_PALETTE["card_hover"],
                                              text_color="#FDECEE")
        self.dashboard_button.grid(row=2, column=0, padx=20, pady=5, sticky="ew")

        ctk.CTkLabel(self.sidebar_frame, text="Library", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color="#FDECEE").grid(row=3, column=0, padx=20, pady=(10, 0),
                                                sticky="w")
        self.library_button = ctk.CTkButton(self.sidebar_frame, height=40, text="📚    My Library",
                                            font=ctk.CTkFont(size=20, weight="bold"), command=self.show_library,
                                            fg_color="transparent", hover_color=self.COLOR_PALETTE["card_hover"],
                                            text_color="#FDECEE")
        self.library_button.grid(row=4, column=0, padx=20, pady=5, sticky="ew")
        self.playlists_button = ctk.CTkButton(self.sidebar_frame, text="🎵   My Playlists",
                                              font=ctk.CTkFont(size=20, weight="bold"), height=40,
                                              command=self.show_playlists,
                                              fg_color="transparent", hover_color=self.COLOR_PALETTE["card_hover"],
                                              text_color="#FDECEE")
        self.playlists_button.grid(row=5, column=0, padx=20, pady=5, sticky="ew")
        self.favourite_button = ctk.CTkButton(self.sidebar_frame, text="❤  My Favourite",
                                              font=ctk.CTkFont(size=20, weight="bold"), height=40,
                                              command=self.show_favourites,
                                              fg_color="transparent", hover_color=self.COLOR_PALETTE["card_hover"],
                                              text_color="#FDECEE")
        self.favourite_button.grid(row=6, column=0, padx=20, pady=5, sticky="ew")

        ctk.CTkLabel(self.sidebar_frame, text="Support", font=ctk.CTkFont(size=12, weight="bold"),
                     text_color="#FDECEE").grid(row=7, column=0, padx=20, pady=(10, 0),
                                                sticky="w")
        self.setting_button = ctk.CTkButton(self.sidebar_frame, text="⚙️        Settings", height=40,
                                            font=ctk.CTkFont(size=20, weight="bold"), command=self.show_settings,
                                            fg_color="transparent", hover_color=self.COLOR_PALETTE["card_hover"],
                                            text_color="#FDECEE")
        self.setting_button.grid(row=8, column=0, padx=20, pady=5, sticky="ew")

        self.spacer_label = ctk.CTkLabel(self.sidebar_frame, text="")
        self.spacer_label.grid(row=9, column=0)

        self.admin_button = ctk.CTkButton(self.sidebar_frame, text="🛡️ Admin Panel",
                                          font=ctk.CTkFont(size=20, weight="bold"), height=40, fg_color="transparent",
                                          hover_color=self.COLOR_PALETTE["card_hover"],
                                          command=self.show_admin_panel)
        self.admin_button.grid(row=10, column=0, padx=20, pady=10, sticky="ew")

        # 2. Header Frame (Kolom 1-2, Baris 0)
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=1, columnspan=2, sticky="new", padx=20, pady=(20, 10))
        self.header_frame.grid_columnconfigure(0, weight=1)
        self.header_frame.grid_columnconfigure(1, weight=0)

        self.search_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.search_frame.grid(row=0, column=0, sticky="ew")
        self.search_frame.grid_columnconfigure(0, weight=1)
        self.search_entry = ctk.CTkEntry(self.search_frame, placeholder_text="Cari Musik, Album, Artis...",
                                         fg_color=self.COLOR_PALETTE["card_bg"],
                                         border_color=self.COLOR_PALETTE["card_hover"],
                                         text_color=self.COLOR_PALETTE["text_primary"],
                                         placeholder_text_color="#FDECEE")
        self.search_entry.grid(row=0, column=0, sticky="ew", padx=(0, 10))
        self.search_btn = ctk.CTkButton(self.search_frame, text="search", width=60, command=self.on_search,
                                        fg_color=self.COLOR_PALETTE["card_bg"],
                                        hover_color=self.COLOR_PALETTE["card_hover"])
        self.search_btn.grid(row=0, column=1)

        self.profile_frame = ctk.CTkFrame(self.header_frame, fg_color="transparent")
        self.profile_frame.grid(row=0, column=1, sticky="e")

        self.profile_name_label = ctk.CTkLabel(self.profile_frame, textvariable=self.username_var,
                                               font=ctk.CTkFont(weight="bold"),
                                               text_color=self.COLOR_PALETTE["text_primary"])
        self.profile_name_label.pack(side="left", padx=10)

        self.avatar_button = ctk.CTkButton(self.profile_frame, text="👤", width=40, height=40, corner_radius=20,
                                           command=self.show_settings, fg_color=self.COLOR_PALETTE["card_bg"],
                                           hover_color=self.COLOR_PALETTE["card_hover"])
        self.avatar_button.pack(side="left")

        # 3. Main Content Frame (Kolom 1, Baris 1)
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=1, column=1, sticky="nsew", padx=20, pady=(0, 20))
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(1, weight=1)

        self.main_title_label = ctk.CTkLabel(self.main_frame, text="", font=ctk.CTkFont(size=24, weight="bold"),
                                             text_color=self.COLOR_PALETTE["text_primary"])
        self.main_title_label.grid(row=0, column=0, padx=10, pady=(0, 10), sticky="w")

        self.content_frame = ctk.CTkScrollableFrame(self.main_frame, fg_color="transparent")
        self.content_frame._scrollbar.configure(width=0)
        self.content_frame.grid(row=1, column=0, sticky="nsew")
        self.content_frame.grid_columnconfigure(0, weight=1)

        # 4. Sidebar Kanan (Kolom 2, Baris 1)
        self.right_sidebar = ctk.CTkFrame(self, width=280, fg_color=self.COLOR_PALETTE["right_sidebar_bg"],
                                          corner_radius=15)
        self.right_sidebar.grid(row=1, column=2, sticky="nsew", pady=(0, 20), padx=(0, 20))
        self.right_sidebar.grid_rowconfigure(1, weight=1)

        ctk.CTkLabel(self.right_sidebar, text="Recently Played", font=ctk.CTkFont(size=18, weight="bold")).grid(row=0,
                                                                                                                column=0,
                                                                                                                padx=20,
                                                                                                                pady=10,
                                                                                                                sticky="w")

        self.history_frame = ctk.CTkScrollableFrame(self.right_sidebar, fg_color="transparent")
        self.history_frame._scrollbar.configure(width=0)
        self.history_frame.grid(row=1, column=0, sticky="nsew", padx=10)
        self.history_frame.grid_columnconfigure(0, weight=1)

        # 5. Player Bar (Kolom 1-2, Baris 2)
        self.player_bar = ctk.CTkFrame(self, height=100, corner_radius=0, fg_color=self.COLOR_PALETTE["player_bg"])
        self.player_bar.grid(row=2, column=1, columnspan=2, sticky="sew")

        self.player_bar.grid_columnconfigure(2, weight=1)

        self.album_art_button = ctk.CTkButton(self.player_bar, width=80, height=80, fg_color="gray20",
                                              text="", image=self.default_art_image_small,
                                              command=self.show_now_playing_view)
        self.album_art_button.grid(row=0, column=0, rowspan=2, padx=10, pady=10)
        self.mini_visualizer = AudioVisualizer(
            self.player_bar,
            self.visualizer_engine,
            mode='bars',
            width=150,
            height=80,
            bg=self.COLOR_PALETTE["player_bg"]
        )
        self.mini_visualizer.grid(row=0, column=7, rowspan=2, padx=10)
        self.mini_visualizer.start_animation()

        self.info_frame = ctk.CTkFrame(self.player_bar, fg_color="transparent")
        self.info_frame.grid(row=0, column=1, rowspan=2, padx=10, sticky="w")
        self.player_song_title = ctk.CTkLabel(self.info_frame, text="Not Playing", font=ctk.CTkFont(weight="bold"),
                                              text_color=self.COLOR_PALETTE["text_primary"])
        self.player_song_title.pack(anchor="w")
        self.player_song_artist = ctk.CTkLabel(self.info_frame, text="---",
                                               text_color=self.COLOR_PALETTE["text_secondary"])
        self.player_song_artist.pack(anchor="w")
        self.controls_frame = ctk.CTkFrame(self.player_bar, fg_color="transparent")
        self.controls_frame.grid(row=0, column=2, rowspan=2, pady=5, sticky="ew")
        self.controls_frame.grid_columnconfigure(0, weight=1)
        self.button_frame = ctk.CTkFrame(self.controls_frame, fg_color="transparent")
        self.button_frame.pack(fill="x", expand=True)
        self.button_frame.grid_columnconfigure(0, weight=1)
        self.button_frame.grid_columnconfigure(6, weight=2)

        # Tombol Shuffle (Ikon Pink Transparan)
        self.shuffle_button = ctk.CTkButton(self.button_frame, text="🔀", font=ctk.CTkFont(size = 20),width=30, fg_color="transparent",
                                            command=self.on_shuffle_click,
                                            text_color=self.COLOR_PALETTE["text_secondary"],
                                            hover_color=self.COLOR_PALETTE["card_hover"])
        self.shuffle_button.grid(row=0, column=1, padx=5, pady=5)

        # Tombol Prev (Transparan)
        self.prev_button = ctk.CTkButton(self.button_frame, text="<",font=ctk.CTkFont(size = 20), width=50, height=50, corner_radius=25,
                                         command=self.on_prev_click,
                                         fg_color="transparent", hover_color=self.COLOR_PALETTE["card_hover"],
                                         text_color=self.COLOR_PALETTE["text_secondary"])
        self.prev_button.grid(row=0, column=2, padx=5, pady=5)

        # Tombol Play/Pause (Lingkaran Putih Kontras Tinggi)
        self.play_button = ctk.CTkButton(self.button_frame, text="▶",font=ctk.CTkFont(size = 20), width=50, height=50, corner_radius=25,
                                         command=self.on_play_pause_click,
                                         fg_color=self.COLOR_PALETTE["accent_blue"],
                                         text_color=self.COLOR_PALETTE["text_secondary"],
                                         hover_color=self.COLOR_PALETTE["card_hover"])
        self.play_button.grid(row=0, column=3, padx=5, pady=5)

        # Tombol Next (Transparan)
        self.next_button = ctk.CTkButton(self.button_frame, text=">",font=ctk.CTkFont(size = 20),width=50, height=50, corner_radius=25,
                                         command=self.on_next_click,
                                         fg_color="transparent", hover_color=self.COLOR_PALETTE["card_hover"],
                                         text_color=self.COLOR_PALETTE["text_secondary"])
        self.next_button.grid(row=0, column=4, padx=5, pady=5)

        # Tombol Repeat (Ikon Pink Transparan)
        self.repeat_button = ctk.CTkButton(self.button_frame, text="🔁",font=ctk.CTkFont(size = 20), width=30, fg_color="transparent",
                                           command=self.on_repeat_click,
                                           text_color=self.COLOR_PALETTE["text_secondary"],
                                           hover_color=self.COLOR_PALETTE["card_hover"])
        self.repeat_button.grid(row=0, column=5, padx=5, pady=5)

        self.slider_frame = ctk.CTkFrame(self.controls_frame, fg_color="transparent")
        self.slider_frame.pack(fill="x", expand=True, padx=10)
        # --- PERBAIKAN: Hanya kolom 1 yang diberi 'weight' ---
        self.slider_frame.grid_columnconfigure(1, weight=1)

        self.time_start_label = ctk.CTkLabel(self.slider_frame, text="00:00",
                                             text_color=self.COLOR_PALETTE["text_secondary"])
        self.time_start_label.grid(row=0, column=0, padx=5)

        self.slider = ctk.CTkSlider(self.slider_frame, from_=0, to=1, number_of_steps=1000,
                                    command=self.on_slider_drag,
                                    button_length=15,
                                    progress_color=self.COLOR_PALETTE["accent_pink"],
                                    button_color=self.COLOR_PALETTE["text_primary"])
        self.slider.bind("<ButtonPress-1>", self.on_slider_press)
        self.slider.bind("<ButtonRelease-1>", self.on_slider_release)

        self.slider.set(0)
        self.slider.grid(row=0, column=1, sticky="ew")
        self.time_end_label = ctk.CTkLabel(self.slider_frame, text="00:00",
                                           text_color=self.COLOR_PALETTE["text_secondary"])
        self.time_end_label.grid(row=0, column=2, padx=5)

        # --- Kontrol Volume ---
        self.volume_label = ctk.CTkLabel(self.slider_frame, text="🔊",font=ctk.CTkFont(size = 20), text_color=self.COLOR_PALETTE["text_secondary"])
        self.volume_label.grid(row=0, column=3, padx=(10, 5))

        self.volume_slider = ctk.CTkSlider(self.slider_frame, from_=0, to=1, number_of_steps=100,
                                           command=self.on_volume_change,
                                           width=100,
                                           progress_color=self.COLOR_PALETTE["accent_pink"],
                                           button_color=self.COLOR_PALETTE["text_primary"],
                                           button_hover_color=self.COLOR_PALETTE["card_hover"]) # Hover putih pudar
        self.volume_slider.set(1.0)
        pygame.mixer.music.set_volume(1.0)
        self.volume_slider.grid(row=0, column=4, padx=(0, 10))

        self.volume_percent_label = ctk.CTkLabel(self.slider_frame, text="100%",font=ctk.CTkFont(size = 20),
                                                 text_color=self.COLOR_PALETTE["text_secondary"])
        self.volume_percent_label.grid(row=0, column=5, padx=(0, 10))

        self.create_now_playing_view()
        self.update_progress()
        self.show_dashboard()
        self.update_history_sidebar()


        # --- FUNGSI BARU: Untuk memuat gambar dengan aman ---

    def load_image_safe(self, path, size, is_placeholder=False):
        if path and os.path.exists(path):
            try:
                img = Image.open(path)
                return ctk.CTkImage(img, size=size)
            except Exception as e:
                print(f"Gagal memuat gambar {path}: {e}")

        if is_placeholder:
            img = Image.new("RGB", size, (50, 50, 50))
            return ctk.CTkImage(img, size=size)
        return None

    # --- FUNGSI 'Now Playing' View ---
    def create_now_playing_view(self):
        # Frame utama (akan menutupi kolom 1 dan 2)
        self.now_playing_frame = ctk.CTkFrame(self, fg_color=self.COLOR_PALETTE["window_bg"], corner_radius=0)

        self.now_playing_frame.grid_columnconfigure(0, weight=1)
        self.now_playing_frame.grid_rowconfigure(0, weight=0)  # Tombol close
        self.now_playing_frame.grid_rowconfigure(1, weight=1)  # Konten tengah (art + info)
        self.now_playing_frame.grid_rowconfigure(2, weight=0)  # Player bar bawah

        # Tombol Close (seperti di Image 1)
        close_btn = ctk.CTkButton(self.now_playing_frame, text="Close", command=self.hide_now_playing_view,
                                  fg_color=self.COLOR_PALETTE["card_bg"],
                                  hover_color=self.COLOR_PALETTE["card_hover"])
        close_btn.grid(row=0, column=0, padx=20, pady=20, sticky="w")

        # --- Konten Tengah (Art + Info) ---
        np_content_frame = ctk.CTkFrame(self.now_playing_frame, fg_color="transparent")
        np_content_frame.grid(row=1, column=0, sticky="nsew", padx=50, pady=50)
        np_content_frame.grid_rowconfigure(0, weight=1)
        np_content_frame.grid_columnconfigure(0, weight=1, uniform="group1")  # Kolom untuk Art
        np_content_frame.grid_columnconfigure(1, weight=1, uniform="group1")  # Kolom untuk Info


        # Label Album Art (sebelah kiri)
        self.np_art_label = ctk.CTkLabel(np_content_frame, text="", image=self.default_art_image_large)
        self.np_art_label.grid(row=0, column=0, sticky="e", padx=(0, 20))



        # Frame Info (sebelah kanan)
        np_info_frame = ctk.CTkFrame(np_content_frame, fg_color="transparent")
        np_info_frame.grid(row=0, column=1, sticky="w", padx=(20, 0))

        self.np_now_playing_label = ctk.CTkLabel(np_info_frame, text="NOW PLAYING",
                                                 font=ctk.CTkFont(size=14, weight="bold"),
                                                 text_color=self.COLOR_PALETTE["text_secondary"])
        self.np_now_playing_label.pack(anchor="w", pady=(0, 5))
        self.np_title_label = ctk.CTkLabel(np_info_frame, text="Song Title",
                                           font=ctk.CTkFont(size=48, weight="bold"),
                                           text_color=self.COLOR_PALETTE["text_primary"])
        self.np_title_label.pack(anchor="w")

        self.np_artist_label = ctk.CTkLabel(np_info_frame, text="Artist Name", font=ctk.CTkFont(size=24),
                                            text_color=self.COLOR_PALETTE["text_secondary"])
        self.np_artist_label.pack(anchor="w")

        # Label Album (seperti di Image 2)
        self.np_album_label = ctk.CTkLabel(np_info_frame, text="Album Name", font=ctk.CTkFont(size=18),
                                           text_color=self.COLOR_PALETTE["text_secondary"])
        self.np_album_label.pack(anchor="w", pady=(0, 50))

        self.np_lyrics_label = ctk.CTkLabel(np_info_frame, text="...",
                                            font=ctk.CTkFont(size=24, weight="bold"),  # Font besar
                                            text_color=self.COLOR_PALETTE["accent_pink"],  # Warna Pink
                                            wraplength=500,  # Bungkus teks panjang
                                            anchor="w", justify="left")
        self.np_lyrics_label.pack(anchor="w", pady=(20, 0))
        if VISUALIZER_AVAILABLE:
            self.np_mini_visualizer = AudioVisualizer(
                np_info_frame,
                self.visualizer_engine,
                mode='bars',
                width=250,
                height=60,
                bg=self.COLOR_PALETTE["window_bg"]
            )
            self.np_mini_visualizer.pack(anchor="w", pady=(10, 20))
            self.np_mini_visualizer.start_animation()

        # --- Player Bar Bawah ---
        np_bottom_bar = ctk.CTkFrame(self.now_playing_frame, height=120, corner_radius=0,
                                     fg_color=self.COLOR_PALETTE["player_bg"])
        np_bottom_bar.grid(row=2, column=0, sticky="sew")
        np_bottom_bar.grid_columnconfigure(1, weight=1)  # Kolom tengah untuk tombol
        np_bottom_bar.grid_columnconfigure(2, weight=0)  # Kolom kanan untuk volume

        # Slider Durasi (di atas tombol)
        np_slider_frame = ctk.CTkFrame(np_bottom_bar, fg_color="transparent")
        np_slider_frame.grid(row=0, column=0, columnspan=3, sticky="ew", padx=40, pady=(10, 0))
        np_slider_frame.grid_columnconfigure(1, weight=1)


        self.np_time_start_label = ctk.CTkLabel(np_slider_frame, text="00:00",
                                                text_color=self.COLOR_PALETTE["text_secondary"])
        self.np_time_start_label.grid(row=0, column=0, padx=5)

        self.np_slider = ctk.CTkSlider(np_slider_frame, from_=0, to=1, number_of_steps=1000,
                                       command=self.on_slider_drag,
                                       button_length=15,
                                       progress_color=self.COLOR_PALETTE["accent_pink"],
                                       button_color=self.COLOR_PALETTE["text_primary"])
        self.np_slider.bind("<ButtonPress-1>", self.on_slider_press)
        self.np_slider.bind("<ButtonRelease-1>", self.on_slider_release)
        self.np_slider.set(0)
        self.np_slider.grid(row=0, column=1, sticky="ew")

        self.np_time_end_label = ctk.CTkLabel(np_slider_frame, text="00:00",
                                              text_color=self.COLOR_PALETTE["text_secondary"])
        self.np_time_end_label.grid(row=0, column=2, padx=5)

        # Tombol Kontrol (di bawah slider)
        np_button_frame = ctk.CTkFrame(np_bottom_bar, fg_color="transparent")
        np_button_frame.grid(row=1, column=1, sticky="n", pady=(0, 10))


        # Tombol Shuffle (Ikon Pink Transparan)
        self.np_shuffle_button = ctk.CTkButton(np_button_frame, text="🔀", width=40, height=40, fg_color="transparent",
                                               command=self.on_shuffle_click,
                                               text_color=self.COLOR_PALETTE["text_secondary"],
                                               hover_color=self.COLOR_PALETTE["card_hover"],
                                               font=ctk.CTkFont(size = 20 ))
        self.np_shuffle_button.grid(row=0, column=1, padx=10, pady=5)

        # Tombol Prev (Transparan)
        self.np_prev_button = ctk.CTkButton(np_button_frame, text="<", width=60, height=60, corner_radius=30,
                                            command=self.on_prev_click,
                                            fg_color="transparent", hover_color=self.COLOR_PALETTE["card_hover"],
                                            text_color=self.COLOR_PALETTE["text_secondary"],
                                            font=ctk.CTkFont(size = 20))
        self.np_prev_button.grid(row=0, column=2, padx=10, pady=5)

        # Tombol Play/Pause (Lingkaran Putih Kontras Tinggi)
        self.np_play_button = ctk.CTkButton(np_button_frame, text="▶", width=80, height=80, corner_radius=40,
                                            command=self.on_play_pause_click,
                                            fg_color=self.COLOR_PALETTE["text_primary"],
                                            text_color=self.COLOR_PALETTE["player_bg"],
                                            font=ctk.CTkFont(size=20),
                                            hover_color=self.COLOR_PALETTE["card_hover"])
        self.np_play_button.grid(row=0, column=3, padx=10, pady=5)

        # Tombol Next (Transparan)
        self.np_next_button = ctk.CTkButton(np_button_frame, text=">", width=60, height=60, corner_radius=30,
                                            command=self.on_next_click,
                                            fg_color="transparent", hover_color=self.COLOR_PALETTE["card_hover"],
                                            text_color=self.COLOR_PALETTE["text_secondary"],
                                            font=ctk.CTkFont(size = 20))
        self.np_next_button.grid(row=0, column=4, padx=10, pady=5)

        # Tombol Repeat (Ikon Pink Transparan)
        self.np_repeat_button = ctk.CTkButton(np_button_frame, text="🔁", width=40, height=40, fg_color="transparent",
                                              command=self.on_repeat_click,
                                              text_color=self.COLOR_PALETTE["text_secondary"],
                                              hover_color=self.COLOR_PALETTE["card_hover"],
                                              font=ctk.CTkFont(size = 20))
        self.np_repeat_button.grid(row=0, column=5, padx=10, pady=5)

        # Kontrol Volume (di kanan bawah)
        np_volume_frame = ctk.CTkFrame(np_bottom_bar, fg_color="transparent")
        np_volume_frame.grid(row=1, column=2, padx=(20, 40), pady=(0, 10), sticky="e")
        np_volume_frame.grid_columnconfigure(1, weight=1)

        self.np_volume_label = ctk.CTkLabel(np_volume_frame, text="🔊",font=ctk.CTkFont(size = 20), text_color=self.COLOR_PALETTE["text_secondary"])
        self.np_volume_label.grid(row=0, column=0, padx=(0, 5))

        self.np_volume_slider = ctk.CTkSlider(np_volume_frame, from_=0, to=1, number_of_steps=100,
                                              command=self.on_volume_change,
                                              width=120,
                                              progress_color=self.COLOR_PALETTE["accent_pink"],
                                              button_color=self.COLOR_PALETTE["text_primary"],
                                              button_hover_color="#F0F0F0")  # Hover putih pudar
        self.np_volume_slider.set(1.0)
        self.np_volume_slider.grid(row=0, column=1)

        self.np_volume_percent_label = ctk.CTkLabel(np_volume_frame, text="100%",font=ctk.CTkFont(size = 20), text_color=self.COLOR_PALETTE["text_secondary"])
        self.np_volume_percent_label.grid(row=0, column=2, padx=(5, 0))

    def show_now_playing_view(self):
        if not self.player.current_song:
            print("Tidak ada lagu yang diputar.")
            return
        self.update_player_ui()
        self.now_playing_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.now_playing_frame.lift()

        # --- BARU: Mulai animasi ---
        if not self.np_animation_running: # Hanya mulai jika belum berjalan
            self.np_animation_running = True
            self._animate_now_playing_dots()

    def _animate_now_playing_dots(self):
        """Loop untuk menganimasikan titik-titik 'Now Playing'."""
        if not self.np_animation_running:
            return  # Hentikan loop jika view ditutup

        try:
            # Update jumlah titik (akan berputar 0, 1, 2, 3, 0, ...)
            self.np_anim_dots = (self.np_anim_dots + 1) % 5

            dots = "." * self.np_anim_dots  # Hasilnya: "", ".", "..", "..."

            # Atur teks (tambahkan spasi agar rata kiri dan tidak "melompat")
            base_text = "NOW PLAYING"
            self.np_now_playing_label.configure(text=f"{base_text}{dots:<3}")

            # Jadwalkan frame berikutnya (setiap 500ms atau 0.5 detik)
            self.after(500, self._animate_now_playing_dots)

        except Exception as e:
            # Jika jendela ditutup saat animasi berjalan
            print(f"Error animasi titik: {e}")
            self.np_animation_running = False

    def hide_now_playing_view(self):
        self.now_playing_frame.place_forget()

        # --- BARU: Hentikan animasi ---
        self.np_animation_running = False
        self.np_now_playing_label.configure(text="NOW PLAYING")  # Reset ke teks awal

    # --- FUNGSI PLAYER BAR ---
    def format_time(self, seconds):
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins:02}:{secs:02}"

    def update_progress(self):
        if self.player.is_playing and self.player.current_song and not self.is_slider_seeking:
            total_duration = self.player.current_song.duration_seconds
            current_time = self.player.get_current_playback_time()
            # --- BARU: Logika Lirik ---
            # 1. Coba muat lirik jika belum ada (mungkin baru selesai download)
            if self.current_lyrics is None:
                self.current_lyrics = self.player.parse_lyrics(self.player.current_song.file_path)
                if self.current_lyrics:
                    self.current_lyric_times = list(self.current_lyrics.keys())
                    print("Lirik dimuat ke GUI!")

            # 2. Update tampilan teks jika lirik ada
            if self.current_lyrics and self.current_lyric_times:
                # Cari teks lirik berdasarkan waktu saat ini
                # Kita cari timestamp terbesar yang <= current_time
                display_text = ""
                for t in self.current_lyric_times:
                    if t <= current_time:
                        display_text = self.current_lyrics[t]
                    else:
                        break  # Berhenti karena waktu lirik sudah lewat waktu lagu

                # Update label hanya jika teks berubah (untuk performa)
                if display_text != self.current_lyric_text:
                    self.current_lyric_text = display_text
                    # Hanya update jika Now Playing sedang dibuka
                    if self.now_playing_frame.winfo_ismapped():
                        self.np_lyrics_label.configure(text=display_text)
            if current_time < total_duration:
                current_time_str = self.format_time(current_time)
                self.time_start_label.configure(text=current_time_str)
                self.np_time_start_label.configure(text=current_time_str)

                slider_pos = current_time / total_duration
                self.slider.set(slider_pos)
                self.np_slider.set(slider_pos)
            else:
                if self.player.repeat_mode != "one":
                    self.on_next_click()
        self.after(100, self.update_progress)

    def on_slider_press(self, event):
        self.is_slider_seeking = True

    def on_slider_drag(self, value):
        if self.player.current_song:
            total_duration = self.player.current_song.duration_seconds
            seek_time_sec = value * total_duration
            seek_time_str = self.format_time(seek_time_sec)

            self.time_start_label.configure(text=seek_time_str)
            self.np_time_start_label.configure(text=seek_time_str)

    def on_slider_release(self, event):
        self.is_slider_seeking = False
        if self.player.current_song:
            if self.now_playing_frame.winfo_ismapped():
                value = self.np_slider.get()
            else:
                value = self.slider.get()

            total_duration = self.player.current_song.duration_seconds
            seek_time_sec = value * total_duration

            self.player.seek_song(seek_time_sec)

    # --- BARU: Fungsi Kontrol Volume ---
    def on_volume_change(self, value):
        """Dipanggil oleh KEDUA slider volume."""
        pygame.mixer.music.set_volume(value)

        self.volume_slider.set(value)
        self.np_volume_slider.set(value)

        percent_str = f"{int(value * 100)}%"
        self.volume_percent_label.configure(text=percent_str)
        self.np_volume_percent_label.configure(text=percent_str)

        if value == 0:
            self.volume_label.configure(text="🔇")
            self.np_volume_label.configure(text="🔇")
        else:
            self.volume_label.configure(text="🔊")
            self.np_volume_label.configure(text="🔊")

    # --- FUNGSI SIDEBAR KANAN ---
    def update_history_sidebar(self):
        for widget in self.history_frame.winfo_children():
            widget.destroy()
        history = self.player.get_recently_played()
        if not history:
            ctk.CTkLabel(self.history_frame, text="Belum ada riwayat.").pack(anchor="w", padx=10)
            return
        for song in history:
            history_item = ctk.CTkFrame(self.history_frame, fg_color=self.COLOR_PALETTE["card_bg"])
            history_item.pack(fill="x", pady=5)
            history_item.grid_columnconfigure(1, weight=1)

            img = self.load_image_safe(song.image_path, (40, 40))
            art = ctk.CTkLabel(history_item, text="", image=img)
            art.grid(row=0, column=0, rowspan=2, padx=10, pady=10)

            title = ctk.CTkLabel(history_item, text=song.title, font=ctk.CTkFont(weight="bold"), anchor="w")
            title.grid(row=0, column=1, sticky="ew", padx=5)
            artist = ctk.CTkLabel(history_item, text=song.artist, text_color=self.COLOR_PALETTE["text_secondary"],
                                  anchor="w")
            artist.grid(row=1, column=1, sticky="ew", padx=5)
            play_btn = ctk.CTkButton(history_item, text="▶", width=30,fg_color=self.COLOR_PALETTE["accent_pink"], hover_color=self.COLOR_PALETTE["card_hover"],
                                     command=lambda s=song: self.on_play_song(s, None))
            play_btn.grid(row=0, column=2, rowspan=2, padx=10)

    # --- FUNGSI TAMPILAN (VIEWS) ---
    def clear_content_frame(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    # --- FUNGSI TAMPILAN (VIEWS) ---
    def clear_content_frame(self):
        for widget in self.content_frame.winfo_children():
            widget.destroy()

    def _reset_sidebar_buttons(self):
        """Mengatur semua tombol sidebar kembali ke status non-aktif (transparan)."""
        inactive_color = "transparent"
        inactive_text = "#FDECEE"  # Warna teks pink muda

        self.dashboard_button.configure(fg_color=inactive_color, text_color=inactive_text)
        self.library_button.configure(fg_color=inactive_color, text_color=inactive_text)
        self.playlists_button.configure(fg_color=inactive_color, text_color=inactive_text)
        self.favourite_button.configure(fg_color=inactive_color, text_color=inactive_text)
        self.setting_button.configure(fg_color=inactive_color, text_color=inactive_text)
        self.admin_button.configure(fg_color=inactive_color, text_color=inactive_text)

    def show_dashboard(self):
        self._reset_sidebar_buttons()
        self.dashboard_button.configure(fg_color=self.COLOR_PALETTE["accent_blue"],
                                        text_color="#FFFFFF")  # Atur ke Aktif

        self.clear_content_frame()
        self.main_title_label.configure(text="Dashboard")


        banner = ctk.CTkFrame(self.content_frame, height=150, fg_color='white')
        banner.pack(fill="x", padx=10, pady=10)

        try:
            banner_image = ctk.CTkImage(Image.open("upgrade_banner.png"), size=(1500, 350))
            banner_label = ctk.CTkLabel(banner, text="", image=banner_image)
            banner_label.pack(fill="both", expand=True)
        except Exception as e:
            print(f"Peringatan: Gagal memuat upgrade_banner.png: {e}. Menampilkan teks fallback.")
            banner_label = ctk.CTkLabel(banner, text="Upgrade to Premium!", font=ctk.CTkFont(size=20))
            banner_label.place(relx=0.5, rely=0.5, anchor="center")

        ctk.CTkLabel(self.content_frame, text="Discover Songs", font=ctk.CTkFont(size=18, weight="bold")).pack(
            anchor="w", padx=10, pady=(10, 0))

        genre_frame = ctk.CTkScrollableFrame(self.content_frame, orientation="horizontal", height=50,
                                             fg_color="transparent")
        genre_frame._scrollbar.configure(height=0)
        genre_frame.pack(fill="x", padx=10, pady=5)

        genres = ["All", "Pop", "R&B", "Rock", "K-Pop", "Jazz", "Blues", "Ambient", "Indie"]
        self.genre_buttons = {}
        for genre in genres:
            btn = ctk.CTkButton(genre_frame, text=genre, font=ctk.CTkFont(size=14, weight="bold"), fg_color=self.COLOR_PALETTE["card_bg"], height=40,
                                hover_color=self.COLOR_PALETTE["card_hover"],
                                command=lambda g=genre: self.on_genre_filter(g))
            btn.pack(side="left", padx=5, anchor="w")
            self.genre_buttons[genre] = btn

        self.card_scroll_frame = ctk.CTkScrollableFrame(self.content_frame, orientation="horizontal", height=250,
                                                        fg_color="transparent")
        self.card_scroll_frame._scrollbar.configure(
            height=15,  # Dibuat terlihat (ubah ke 0 jika ingin tetap tersembunyi)
            fg_color="transparent",  # Warna track
            button_color=self.COLOR_PALETTE["card_hover"],  # Warna scrollbar
            button_hover_color=self.COLOR_PALETTE["accent_pink"]  # Warna saat di-hover
        )
        self.card_scroll_frame.pack(fill="x", expand=True, padx=10, pady=10)
        self.on_genre_filter(self.current_genre_filter)

    def show_library(self):
        self._reset_sidebar_buttons()
        self.library_button.configure(fg_color=self.COLOR_PALETTE["accent_blue"], text_color="#FFFFFF")  # Atur ke Aktif

        self.clear_content_frame()
        self.main_title_label.configure(text="All Songs in Library")
        all_songs = self.player.song_library.values()
        if not all_songs:
            ctk.CTkLabel(self.content_frame, text="Library kosong.").pack(fill="x", padx=10)
            return
        for song in all_songs:
            self.create_song_widget(self.content_frame, song, context_playlist=None)

    def show_playlists(self):
        self._reset_sidebar_buttons()
        self.playlists_button.configure(fg_color=self.COLOR_PALETTE["accent_blue"],
                                        text_color="#FFFFFF")  # Atur ke Aktif

        self.clear_content_frame()
        self.main_title_label.configure(text="My Playlists")

        # --- PERUBAHAN: Frame dibuat transparan ---
        create_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        create_frame.pack(fill="x", pady=(0, 10))
        create_frame.grid_columnconfigure(0, weight=1)

        # --- PERUBAHAN: Menambahkan warna tema ke Entry field ---
        self.playlist_entry = ctk.CTkEntry(create_frame, placeholder_text="Nama playlist baru",
                                           fg_color=self.COLOR_PALETTE["card_bg"],
                                           border_color=self.COLOR_PALETTE["card_hover"],
                                           text_color=self.COLOR_PALETTE["text_primary"],
                                           placeholder_text_color=self.COLOR_PALETTE["text_primary"])
        self.playlist_entry.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        # --- PERUBAHAN: Menambahkan warna tema ke Tombol "Create" ---
        create_btn = ctk.CTkButton(create_frame, text="Create", width=80, command=self.on_create_playlist,
                                   fg_color=self.COLOR_PALETTE["accent_pink"],
                                   hover_color=self.COLOR_PALETTE["card_hover"])
        create_btn.grid(row=0, column=1, padx=10, pady=10)

        self.playlist_status_label = ctk.CTkLabel(self.content_frame, text="")
        self.playlist_status_label.pack(fill="x", padx=10, pady=(0, 10))
        ctk.CTkLabel(self.content_frame, text="Your Playlists", font=ctk.CTkFont(size=16)).pack(fill="x", padx=10,
                                                                                                pady=10)
        playlists = self.player.user_playlists.values()
        if not playlists:
            ctk.CTkLabel(self.content_frame, text="Belum ada playlist.").pack(fill="x", padx=10)
            return
        for pl in playlists:
            # --- PERUBAHAN: Menambahkan warna tema ke Frame Playlist ---
            pl_frame = ctk.CTkFrame(self.content_frame, fg_color=self.COLOR_PALETTE["card_bg"])
            pl_frame.pack(fill="x", pady=5)
            pl_frame.grid_columnconfigure(0, weight=1)

            # --- PERUBAHAN: Menambahkan warna tema ke Label Nama ---
            pl_label = ctk.CTkLabel(pl_frame, text=pl.name, anchor="w", font=ctk.CTkFont(size=14, weight="bold"),
                                    text_color=self.COLOR_PALETTE["text_primary"])
            pl_label.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

            # --- PERUBAHAN: Menambahkan warna tema ke Tombol "View Songs" ---
            view_btn = ctk.CTkButton(pl_frame, text="View Songs", width=80,
                                     command=lambda p=pl: self.show_playlist_songs(p),
                                     fg_color=self.COLOR_PALETTE["accent_blue"],
                                     hover_color=self.COLOR_PALETTE["card_hover"])
            view_btn.grid(row=0, column=1, padx=10)
            delete_btn = ctk.CTkButton(pl_frame, text="X", width=60,
                                       fg_color=self.COLOR_PALETTE["card_bg"], hover_color=self.COLOR_PALETTE["card_hover"],
                                       command=lambda p_name=pl.name: self.on_delete_playlist(p_name))
            delete_btn.grid(row=0, column=2, padx=(5, 10))

    def on_delete_playlist(self, playlist_name):
        # Optional: You could add a confirmation dialog here if you want
        success, message = self.player.user_delete_playlist(playlist_name)

        if success:
            self.playlist_status_label.configure(text=message, text_color="green")
            # Refresh the playlist view to remove the deleted item
            self.show_playlists()
        else:
            self.playlist_status_label.configure(text=message, text_color="red")
    def show_playlist_songs(self, playlist_obj):
        self.clear_content_frame()
        self.main_title_label.configure(text=f"Playlist: {playlist_obj.name}")

        # --- BARU: Frame untuk tombol header ---
        header_btn_frame = ctk.CTkFrame(self.content_frame, fg_color="transparent")
        header_btn_frame.pack(fill="x", pady=(0, 15))
        header_btn_frame.grid_columnconfigure(0, weight=0)
        header_btn_frame.grid_columnconfigure(1, weight=1)  # Spacer
        header_btn_frame.grid_columnconfigure(2, weight=0)



        # --- BARU: Tombol Tambah Lagu ---
        add_song_btn = ctk.CTkButton(header_btn_frame, text="+ Tambah Lagu dari Library",
                                     command=lambda p=playlist_obj: self.open_library_song_selector(p),
                                     fg_color=self.COLOR_PALETTE["accent_pink"],
                                     hover_color=self.COLOR_PALETTE["card_hover"])
        add_song_btn.grid(row=0, column=2, padx=10, sticky="e")
        # --- Akhir Frame Header ---

        songs = playlist_obj.view_songs()
        if not songs:
            ctk.CTkLabel(self.content_frame, text="Playlist ini kosong.").pack(fill="x", padx=10)
            return
        for song in songs:
            self.create_song_widget(self.content_frame, song, context_playlist=playlist_obj)

    def show_favourites(self):
        self._reset_sidebar_buttons()
        self.favourite_button.configure(fg_color=self.COLOR_PALETTE["accent_blue"],
                                        text_color="#FFFFFF")  # Atur ke Aktif

        self.show_playlist_songs(self.player.favourite_playlist)

    def show_admin_panel(self):
        # Cek apakah sudah login sebelumnya (opsional, agar tidak tanya password terus)
        if getattr(self, "is_admin_authenticated", False):
            self._load_admin_panel_content()
            return

        # 1. Tampilkan Peringatan Awal (Simulasi Pop-up Konfirmasi)
        # Karena CTk tidak punya Yes/No dialog bawaan yang sederhana, kita pakai Toplevel window kecil
        self.auth_dialog = ctk.CTkToplevel(self)
        self.auth_dialog.title("Restricted Access")
        self.auth_dialog.geometry("400x200")
        self.auth_dialog.grab_set()  # Fokus ke window ini

        # Pusatkan window
        self.auth_dialog.update_idletasks()
        x = (self.winfo_screenwidth() - self.auth_dialog.winfo_width()) // 2
        y = (self.winfo_screenheight() - self.auth_dialog.winfo_height()) // 2
        self.auth_dialog.geometry(f"+{x}+{y}")

        ctk.CTkLabel(self.auth_dialog,
                     text="Hanya seorang Admin yang bisa menggunakan fitur ini.\nApakah kamu seorang Admin?",
                     font=ctk.CTkFont(size=14),
                     text_color=self.COLOR_PALETTE["text_primary"],
                     wraplength=350).pack(pady=30)

        btn_frame = ctk.CTkFrame(self.auth_dialog, fg_color="transparent")
        btn_frame.pack(pady=10)

        ctk.CTkButton(btn_frame, text="Yes", width=100,
                      fg_color=self.COLOR_PALETTE["accent_pink"],
                      command=self._prompt_password).pack(side="left", padx=10)

        ctk.CTkButton(btn_frame, text="No", width=100,
                      fg_color=self.COLOR_PALETTE["card_hover"],
                      command=self.auth_dialog.destroy).pack(side="left", padx=10)

    def _prompt_password(self):
        """Fungsi internal untuk meminta password setelah klik Yes."""
        self.auth_dialog.destroy()  # Tutup dialog Yes/No

        # 2. Minta Password
        # Kita gunakan CTkInputDialog bawaan untuk ini
        dialog = ctk.CTkInputDialog(text="Masukkan Password Admin:", title="Verifikasi Admin")

        # Trik agar dialog muncul di tengah (sedikit hacky karena CTkInputDialog tidak punya parameter parent)
        # Tapi defaultnya sudah cukup oke.

        password = dialog.get_input()

        # 3. Validasi Password
        if password == "admin":
            self.is_admin_authenticated = True  # Simpan status login
            self._load_admin_panel_content()  # Buka panel admin
        else:
            if password is not None:  # Jika user tidak klik cancel
                # Tampilkan pesan error (bisa pakai print atau dialog error kecil)
                print("Akses ditolak: Password salah.")
                # Opsional: Tampilkan dialog error
                error_pop = ctk.CTkToplevel(self)
                error_pop.title("Error")
                error_pop.geometry("300x150")
                ctk.CTkLabel(error_pop, text="Password Salah!", text_color="red").pack(pady=40)
                # ...

    def _load_admin_panel_content(self):
        """Fungsi internal untuk menampilkan isi Admin Panel (kode lama Anda)."""
        self._reset_sidebar_buttons()
        self.admin_button.configure(fg_color=self.COLOR_PALETTE["card_hover"],
                                    text_color="#FFFFFF")  # Atur ke Aktif

        self.clear_content_frame()
        self.main_title_label.configure(text="Admin Panel")

        # --- Kode Admin Panel Asli Anda (Paste di sini) ---
        # Salin semua kode dari `self.admin_add_frame = ...` sampai akhir fungsi show_admin_panel lama Anda
        # ke dalam fungsi ini.



        # ... (Lanjutkan dengan semua kode UI Admin Panel Anda yang panjang itu) ...
        # (Agar jawaban tidak terlalu panjang, saya tidak paste ulang seluruh 200 baris UI Admin Panel Anda di sini)
        # (Pastikan Anda memindahkan logika UI Admin Panel ke dalam fungsi ini!)
        # --- PERUBAHAN WARNA: Bagian Tambah Lagu ---
        self.admin_add_frame = ctk.CTkFrame(self.content_frame, fg_color=self.COLOR_PALETTE["card_bg"])
        self.admin_add_frame.pack(fill="x", padx=10, pady=10)
        self.admin_add_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.admin_add_frame, text="Tambah Lagu Baru", font=ctk.CTkFont(size=16, weight="bold")).grid(
            row=0, column=0, columnspan=2, pady=10)

        ctk.CTkLabel(self.admin_add_frame, text="ID Lagu", text_color=self.COLOR_PALETTE["text_primary"]).grid(row=1,
                                                                                                               column=0,
                                                                                                               padx=10,
                                                                                                               pady=5,
                                                                                                               sticky="w")
        self.admin_entry_id = ctk.CTkEntry(self.admin_add_frame, placeholder_text="cth: S007",
                                           fg_color=self.COLOR_PALETTE["card_hover"],
                                           border_color=self.COLOR_PALETTE["card_hover"])
        self.admin_entry_id.grid(row=1, column=1, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(self.admin_add_frame, text="Judul", text_color=self.COLOR_PALETTE["text_primary"]).grid(row=2,
                                                                                                             column=0,
                                                                                                             padx=10,
                                                                                                             pady=5,
                                                                                                             sticky="w")
        self.admin_entry_title = ctk.CTkEntry(self.admin_add_frame, placeholder_text="Judul Lagu",
                                              fg_color=self.COLOR_PALETTE["card_hover"],
                                              border_color=self.COLOR_PALETTE["card_hover"])
        self.admin_entry_title.grid(row=2, column=1, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(self.admin_add_frame, text="Artis", text_color=self.COLOR_PALETTE["text_primary"]).grid(row=3,
                                                                                                             column=0,
                                                                                                             padx=10,
                                                                                                             pady=5,
                                                                                                             sticky="w")
        self.admin_entry_artist = ctk.CTkEntry(self.admin_add_frame, placeholder_text="Nama Artis",
                                               fg_color=self.COLOR_PALETTE["card_hover"],
                                               border_color=self.COLOR_PALETTE["card_hover"])
        self.admin_entry_artist.grid(row=3, column=1, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(self.admin_add_frame, text="Album", text_color=self.COLOR_PALETTE["text_primary"]).grid(row=4,
                                                                                                             column=0,
                                                                                                             padx=10,
                                                                                                             pady=5,
                                                                                                             sticky="w")
        self.admin_entry_album = ctk.CTkEntry(self.admin_add_frame, placeholder_text="Nama Album",
                                              fg_color=self.COLOR_PALETTE["card_hover"],
                                              border_color=self.COLOR_PALETTE["card_hover"])
        self.admin_entry_album.grid(row=4, column=1, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(self.admin_add_frame, text="Genre", text_color=self.COLOR_PALETTE["text_primary"]).grid(row=5,
                                                                                                             column=0,
                                                                                                             padx=10,
                                                                                                             pady=5,
                                                                                                             sticky="w")
        self.admin_entry_genre = ctk.CTkEntry(self.admin_add_frame, placeholder_text="Pop/Rock/R&B",
                                              fg_color=self.COLOR_PALETTE["card_hover"],
                                              border_color=self.COLOR_PALETTE["card_hover"])
        self.admin_entry_genre.grid(row=5, column=1, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(self.admin_add_frame, text="File Audio", text_color=self.COLOR_PALETTE["text_primary"]).grid(row=6,
                                                                                                                  column=0,
                                                                                                                  padx=10,
                                                                                                                  pady=5,
                                                                                                                  sticky="w")
        self.admin_browse_button = ctk.CTkButton(self.admin_add_frame, text="Pilih File Audio...",
                                                 command=self.browse_file, fg_color = self.COLOR_PALETTE["accent_pink"], hover_color = self.COLOR_PALETTE["card_hover"]  )
        self.admin_browse_button.grid(row=6, column=1, padx=10, pady=5, sticky="ew")
        self.admin_file_path_label = ctk.CTkLabel(self.admin_add_frame, textvariable=self.admin_file_path_var,
                                                  text_color=self.COLOR_PALETTE["text_secondary"], wraplength=350)
        self.admin_file_path_label.grid(row=7, column=0, columnspan=2, padx=10, pady=5)

        ctk.CTkLabel(self.admin_add_frame, text="File Gambar", text_color=self.COLOR_PALETTE["text_primary"]).grid(
            row=8, column=0, padx=10, pady=5, sticky="w")
        self.admin_browse_image_button = ctk.CTkButton(self.admin_add_frame, text="Pilih Gambar Sampul...",
                                                       command=self.browse_image, fg_color = self.COLOR_PALETTE["accent_pink"], hover_color = self.COLOR_PALETTE["card_hover"])
        self.admin_browse_image_button.grid(row=8, column=1, padx=10, pady=5, sticky="ew")
        self.admin_image_path_label = ctk.CTkLabel(self.admin_add_frame, textvariable=self.admin_image_path_var,
                                                   text_color=self.COLOR_PALETTE["text_secondary"], wraplength=350)
        self.admin_image_path_label.grid(row=9, column=0, columnspan=2, padx=10, pady=5)

        self.admin_save_button = ctk.CTkButton(self.admin_add_frame, text="Simpan Lagu", fg_color = self.COLOR_PALETTE["accent_pink"], hover_color = self.COLOR_PALETTE["card_hover"],command=self.on_save_song)
        self.admin_save_button.grid(row=10, column=0, columnspan=2, padx=10, pady=20)

        self.admin_status_label = ctk.CTkLabel(self.admin_add_frame, text="",
                                               text_color=self.COLOR_PALETTE["text_secondary"])
        self.admin_status_label.grid(row=11, column=0, columnspan=2, padx=10, pady=5)

        # --- PERUBAHAN WARNA: Bagian Edit/Hapus Lagu ---
        self.admin_edit_frame = ctk.CTkFrame(self.content_frame, fg_color=self.COLOR_PALETTE["card_bg"])
        self.admin_edit_frame.pack(fill="x", padx=10, pady=10)
        self.admin_edit_frame.grid_columnconfigure(1, weight=1)

        ctk.CTkLabel(self.admin_edit_frame, text="Edit Lagu", font=ctk.CTkFont(size=16, weight="bold")).grid(
            row=0, column=0, columnspan=2, pady=10)

        search_frame = ctk.CTkFrame(self.admin_edit_frame, fg_color="transparent")
        search_frame.grid(row=1, column=0, columnspan=2, padx=10, pady=5, sticky="ew")
        search_frame.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(search_frame, text="Cari Lagu", text_color=self.COLOR_PALETTE["text_primary"]).grid(row=0,
                                                                                                            column=0,
                                                                                                            padx=(0,
                                                                                                                  10))
        self.admin_edit_search_entry = ctk.CTkEntry(search_frame,
                                                    placeholder_text="Cari berdasarkan id, judul, album, genre... ",
                                                    fg_color=self.COLOR_PALETTE["card_hover"],
                                                    border_color=self.COLOR_PALETTE["card_hover"])
        self.admin_edit_search_entry.grid(row=0, column=1, sticky="ew")
        self.admin_edit_load_button = ctk.CTkButton(search_frame, text="Search", fg_color = self.COLOR_PALETTE["accent_pink"], hover_color = self.COLOR_PALETTE["card_hover"],width=60,
                                                    command=self.on_admin_load_song)
        self.admin_edit_load_button.grid(row=0, column=2, padx=(10, 0))

        ctk.CTkLabel(self.admin_edit_frame, text="Judul", text_color=self.COLOR_PALETTE["text_primary"]).grid(row=2,
                                                                                                              column=0,
                                                                                                              padx=10,
                                                                                                              pady=5,
                                                                                                              sticky="w")
        self.admin_edit_title = ctk.CTkEntry(self.admin_edit_frame, state="disabled",
                                             fg_color=self.COLOR_PALETTE["card_hover"],
                                             border_color=self.COLOR_PALETTE["card_hover"])
        self.admin_edit_title.grid(row=2, column=1, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(self.admin_edit_frame, text="Artis", text_color=self.COLOR_PALETTE["text_primary"]).grid(row=3,
                                                                                                              column=0,
                                                                                                              padx=10,
                                                                                                              pady=5,
                                                                                                              sticky="w")
        self.admin_edit_artist = ctk.CTkEntry(self.admin_edit_frame, state="disabled",
                                              fg_color=self.COLOR_PALETTE["card_hover"],
                                              border_color=self.COLOR_PALETTE["card_hover"])
        self.admin_edit_artist.grid(row=3, column=1, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(self.admin_edit_frame, text="Album", text_color=self.COLOR_PALETTE["text_primary"]).grid(row=4,
                                                                                                              column=0,
                                                                                                              padx=10,
                                                                                                              pady=5,
                                                                                                              sticky="w")
        self.admin_edit_album = ctk.CTkEntry(self.admin_edit_frame, state="disabled",
                                             fg_color=self.COLOR_PALETTE["card_hover"],
                                             border_color=self.COLOR_PALETTE["card_hover"])
        self.admin_edit_album.grid(row=4, column=1, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(self.admin_edit_frame, text="Genre", text_color=self.COLOR_PALETTE["text_primary"]).grid(row=5,
                                                                                                              column=0,
                                                                                                              padx=10,
                                                                                                              pady=5,
                                                                                                              sticky="w")
        self.admin_edit_genre = ctk.CTkEntry(self.admin_edit_frame, state="disabled",
                                             fg_color=self.COLOR_PALETTE["card_hover"],
                                             border_color=self.COLOR_PALETTE["card_hover"])
        self.admin_edit_genre.grid(row=5, column=1, padx=10, pady=5, sticky="ew")

        ctk.CTkLabel(self.admin_edit_frame, text="Gambar Baru", text_color=self.COLOR_PALETTE["text_primary"]).grid(
            row=6, column=0, padx=10, pady=5, sticky="w")
        self.admin_edit_browse_img_btn = ctk.CTkButton(self.admin_edit_frame, text="Pilih Gambar Baru (Opsional)...",fg_color = self.COLOR_PALETTE["accent_pink"], hover_color = self.COLOR_PALETTE["card_hover"],
                                                       command=self.browse_edit_image, state="disabled")
        self.admin_edit_browse_img_btn.grid(row=6, column=1, padx=10, pady=5, sticky="ew")

        self.admin_edit_image_path_label = ctk.CTkLabel(self.admin_edit_frame,
                                                        textvariable=self.admin_edit_image_path_var,
                                                        text_color=self.COLOR_PALETTE["text_secondary"],
                                                        wraplength=350)
        self.admin_edit_image_path_label.grid(row=7, column=0, columnspan=2, padx=10, pady=5)

        edit_button_frame = ctk.CTkFrame(self.admin_edit_frame, fg_color="transparent")
        edit_button_frame.grid(row=8, column=0, columnspan=2, padx=10, pady=20, sticky="ew")
        edit_button_frame.grid_columnconfigure(0, weight=1)
        edit_button_frame.grid_columnconfigure(1, weight=1)

        self.admin_edit_update_button = ctk.CTkButton(edit_button_frame, text="Perbarui Lagu",fg_color = self.COLOR_PALETTE["accent_pink"], hover_color = self.COLOR_PALETTE["card_hover"],
                                                      command=self.on_admin_update_song, state="disabled")
        self.admin_edit_update_button.grid(row=0, column=0, padx=5, sticky="ew")

        self.admin_edit_delete_button = ctk.CTkButton(edit_button_frame, text="Hapus Lagu Ini",
                                                      command=self.on_admin_delete_song,fg_color = self.COLOR_PALETTE["window_bg"], hover_color = self.COLOR_PALETTE["card_hover"]
                                                      , state="disabled")
        self.admin_edit_delete_button.grid(row=0, column=1, padx=5, sticky="ew")

        self.admin_edit_status_label = ctk.CTkLabel(self.admin_edit_frame, text="",
                                                    text_color=self.COLOR_PALETTE["text_secondary"])
        self.admin_edit_status_label.grid(row=9, column=0, columnspan=2, padx=10, pady=5)

    def show_settings(self):
        self._reset_sidebar_buttons()
        self.setting_button.configure(fg_color=self.COLOR_PALETTE["accent_blue"], text_color="#FFFFFF")  # Atur ke Aktif

        self.clear_content_frame()
        self.main_title_label.configure(text="Profile Settings")

        # --- PERUBAHAN: Ganti warna frame ---
        settings_frame = ctk.CTkFrame(self.content_frame, fg_color=self.COLOR_PALETTE["card_bg"])
        settings_frame.pack(fill="x", padx=10, pady=10)

        basic_info_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        basic_info_frame.pack(fill="x", padx=20, pady=20)

        # --- PERUBAHAN: Ganti warna label ---
        ctk.CTkLabel(basic_info_frame, text="Basic Information", font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=self.COLOR_PALETTE["text_primary"]).pack(anchor="w")

        ctk.CTkLabel(basic_info_frame, text="Name", text_color=self.COLOR_PALETTE["text_secondary"]).pack(anchor="w",
                                                                                                          pady=(10, 0))

        # --- PERUBAHAN: Ganti warna entry field ---
        self.settings_name_entry = ctk.CTkEntry(basic_info_frame,
                                                fg_color=self.COLOR_PALETTE["card_hover"],
                                                text_color=self.COLOR_PALETTE["text_primary"],
                                                border_color=self.COLOR_PALETTE["card_hover"])
        self.settings_name_entry.insert(0, self.username_var.get())
        self.settings_name_entry.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(basic_info_frame, text="Mobile Number (Placeholder)",
                     text_color=self.COLOR_PALETTE["text_secondary"]).pack(anchor="w", pady=(10, 0))
        self.settings_mobile_entry = ctk.CTkEntry(basic_info_frame, placeholder_text="+1234567890", state="disabled",
                                                  fg_color=self.COLOR_PALETTE["card_hover"])
        self.settings_mobile_entry.pack(fill="x", pady=(0, 10))

        ctk.CTkLabel(basic_info_frame, text="Email ID (Placeholder)",
                     text_color=self.COLOR_PALETTE["text_secondary"]).pack(anchor="w", pady=(10, 0))
        self.settings_email_entry = ctk.CTkEntry(basic_info_frame, placeholder_text="user@example.com",
                                                 state="disabled", fg_color=self.COLOR_PALETTE["card_hover"])
        self.settings_email_entry.pack(fill="x", pady=(0, 10))

        # --- PERUBAHAN: Ganti warna tombol save ---
        save_btn = ctk.CTkButton(basic_info_frame, text="Save Changes", command=self.on_save_settings,
                                 fg_color=self.COLOR_PALETTE["accent_pink"],
                                 hover_color=self.COLOR_PALETTE["card_hover"])
        save_btn.pack(anchor="w", pady=20)

        self.settings_status_label = ctk.CTkLabel(basic_info_frame, text="")
        self.settings_status_label.pack(anchor="w", pady=5)

    def create_song_widget(self, parent_frame, song, context_playlist):
        # 1. Ganti warna frame
        song_frame = ctk.CTkFrame(parent_frame, fg_color=self.COLOR_PALETTE["card_bg"])
        song_frame.pack(fill="x", pady=5)
        song_frame.grid_columnconfigure(0, weight=1)

        info = f"{song.title} - {song.artist}"
        # 2. Ganti warna teks
        song_label = ctk.CTkLabel(song_frame, text=info, anchor="w", text_color=self.COLOR_PALETTE["text_primary"])
        song_label.grid(row=0, column=0, padx=10, pady=10, sticky="ew")

        is_favourite = song in self.player.favourite_playlist.view_songs()
        like_text = "❤" if is_favourite else "♡"
        # 3. Ganti warna tombol 'like'
        like_color = self.COLOR_PALETTE["accent_pink"] if is_favourite else self.COLOR_PALETTE["text_secondary"]

        like_btn = ctk.CTkButton(song_frame, text=like_text, width=30,
                                 fg_color="transparent",
                                 text_color=like_color,
                                 hover_color=self.COLOR_PALETTE["card_hover"],
                                 command=lambda s=song: self.on_toggle_favourite(s))
        like_btn.grid(row=0, column=1, padx=5)

        # 4. Ganti warna tombol 'Play'
        play_btn = ctk.CTkButton(song_frame, text="Play", width=60,
                                 fg_color=self.COLOR_PALETTE["accent_blue"],
                                 hover_color=self.COLOR_PALETTE["card_hover"],
                                 command=lambda s=song, p=context_playlist: self.on_play_song(s, context_playlist=p))
        play_btn.grid(row=0, column=2, padx=5)

        if context_playlist and context_playlist.name != "My Favourites":
            remove_btn = ctk.CTkButton(song_frame, text="X", width=30, fg_color="transparent", hover_color= self.COLOR_PALETTE["card_hover"],
                                       command=lambda s=song, p=context_playlist: self.on_remove_from_playlist(s, p))
            remove_btn.grid(row=0, column=3, padx=(0, 10))

    def create_song_card(self, parent_frame, song):
        # 1. Atur ukuran kartu agar lebih tinggi (sesuai logika proyek lama)
        card_width = 170
        card_height = 250  # 150 untuk gambar + 80 untuk teks/padding

        card = ctk.CTkFrame(parent_frame, width=card_width, height=card_height, corner_radius=20,
                            fg_color=self.COLOR_PALETTE["card_bg"])
        card.pack(side="left", padx=10, pady=10)

        # 2. Nonaktifkan propagasi (sesuai logika proyek lama)
        card.pack_propagate(False)

        # 3. Tombol Gambar (dulu img_label)
        img_size = (150, 130)  # Ukuran gambar tetap
        img = self.load_image_safe(song.image_path, img_size, is_placeholder=True)

        img_button = ctk.CTkButton(card, text="", image=img, fg_color="transparent",
                                   width=img_size[0], height=img_size[1],
                                   corner_radius=15,
                                   hover_color=self.COLOR_PALETTE["card_hover"],
                                   command=lambda s=song: self.on_play_song(s, context_playlist=None))
        # 4. Gunakan .pack(side="top") (sesuai logika proyek lama)
        img_button.pack(side="top", padx=10, pady=(10, 0))  # Beri jarak 10px dari tepi

        # 5. Frame Info (dulu info_frame)
        info_frame = ctk.CTkFrame(card, fg_color="transparent")
        # 6. Gunakan .pack(side="top") lagi (sesuai logika proyek lama)
        info_frame.pack(side="top", fill="x", expand=True, padx=10, pady=(5, 10))

        info_frame.grid_columnconfigure(0, weight=1)
        info_frame.grid_columnconfigure(1, weight=0)
        info_frame.grid_rowconfigure(0, weight=1)

        # Frame untuk Teks
        text_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        text_frame.grid(row=0, column=0, sticky="w")

        title = ctk.CTkLabel(text_frame, text=song.title, font=ctk.CTkFont(weight="bold"),
                             text_color=self.COLOR_PALETTE["text_primary"])
        title.pack(anchor="w")

        artist = ctk.CTkLabel(text_frame, text=song.artist, text_color=self.COLOR_PALETTE["text_secondary"],
                              font=ctk.CTkFont(size=12))
        artist.pack(anchor="w")

        # Tombol 'Like'
        is_favourite = song in self.player.favourite_playlist.view_songs()
        like_text = "❤" if is_favourite else "♡"
        like_color = self.COLOR_PALETTE["accent_pink"] if is_favourite else self.COLOR_PALETTE["text_secondary"]

        like_btn = ctk.CTkButton(info_frame, text=like_text, width=30, height=30,
                                 fg_color="transparent",
                                 text_color=like_color,
                                 hover=False,
                                 command=lambda s=song: self.on_toggle_favourite(s))
        like_btn.grid(row=0, column=1, sticky="e")

    # --- FUNGSI KONTROL (PENGHUBUNG GUI KE BACKEND) ---

    def on_save_settings(self):
        new_name = self.settings_name_entry.get()
        if not new_name:
            self.settings_status_label.configure(text="Nama tidak boleh kosong.", text_color="red")
            return
        success = self.player.set_username(new_name)
        if success:
            self.username_var.set(new_name)
            self.settings_status_label.configure(text="Nama berhasil diperbarui!", text_color="green")
        else:
            self.settings_status_label.configure(text="Gagal menyimpan nama.", text_color="red")

    def browse_file(self):
        file_path = ctk.filedialog.askopenfilename(
            title="Pilih File Audio",
            filetypes=[("Audio Files", "*.mp3 *.ogg *.wav"), ("All Files", "*.*")]
        )
        if file_path:
            self.admin_file_path_var.set(file_path)
            status_msg = "File dipilih."

            # --- BARU: Auto-Generate & Fill ID ---
            # Cek apakah kolom ID masih kosong. Jika ya, isi otomatis.
            if not self.admin_entry_id.get():
                existing_ids = [int(sid[1:]) for sid in self.player.song_library.keys() if
                                sid.startswith('S') and sid[1:].isdigit()]
                next_num = max(existing_ids) + 1 if existing_ids else 1
                new_id = f"S{next_num:03d}"

                self.admin_entry_id.delete(0, "end")
                self.admin_entry_id.insert(0, new_id)
                status_msg += f" ID Otomatis: {new_id}."
            # -------------------------------------

            # 1. Deteksi Durasi
            try:
                audio_info = None
                if file_path.endswith('.mp3'):
                    audio_info = MP3(file_path)
                elif file_path.endswith('.ogg'):
                    audio_info = OggVorbis(file_path)
                elif file_path.endswith('.wav'):
                    audio_info = WAVE(file_path)

                if audio_info:
                    self.admin_detected_duration = int(audio_info.info.length)
                    status_msg += f" Durasi: {self.admin_detected_duration}s."
            except Exception as e:
                print(f"Error baca durasi: {e}")
                self.admin_detected_duration = 0

            # 2. Auto-Fill Metadata (Khusus MP3)
            if file_path.endswith('.mp3'):
                try:
                    audio_tags = ID3(file_path)

                    # Ambil Teks
                    title = audio_tags.get("TIT2")
                    artist = audio_tags.get("TPE1")
                    album = audio_tags.get("TALB")
                    genre = audio_tags.get("TCON")

                    if title:
                        self.admin_entry_title.delete(0, "end")
                        self.admin_entry_title.insert(0, title.text[0])
                    if artist:
                        self.admin_entry_artist.delete(0, "end")
                        self.admin_entry_artist.insert(0, artist.text[0])
                    if album:
                        self.admin_entry_album.delete(0, "end")
                        self.admin_entry_album.insert(0, album.text[0])
                    if genre:
                        self.admin_entry_genre.delete(0, "end")
                        self.admin_entry_genre.insert(0, genre.text[0])

                    status_msg += " Teks terisi."

                    # Ambil Gambar
                    pict = None
                    for key in audio_tags.keys():
                        if key.startswith("APIC"):
                            pict = audio_tags[key]
                            break

                    if pict:
                        # Simpan gambar
                        folder = os.path.dirname(file_path)
                        base_name = os.path.splitext(os.path.basename(file_path))[0]
                        img_filename = f"{base_name}_cover.jpg"
                        img_path = os.path.join(folder, img_filename)

                        with open(img_path, "wb") as f:
                            f.write(pict.data)

                        self.admin_image_path_var.set(img_path)
                        status_msg += " Cover ditemukan!"
                    else:
                        status_msg += " (MP3 ini tidak punya Cover)"
                        self.admin_image_path_var.set("Belum ada gambar dipilih")

                except Exception as e:
                    print(f"Gagal ekstrak metadata: {e}")
                    status_msg += " Gagal baca metadata."

            self.admin_status_label.configure(text=status_msg, text_color="yellow")
    def browse_image(self):
        file_path = ctk.filedialog.askopenfilename(
            title="Pilih File Gambar",
            filetypes=[("Image Files", "*.png *.jpg *.jpeg"), ("All Files", "*.*")]
        )
        if file_path:
            self.admin_image_path_var.set(file_path)
            self.admin_status_label.configure(text="Gambar dipilih.", text_color="green")

    def browse_edit_image(self):
        file_path = ctk.filedialog.askopenfilename(
            title="Pilih File Gambar Baru",
            filetypes=[("Image Files", "*.png *.jpg *.jpeg"), ("All Files", "*.*")]
        )
        if file_path:
            self.admin_edit_image_path_var.set(file_path)
            self.admin_edit_status_label.configure(text="Gambar baru dipilih.", text_color="green")

    def on_save_song(self):
        try:
            s_id = self.admin_entry_id.get().strip()  # .strip() untuk hapus spasi tak sengaja
            title = self.admin_entry_title.get()
            artist = self.admin_entry_artist.get()
            album = self.admin_entry_album.get()
            genre = self.admin_entry_genre.get()
            file_path = self.admin_file_path_var.get()
            image_path = self.admin_image_path_var.get()
            duration = self.admin_detected_duration

            # Validasi Dasar (ID dan Gambar boleh kosong sekarang)
            if not all([title, artist, album, genre]):
                raise ValueError("Judul, Artis, Album, dan Genre harus diisi")

            if file_path == "Belum ada file dipilih":
                raise ValueError("File audio belum dipilih")

            # --- LOGIKA BARU: Handle Gambar Kosong ---
            # Jika user tidak memilih gambar, tapi ada file audio,
            # kita bisa pakai gambar default atau gambar hasil ekstraksi (jika ada).
            if image_path == "Belum ada gambar dipilih":
                # Cek apakah browse_file sudah berhasil ekstrak gambar sebelumnya?
                # (Biasanya browse_file sudah mengisi variabel ini jika ada cover art)
                # Jika masih kosong juga, gunakan placeholder atau biarkan backend menanganinya (misal string kosong)
                image_path = ""  # Atau path ke "default_cover.jpg" jika Anda punya

            if duration <= 0:
                raise ValueError("Durasi tidak valid (file mungkin rusak)")

        except ValueError as e:
            self.admin_status_label.configure(text=f"Error: {e}", text_color="red")
            return

        # Panggil backend (s_id bisa string kosong, backend akan generate)
        success = self.player.admin_add_song(s_id, title, artist, album, genre, duration, file_path, image_path)

        if success:
            self.admin_status_label.configure(text=f"Sukses: '{title}' ditambahkan!", text_color="green")

            # Reset Form
            self.admin_entry_id.delete(0, 'end')
            self.admin_entry_title.delete(0, 'end')
            self.admin_entry_artist.delete(0, 'end')
            self.admin_entry_album.delete(0, 'end')
            self.admin_entry_genre.delete(0, 'end')
            self.admin_file_path_var.set("Belum ada file dipilih")
            self.admin_image_path_var.set("Belum ada gambar dipilih")
            self.admin_detected_duration = 0

            self.refresh_current_view()
        else:
            self.admin_status_label.configure(text=f"Error: Gagal menyimpan lagu.", text_color="red")

    def on_admin_load_song(self):
        query = self.admin_edit_search_entry.get().strip()

        if not query:
            self.admin_edit_status_label.configure(text="Masukkan kata kunci pencarian.", text_color="red")
            return

        song = None

        # 1. Coba cari berdasarkan ID Persis
        song = self.player.get_song_by_id(query)

        # 2. Jika tidak ketemu, cari secara luas (ID case-insensitive, Judul, Artis, Album, Genre)
        if not song:
            query_lower = query.lower()
            for s in self.player.song_library.values():
                # Cek apakah query ada di dalam salah satu atribut lagu
                if (s.song_id.lower() == query_lower or
                        query_lower in s.title.lower() or
                        query_lower in s.artist.lower() or
                        query_lower in s.album.lower() or
                        query_lower in s.genre.lower()):
                    song = s
                    break  # Ambil yang pertama ketemu

        if song:
            self.loaded_song_id_to_edit = song.song_id  # Penting: Simpan ID aslinya

            self.admin_edit_title.configure(state="normal")
            self.admin_edit_artist.configure(state="normal")
            self.admin_edit_album.configure(state="normal")
            self.admin_edit_genre.configure(state="normal")
            self.admin_edit_browse_img_btn.configure(state="normal")

            self.admin_edit_title.delete(0, "end")
            self.admin_edit_title.insert(0, song.title)
            self.admin_edit_artist.delete(0, "end")
            self.admin_edit_artist.insert(0, song.artist)
            self.admin_edit_album.delete(0, "end")
            self.admin_edit_album.insert(0, song.album)
            self.admin_edit_genre.delete(0, "end")
            self.admin_edit_genre.insert(0, song.genre)

            self.admin_edit_image_path_var.set(song.image_path)

            self.admin_edit_update_button.configure(state="normal")
            self.admin_edit_delete_button.configure(state="normal")

            # Update pesan agar user tahu lagu mana yang ditemukan (berguna jika mencari berdasarkan genre)
            self.admin_edit_status_label.configure(text=f"Ditemukan: '{song.title}' (ID: {song.song_id})",
                                                   text_color="green")
        else:
            self.loaded_song_id_to_edit = None
            self.admin_edit_title.delete(0, "end")
            self.admin_edit_artist.delete(0, "end")
            self.admin_edit_album.delete(0, "end")
            self.admin_edit_genre.delete(0, "end")

            self.admin_edit_title.configure(state="disabled")
            self.admin_edit_artist.configure(state="disabled")
            self.admin_edit_album.configure(state="disabled")
            self.admin_edit_genre.configure(state="disabled")
            self.admin_edit_update_button.configure(state="disabled")
            self.admin_edit_delete_button.configure(state="disabled")

            self.admin_edit_image_path_var.set("Pilih gambar baru (opsional)")
            self.admin_edit_browse_img_btn.configure(state="disabled")

            self.admin_edit_status_label.configure(text=f"Lagu '{query}' tidak ditemukan.",
                                                   text_color="red")
    def on_admin_update_song(self):
        if not self.loaded_song_id_to_edit:
            self.admin_edit_status_label.configure(text="Error: Belum ada lagu dimuat.", text_color="red")
            return

        new_title = self.admin_edit_title.get()
        new_artist = self.admin_edit_artist.get()
        new_album = self.admin_edit_album.get()
        new_genre = self.admin_edit_genre.get()
        new_image_path = self.admin_edit_image_path_var.get()

        success = self.player.admin_update_song(
            self.loaded_song_id_to_edit,
            new_title, new_artist, new_album, new_genre, new_image_path
        )

        if success:
            self.admin_edit_status_label.configure(text=f"Lagu '{new_title}' berhasil diperbarui.", text_color="green")
            self.refresh_current_view()
        else:
            self.admin_edit_status_label.configure(text="Error: Gagal memperbarui lagu.", text_color="red")

    def on_admin_delete_song(self):
        if not self.loaded_song_id_to_edit:
            self.admin_edit_status_label.configure(text="Error: Belum ada lagu dimuat.", text_color="red")
            return

        song_id = self.loaded_song_id_to_edit
        song = self.player.get_song_by_id(song_id)

        success = self.player.admin_delete_song(song_id)

        if success:
            self.admin_edit_status_label.configure(text=f"Lagu '{song.title}' berhasil dihapus.", text_color="green")
            self.loaded_song_id_to_edit = None
            self.admin_edit_search_entry.delete(0, "end")
            self.admin_edit_title.delete(0, "end")
            self.admin_edit_artist.delete(0, "end")
            self.admin_edit_album.delete(0, "end")
            self.admin_edit_genre.delete(0, "end")

            self.admin_edit_title.configure(state="disabled")
            self.admin_edit_artist.configure(state="disabled")
            self.admin_edit_album.configure(state="disabled")
            self.admin_edit_genre.configure(state="disabled")
            self.admin_edit_update_button.configure(state="disabled")
            self.admin_edit_delete_button.configure(state="disabled")

            self.admin_edit_image_path_var.set("Pilih gambar baru (opsional)")
            self.admin_edit_browse_img_btn.configure(state="disabled")

            self.refresh_current_view()
        else:
            self.admin_edit_status_label.configure(text="Error: Gagal menghapus lagu.", text_color="red")

    def refresh_current_view(self):
        current_view = self.main_title_label.cget("text")

        if current_view == "Dashboard":
            self.show_dashboard()
        elif current_view == "All Songs in Library":
            self.show_library()
        elif current_view == "Search Results":
            self.on_search()
        elif current_view == "My Playlists":
            self.show_playlists()
        elif "Playlist:" in current_view:
            try:
                if isinstance(self.player.current_context, DoublyLinkedList):
                    self.show_playlist_songs(self.player.current_context)
                else:
                    self.show_dashboard()
            except Exception:
                self.show_dashboard()

        self.update_history_sidebar()
        self.update_player_ui()

    def open_add_to_playlist_window(self, song):
        if self.add_to_playlist_window is None or not self.add_to_playlist_window.winfo_exists():
            self.add_to_playlist_window = ctk.CTkToplevel(self)
            self.add_to_playlist_window.title("Add to Playlist")
            self.add_to_playlist_window.geometry("300x400")
            self.add_to_playlist_window.grab_set()
            label = ctk.CTkLabel(self.add_to_playlist_window, text=f"Add '{song.title}' to:",
                                 font=ctk.CTkFont(weight="bold"))
            label.pack(pady=10)
            scroll_frame = ctk.CTkScrollableFrame(self.add_to_playlist_window)
            scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
            playlists = self.player.user_playlists.values()
            if not playlists:
                ctk.CTkLabel(scroll_frame, text="Anda belum punya playlist.").pack(pady=10)
            for pl in playlists:
                btn = ctk.CTkButton(scroll_frame, text=pl.name,
                                    command=lambda s=song, p=pl: self.on_add_song_to_playlist(s, p))
                btn.pack(fill="x", pady=5)
        else:
            self.add_to_playlist_window.focus()

    def on_add_song_to_playlist(self, song, playlist):
        self.player.add_song_to_playlist(song, playlist.name)
        print(f"Added {song.title} to {playlist.name}")
        self.add_to_playlist_window.destroy()

    def on_genre_filter(self, genre):
        self.current_genre_filter = genre
        for g, btn in self.genre_buttons.items():
            if g == genre:
                btn.configure(fg_color=self.COLOR_PALETTE["accent_blue"])
            else:
                btn.configure(fg_color=self.COLOR_PALETTE["card_bg"])
        for widget in self.card_scroll_frame.winfo_children():
            widget.destroy()
        songs = self.player.get_songs_by_genre(genre)
        if not songs:
            ctk.CTkLabel(self.card_scroll_frame, text=f"Tidak ada lagu genre {genre}.").pack(side="left", padx=20)
            return
        for song in songs:
            self.create_song_card(self.card_scroll_frame, song)

    def on_search(self):
        self.clear_content_frame()
        self.main_title_label.configure(text="Search Results")
        query = self.search_entry.get()
        if not query: return
        results = self.player.user_search_song(query)
        if not results:
            ctk.CTkLabel(self.content_frame, text="Tidak ada hasil.").pack()
            return
        for song in results:
            self.create_song_widget(self.content_frame, song, context_playlist=None)

    def on_toggle_favourite(self, song):
        self.player.toggle_favourite(song)
        current_title = self.main_title_label.cget("text")
        if current_title == "All Songs in Library":
            self.show_library()
        elif current_title == "My Favourites":
            self.show_favourites()
        elif "Playlist:" in current_title:
            if isinstance(self.player.current_context, DoublyLinkedList):
                self.show_playlist_songs(self.player.current_context)
            else:
                self.show_library()
        elif current_title == "Dashboard":
            self.on_genre_filter(self.current_genre_filter)
        elif current_title == "Search Results":
            self.on_search()
        self.update_history_sidebar()

    def on_shuffle_click(self):
        is_active = self.player.toggle_shuffle()
        active_color = self.COLOR_PALETTE["accent_pink"]
        inactive_color = "transparent"
        text_secondary = self.COLOR_PALETTE["text_secondary"]

        if is_active:
            self.shuffle_button.configure(text="🔀", fg_color=inactive_color, text_color=active_color)
            self.np_shuffle_button.configure(text="🔀", fg_color=inactive_color, text_color=active_color)
        else:
            self.shuffle_button.configure(text="🔀", fg_color=inactive_color, text_color=text_secondary)
            self.np_shuffle_button.configure(text="🔀", fg_color=inactive_color, text_color=text_secondary)

    def on_repeat_click(self):
        mode = self.player.cycle_repeat_mode()

        # Warna aktif (Pink) vs Tidak aktif (Transparan/Secondary)
        active_color = self.COLOR_PALETTE["accent_pink"]
        inactive_color = "transparent"
        text_secondary = self.COLOR_PALETTE["text_secondary"]

        # Atur tampilan berdasarkan mode
        if mode == "none":
            # Mode Mati: Warna teks abu-abu, background transparan
            self.repeat_button.configure(text="🔁", fg_color=inactive_color, text_color=text_secondary)
            self.np_repeat_button.configure(text="🔁", fg_color=inactive_color, text_color=text_secondary)
            print("Repeat Mode: Off")

        elif mode == "all":
            # Mode Ulang Semua (Playlist): Warna teks Pink, background transparan
            self.repeat_button.configure(text="🔁", fg_color=inactive_color, text_color=active_color)
            self.np_repeat_button.configure(text="🔁", fg_color=inactive_color, text_color=active_color)
            print("Repeat Mode: All")

        elif mode == "one":
            # Mode Ulang Satu (Lagu Ini): Ikon ada angka '1', Warna teks Pink
            self.repeat_button.configure(text="🔂", fg_color=inactive_color, text_color=active_color)
            self.np_repeat_button.configure(text="🔂", fg_color=inactive_color, text_color=active_color)
            print("Repeat Mode: One Song")
    def on_create_playlist(self):
        name = self.playlist_entry.get()
        success, message = self.player.user_create_playlist(name)
        if success:
            self.playlist_status_label.configure(text=message, text_color="green")
            self.playlist_entry.delete(0, 'end')
            self.show_playlists()
        else:
            self.playlist_status_label.configure(text=message, text_color="red")

    def on_remove_from_playlist(self, song, playlist):
        self.player.remove_song_from_playlist(song, playlist.name)
        self.show_playlist_songs(playlist)
        if self.player.current_song == song and self.player.current_context == playlist:
            self.player.stop_song()
            self.player.current_song = None
            self.player.current_context = None
            self.update_player_ui()

    def on_play_song(self, song_object, context_playlist=None):
        self.player.play_song(song_object, context_playlist=context_playlist)
        self.current_lyrics = None
        self.current_lyric_times = []
        self.np_lyrics_label.configure(text="Searching lyrics...")  # Tanda loading

        # Panggil download di background
        self.player.download_lyrics_background(song_object)
        self.slider.set(0)
        self.np_slider.set(0)
        self.update_player_ui()
        self.update_history_sidebar()

    def on_play_pause_click(self):
        current_time = self.player.get_current_playback_time()
        self.player.stop_song()
        if not self.player.is_playing:
            self.player.current_seek_time = current_time
        self.update_player_ui()

    def on_next_click(self):
        self.player.play_next_song()
        self.slider.set(0)
        self.np_slider.set(0)
        self.update_player_ui()
        self.update_history_sidebar()

    def on_prev_click(self):
        self.player.play_prev_song()
        self.slider.set(0)
        self.np_slider.set(0)
        self.update_player_ui()
        self.update_history_sidebar()

    def update_player_ui(self):
        # Tentukan warna tombol play/pause
        btn_fg = self.COLOR_PALETTE["accent_blue"]
        btn_text_color = self.COLOR_PALETTE["text_secondary"]  # Warna gelap

        if not self.player.current_song:
            self.player_song_title.configure(text="Not Playing")
            self.player_song_artist.configure(text="---", text_color=self.COLOR_PALETTE["text_secondary"])
            self.np_title_label.configure(text="Not Playing")
            self.np_artist_label.configure(text="---", text_color=self.COLOR_PALETTE["text_secondary"])

            # Perbarui label album (pastikan ada di objek)
            if hasattr(self, 'np_album_label'):
                self.np_album_label.configure(text="---", text_color=self.COLOR_PALETTE["text_secondary"])

            self.play_button.configure(text="▶", fg_color=btn_fg, text_color=btn_text_color)
            self.np_play_button.configure(text="▶", fg_color=btn_fg, text_color=btn_text_color)

            self.time_start_label.configure(text="00:00")
            self.time_end_label.configure(text="00:00")
            self.np_time_start_label.configure(text="00:00")
            self.np_time_end_label.configure(text="00:00")

            self.slider.set(0)
            self.np_slider.set(0)

            self.album_art_button.configure(image=self.default_art_image_small, text="Art")
            self.np_art_label.configure(image=self.default_art_image_large, text="Album Art")
            return

        song = self.player.current_song

        small_img = self.load_image_safe(song.image_path, (80, 80))
        large_img = self.load_image_safe(song.image_path, (400, 400))

        self.player_song_title.configure(text=song.title)
        self.player_song_artist.configure(text=song.artist, text_color=self.COLOR_PALETTE["text_secondary"])
        self.np_title_label.configure(text=song.title)
        self.np_artist_label.configure(text=song.artist, text_color=self.COLOR_PALETTE["text_secondary"])

        if hasattr(self, 'np_album_label'):
            self.np_album_label.configure(text=song.album, text_color=self.COLOR_PALETTE["text_secondary"])

        self.album_art_button.configure(image=small_img, text="")
        self.np_art_label.configure(image=large_img, text="")

        total_duration = song.duration_seconds
        total_duration_str = self.format_time(total_duration)
        self.time_end_label.configure(text=total_duration_str)
        self.np_time_end_label.configure(text=total_duration_str)

        if self.player.is_playing:
            self.play_button.configure(text="||", fg_color=btn_fg, font=ctk.CTkFont(size = 20, weight="bold"),text_color=btn_text_color)
            self.np_play_button.configure(text="||", fg_color=btn_fg,font=ctk.CTkFont(size = 20, weight="bold"), text_color=btn_text_color)
        else:
            self.play_button.configure(text="▶", fg_color=btn_fg,font=ctk.CTkFont(size = 20, weight="bold"), text_color=btn_text_color)
            self.np_play_button.configure(text="▶", fg_color=btn_fg,font=ctk.CTkFont(size = 20, weight="bold"), text_color=btn_text_color)

    def open_library_song_selector(self, target_playlist):
        """Membuka jendela baru untuk memilih lagu dari library untuk ditambahkan."""

        # Cek jika jendela sudah ada
        if hasattr(self,
                   'library_song_selector') and self.library_song_selector is not None and self.library_song_selector.winfo_exists():
            self.library_song_selector.focus()
            return

        self.library_song_selector = ctk.CTkToplevel(self)
        self.library_song_selector.title(f"Tambah ke Playlist: {target_playlist.name}")
        self.library_song_selector.geometry("600x600")
        self.library_song_selector.grab_set()

        ctk.CTkLabel(self.library_song_selector,
                     text="Pilih Lagu yang Belum Ada di Playlist",
                     font=ctk.CTkFont(size=16, weight="bold"),
                     text_color=self.COLOR_PALETTE["text_primary"]).pack(pady=10)

        scroll_frame = ctk.CTkScrollableFrame(self.library_song_selector, fg_color="transparent")
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        scroll_frame.grid_columnconfigure(0, weight=1)

        all_songs = list(self.player.song_library.values())
        if not all_songs:
            ctk.CTkLabel(scroll_frame, text="Library kosong.").pack(pady=20)
            return

        current_song_ids = {song.song_id for song in target_playlist.view_songs()}

        for i, song in enumerate(all_songs):
            is_in_playlist = song.song_id in current_song_ids

            song_item = ctk.CTkFrame(scroll_frame, fg_color=self.COLOR_PALETTE["card_bg"])
            song_item.grid(row=i, column=0, sticky="ew", pady=3)
            song_item.grid_columnconfigure(1, weight=1)  # Kolom info lagu

            # Gambar
            img = self.load_image_safe(song.image_path, (40, 40))
            ctk.CTkLabel(song_item, text="", image=img).grid(row=0, column=0, rowspan=2, padx=10, pady=5)

            # Info Lagu
            title_label = ctk.CTkLabel(song_item, text=song.title, font=ctk.CTkFont(weight="bold"), anchor="w",
                                       text_color=self.COLOR_PALETTE["text_primary"])
            title_label.grid(row=0, column=1, sticky="w", padx=5)
            artist_label = ctk.CTkLabel(song_item, text=song.artist, text_color=self.COLOR_PALETTE["text_secondary"],
                                        anchor="w", font=ctk.CTkFont(size=12))
            artist_label.grid(row=1, column=1, sticky="w", padx=5)

            # --- BARU: Tombol 'Like' ---
            is_favourite = song in self.player.favourite_playlist.view_songs()
            like_text = "❤️" if is_favourite else "♡"
            like_color = self.COLOR_PALETTE["accent_pink"] if is_favourite else self.COLOR_PALETTE["text_secondary"]

            like_btn = ctk.CTkButton(song_item, text=like_text, width=30, height=30,
                                     fg_color="transparent",
                                     text_color=like_color,
                                     hover=False,
                                     command=lambda s=song, p=target_playlist: self.on_toggle_favourite_from_selector(s,
                                                                                                                      p))
            like_btn.grid(row=0, column=2, rowspan=2, padx=5)
            # --- Akhir Tombol 'Like' ---

            # Tombol Tambah
            if is_in_playlist:
                btn_text = "Sudah Ditambahkan"
                btn_state = "disabled"
            else:
                btn_text = "Tambahkan"
                btn_state = "normal"

            add_btn = ctk.CTkButton(song_item, text=btn_text, width=100, state=btn_state,
                                    fg_color=self.COLOR_PALETTE["accent_pink"],
                                    hover_color=self.COLOR_PALETTE["card_hover"],
                                    command=lambda s=song, p=target_playlist: self.on_song_select_and_add(s, p))
            add_btn.grid(row=0, column=3, rowspan=2, padx=10)  # Dipindah ke kolom 3

            # Teks ID (opsional untuk debug)
            id_label = ctk.CTkLabel(song_item, text=song.song_id, text_color=self.COLOR_PALETTE["text_secondary"],
                                    font=ctk.CTkFont(size=10))
            id_label.grid(row=0, column=4, rowspan=2, padx=10)  # Dipindah ke kolom 4

    def on_toggle_favourite_from_selector(self, song, target_playlist):
        """Menjalankan toggle favorit dan me-refresh jendela pop-up."""

        # 1. Toggle favorit di backend (ini akan save data)
        self.player.toggle_favourite(song)

        # 2. Refresh tampilan utama di background (agar 'My Favourites' update)
        self.refresh_current_view()

        # 3. Tutup dan buka kembali jendela selector untuk me-refresh
        #    status tombol "like" di dalamnya.
        if hasattr(self, 'library_song_selector') and self.library_song_selector.winfo_exists():
            self.library_song_selector.destroy()
        self.open_library_song_selector(target_playlist)
    def on_song_select_and_add(self, song, target_playlist):
        """Menambahkan lagu yang dipilih dari selector ke playlist target."""
        self.player.add_song_to_playlist(song, target_playlist.name)

        # Refresh tampilan playlist saat ini
        self.show_playlist_songs(target_playlist)

        # Tutup dan Refresh selector (agar tombol "Tambahkan" berubah menjadi "Sudah Ditambahkan")
        self.library_song_selector.destroy()


if __name__ == "__main__":
    app = App()
    app.mainloop()