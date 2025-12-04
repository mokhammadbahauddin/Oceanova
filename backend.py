# Simpan file ini sebagai backend.py

import time
import random
from collections import deque
import pygame
import json
import os
import threading
import syncedlyrics

DATA_FILE = "music_data.json"


# ==============================================================================
# KELAS 1: SONG (Tipe Data Record)
# ==============================================================================
class Song:
    def __init__(self, song_id, title, artist, album, genre, duration_seconds, file_path,
                 image_path):
        self.song_id = song_id
        self.title = title
        self.artist = artist
        self.album = album
        self.genre = genre
        self.duration_seconds = duration_seconds
        self.file_path = file_path
        self.image_path = image_path
        self.playlist_nodes = []

    def __str__(self):
        mins = self.duration_seconds // 60
        secs = self.duration_seconds % 60
        return f"[{self.song_id}] {self.title} - {self.artist} ({self.album} / {self.genre}) - {mins:02}:{secs:02}"

    def update_details(self, title, artist, album, genre, image_path):
        self.title = title
        self.artist = artist
        self.album = album
        self.genre = genre
        self.image_path = image_path
        print(f"Info lagu '{self.song_id}' telah diupdate.")


# ==============================================================================
# KELAS 2 & 3: DATA STRUCTURE (Doubly Linked List)
# ==============================================================================
class Node:
    def __init__(self, song_object):
        self.song = song_object
        self.next = None
        self.prev = None


class DoublyLinkedList:
    def __init__(self, name):
        self.name = name
        self.head = None
        self.tail = None
        self.current_song_node = None

    def add_song(self, song_object):
        new_node = Node(song_object)
        if self.head is None:
            self.head = new_node
            self.tail = new_node
        else:
            self.tail.next = new_node
            new_node.prev = self.tail
            self.tail = new_node
        song_object.playlist_nodes.append(new_node)
        print(f"'{song_object.title}' ditambahkan ke playlist '{self.name}'.")

    def _remove_node(self, node_to_delete):
        if node_to_delete is None: return
        if self.current_song_node == node_to_delete: self.current_song_node = None
        if node_to_delete == self.head: self.head = node_to_delete.next
        if node_to_delete == self.tail: self.tail = node_to_delete.prev
        if node_to_delete.prev: node_to_delete.prev.next = node_to_delete.next
        if node_to_delete.next: node_to_delete.next.prev = node_to_delete.prev
        if node_to_delete in node_to_delete.song.playlist_nodes:
            node_to_delete.song.playlist_nodes.remove(node_to_delete)

    def remove_song_by_user(self, song_object):
        current = self.head
        node_to_remove = None
        while current:
            if current.song == song_object:
                node_to_remove = current
                break
            current = current.next
        if node_to_remove:
            self._remove_node(node_to_remove)
            print(f"'{song_object.title}' telah dihapus dari playlist '{self.name}'.")
        else:
            print(f"'{song_object.title}' tidak ditemukan di playlist ini.")

    def view_songs(self):
        songs = []
        current = self.head
        while current:
            songs.append(current.song)
            current = current.next
        return songs

    def find_node_by_song(self, song_object):
        current = self.head
        while current:
            if current.song == song_object:
                return current
            current = current.next
        return None

    def play_from_playlist(self):
        if self.head:
            self.current_song_node = self.head
            return self.current_song_node
        return None

    def play_next(self):
        if self.current_song_node:
            if self.current_song_node.next:
                # Jika ada lagu selanjutnya, maju
                self.current_song_node = self.current_song_node.next
            else:
                # Jika di akhir (ekor), lompat ke awal (kepala)
                self.current_song_node = self.head
            return self.current_song_node
        return None

    def play_prev(self):
        if self.current_song_node:
            if self.current_song_node.prev:
                # Jika ada lagu sebelumnya, mundur
                self.current_song_node = self.current_song_node.prev
            else:
                # Jika di awal (kepala), lompat ke akhir (ekor)
                self.current_song_node = self.tail
            return self.current_song_node
        return None


# ==============================================================================
# KELAS 4: MUSIC PLAYER (Controller Utama)
# ==============================================================================
class MusicPlayer:
    def __init__(self):
        pygame.mixer.init()
        self.song_library = {}
        self.user_playlists = {}
        self.favourite_playlist = DoublyLinkedList("My Favourites")
        self.is_shuffle = False
        self.repeat_mode = "none"
        self.current_song = None
        self.is_playing = False
        self.current_context = None
        self.recently_played_history = deque(maxlen=10)
        self.current_seek_time = 0.0
        self.start_time = 0.0  # Waktu saat tombol Play ditekan
        self.pause_start_time = 0.0  # Waktu saat tombol Pause ditekan
        self.username = "Mokhammad Bahauddin"
        self.beat_times = []  # Dihapus dari versi ini
        self.load_data()

    # --- FUNGSI SAVE/LOAD ---
    def load_data(self):
        if not os.path.exists(DATA_FILE):
            print("File data tidak ditemukan. Memulai dengan data kosong.")
            return
        try:
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
                self.username = data.get('username', 'Mokhammad Bahauddin')
                songs_data = data.get('songs', {})
                for song_id, details in songs_data.items():
                    song = Song(
                        song_id=song_id,
                        title=details.get('title'),
                        artist=details.get('artist'),
                        album=details.get('album'),
                        genre=details.get('genre'),
                        duration_seconds=details.get('duration_seconds'),
                        file_path=details.get('file_path'),
                        image_path=details.get('image_path')
                    )
                    self.song_library[song_id] = song

                playlists_data = data.get('playlists', {})
                fav_ids = playlists_data.get("My Favourites", [])
                for song_id in fav_ids:
                    song = self.song_library.get(song_id)
                    if song:
                        self.favourite_playlist.add_song(song)

                for name, song_ids in playlists_data.items():
                    if name == "My Favourites":
                        continue
                    dll = DoublyLinkedList(name)
                    self.user_playlists[name] = dll
                    for song_id in song_ids:
                        song = self.song_library.get(song_id)
                        if song:
                            dll.add_song(song)

            print("Data berhasil dimuat.")
        except Exception as e:
            print(f"Error memuat data: {e}. Memulai dengan data kosong.")
            self.song_library = {}
            self.user_playlists = {}
            self.favourite_playlist = DoublyLinkedList("My Favourites")
            self.username = "Mokhammad Bahauddin"

    def save_data(self):
        try:
            data_to_save = {
                'username': self.username,
                'songs': {},
                'playlists': {}
            }
            for song_id, song_obj in self.song_library.items():
                data_to_save['songs'][song_id] = {
                    'title': song_obj.title,
                    'artist': song_obj.artist,
                    'album': song_obj.album,
                    'genre': song_obj.genre,
                    'duration_seconds': song_obj.duration_seconds,
                    'file_path': song_obj.file_path,
                    'image_path': song_obj.image_path
                }
            data_to_save['playlists']["My Favourites"] = [song.song_id for song in self.favourite_playlist.view_songs()]
            for name, dll_obj in self.user_playlists.items():
                data_to_save['playlists'][name] = [song.song_id for song in dll_obj.view_songs()]

            with open(DATA_FILE, 'w') as f:
                json.dump(data_to_save, f, indent=4)
            print("Data berhasil disimpan.")
        except Exception as e:
            print(f"Error menyimpan data: {e}")

    # --- FUNGSI YANG DIPERBARUI ---
    def set_username(self, new_name):
        if new_name:
            self.username = new_name
            self.save_data()
            return True
        return False

    def admin_add_song(self, s_id, title, artist, album, genre, duration, file_path, image_path):
        # --- FITUR BARU: Auto-Generate ID jika kosong ---
        if not s_id:
            # Cari ID terakhir dan tambahkan 1
            existing_ids = [int(sid[1:]) for sid in self.song_library.keys() if
                            sid.startswith('S') and sid[1:].isdigit()]
            next_num = max(existing_ids) + 1 if existing_ids else 1
            s_id = f"S{next_num:03d}"
        # ------------------------------------------------

        if s_id in self.song_library:
            print(f"Error: ID Lagu '{s_id}' sudah ada.")
            return False

        if duration <= 0:
            print("Error: Durasi tidak valid.")
            return False

        new_song = Song(s_id, title, artist, album, genre, duration, file_path, image_path)
        self.song_library[s_id] = new_song
        self.save_data()
        print(f"Sukses! Lagu '{title}' ditambahkan dengan ID: {s_id}")
        return True
    def get_song_by_id(self, song_id):
        return self.song_library.get(song_id)

    def admin_update_song(self, song_id, title, artist, album, genre, image_path):
        song_to_update = self.get_song_by_id(song_id)
        if song_to_update:
            song_to_update.update_details(title, artist, album, genre, image_path)
            self.save_data()
            print(f"Lagu '{song_id}' berhasil diupdate.")
            return True
        print(f"Error: Lagu '{song_id}' tidak ditemukan untuk diupdate.")
        return False

    def admin_delete_song(self, song_id):
        song_to_delete = self.get_song_by_id(song_id)
        if not song_to_delete:
            print(f"Error: Lagu '{song_id}' tidak ditemukan.")
            return False

        nodes_to_remove = list(song_to_delete.playlist_nodes)

        fav_nodes = [node for node in nodes_to_remove if node in self.favourite_playlist.view_songs()]
        for node in fav_nodes:
            self.favourite_playlist._remove_node(node)

        for playlist in self.user_playlists.values():
            pl_nodes = [node for node in nodes_to_remove if node in playlist.view_songs()]
            for node in pl_nodes:
                playlist._remove_node(node)

        if self.current_song == song_to_delete:
            self.stop_song()
            self.current_song = None
            self.current_context = None

        self.song_library.pop(song_id, None)
        self.save_data()
        print(f"Sukses! Lagu '{song_to_delete.title}' telah dihapus sepenuhnya.")
        return True

    def user_create_playlist(self, playlist_name):
        if not playlist_name:
            return False, "Nama playlist tidak boleh kosong."
        if playlist_name in self.user_playlists:
            return False, f"Playlist '{playlist_name}' sudah ada."
        else:
            self.user_playlists[playlist_name] = DoublyLinkedList(playlist_name)
            self.save_data()
            return True, f"Playlist '{playlist_name}' dibuat."

    def add_song_to_playlist(self, song, playlist_name):
        playlist = self.user_playlists.get(playlist_name)
        if playlist:
            playlist.add_song(song)
            self.save_data()
            return True
        return False

    def remove_song_from_playlist(self, song, playlist_name):
        playlist = self.user_playlists.get(playlist_name)
        if playlist:
            playlist.remove_song_by_user(song)
            self.save_data()
            return True
        return False

    def toggle_favourite(self, song):
        is_favourite = False
        current = self.favourite_playlist.head
        while current:
            if current.song == song:
                is_favourite = True
                break
            current = current.next
        if is_favourite:
            self.favourite_playlist.remove_song_by_user(song)
        else:
            self.favourite_playlist.add_song(song)
        self.save_data()

        # --- DIPERBARUI: Fungsi Pencarian ---

    def user_search_song(self, query):
        results = []
        query_lower = query.lower()  # Untuk pencarian case-insensitive
        query_original = query  # Untuk pencocokan ID case-sensitive

        if not query:
            return []

        # 1. Prioritas Utama: Pencocokan ID Lagu (case-sensitive)
        song_by_id = self.get_song_by_id(query_original)
        if song_by_id:
            results.append(song_by_id)
            return results  # Jika ID cocok, kembalikan HANYA lagu itu

        # 2. Pencarian Luas (case-insensitive)
        for song in self.song_library.values():
            if (query_lower in song.title.lower() or
                    query_lower in song.artist.lower() or
                    query_lower in song.album.lower() or
                    query_lower in song.genre.lower()):  # <-- BARU: Ditambahkan pencarian genre
                results.append(song)
        return results

    def get_songs_by_genre(self, genre):
        if genre.lower() == "all":
            return list(self.song_library.values())
        results = []
        for song in self.song_library.values():
            if song.genre.lower() == genre.lower():
                results.append(song)
        return results

    def get_recently_played(self):
        unique_songs = []
        for song in reversed(self.recently_played_history):
            if song not in unique_songs:
                unique_songs.append(song)
        return unique_songs

    def toggle_shuffle(self):
        self.is_shuffle = not self.is_shuffle
        return self.is_shuffle

    def cycle_repeat_mode(self):
        if self.repeat_mode == "none":
            self.repeat_mode = "all"
        elif self.repeat_mode == "all":
            self.repeat_mode = "one"
        elif self.repeat_mode == "one":
            self.repeat_mode = "none"
        return self.repeat_mode

    def play_song(self, song, context_playlist=None):
        if not song.file_path or song.file_path == "dummy/path.mp3":
            print(f"Error: Tidak ada file audio valid untuk {song.title}")
            return

        self.current_seek_time = 0.0
        self.current_song = song
        self.is_playing = True
        try:
            pygame.mixer.music.load(song.file_path)
            pygame.mixer.music.play()

            # --- UPDATE INI ---
            self.current_seek_time = 0.0
            self.start_time = time.time()  # Catat waktu mulai
            self.is_playing = True
            print(f"▶️ Memutar: {song.title}")
        except Exception as e:
            print(f"Error memutar file {song.file_path}: {e}")
            self.is_playing = False
            return

        self.recently_played_history.append(song)
        if context_playlist:
            self.current_context = context_playlist
            node = context_playlist.find_node_by_song(song)
            if node:
                context_playlist.current_song_node = node
        else:
            self.current_context = 'library'

    def stop_song(self):
        if self.is_playing:
            # PAUSE
            pygame.mixer.music.pause()
            self.is_playing = False
            # Hitung sudah berapa lama lagu berjalan sebelum dipause
            # dan tambahkan ke seek_time
            self.current_seek_time += time.time() - self.start_time
            print(f"⏹️ Jeda: {self.current_song.title}")
        else:
            if self.current_song:
                # UNPAUSE
                pygame.mixer.music.unpause()
                self.is_playing = True
                # Reset start_time ke "sekarang"
                self.start_time = time.time()
                print(f"▶️ Melanjutkan: {self.current_song.title}")

    def seek_song(self, time_seconds):
        if not self.current_song: return
        try:
            pygame.mixer.music.play(start=time_seconds)
            # --- UPDATE INI ---
            self.current_seek_time = time_seconds  # Set posisi baru
            self.start_time = time.time()  # Reset waktu mulai

            if not self.is_playing:
                pygame.mixer.music.pause()
        except Exception as e:
            print(f"Error seeking MP3: {e}")

    def get_current_playback_time(self):
        if not self.current_song:
            return 0.0

        if self.is_playing:
            # Waktu total = (Waktu yang sudah tersimpan/seek) + (Waktu sejak tombol play ditekan)
            return self.current_seek_time + (time.time() - self.start_time)
        else:
            # Jika pause, cukup kembalikan waktu terakhir yang disimpan
            return self.current_seek_time

    # --- DIPERBARUI: Implementasi Lagu Mirip ---
    def _find_similar_song(self):
        """Mencari lagu yang mirip berdasarkan Artis, lalu Genre."""
        if not self.current_song:
            return None

        current_artist = self.current_song.artist
        current_genre = self.current_song.genre

        artist_matches = []
        genre_matches = []

        for song in self.song_library.values():
            if song == self.current_song:
                continue  # Jangan pilih lagu yang sama

            # Prioritas 1: Artis yang sama
            if song.artist == current_artist:
                artist_matches.append(song)
            # Prioritas 2: Genre yang sama
            elif song.genre == current_genre:
                genre_matches.append(song)

        if artist_matches:
            print(f"Menemukan lagu mirip (artis sama): {len(artist_matches)} lagu")
            return random.choice(artist_matches)
        elif genre_matches:
            print(f"Menemukan lagu mirip (genre sama): {len(genre_matches)} lagu")
            return random.choice(genre_matches)

        # Fallback jika tidak ada yang cocok
        print("Tidak ada lagu mirip ditemukan.")
        return None

    def play_next_song(self):
        if not self.current_song: return

        # 1. Mode Repeat One
        if self.repeat_mode == "one":
            print(f"Mengulang lagu: {self.current_song.title}")
            self.play_song(self.current_song, self.current_context)
            return

        # 2. Jika di dalam Playlist (Doubly Linked List)
        if isinstance(self.current_context, DoublyLinkedList):
            playlist = self.current_context
            next_node = None

            # 2a. Jika Shuffle aktif
            if self.is_shuffle:
                all_songs = playlist.view_songs()
                if not all_songs: self.is_playing = False; return
                random_song = random.choice(all_songs)
                self.play_song(random_song, context_playlist=playlist)
                return

            # 2b. Jika Shuffle non-aktif (mengikuti urutan DLL)
            next_node = playlist.play_next()
            if next_node:
                self.play_song(next_node.song, context_playlist=playlist)
            else:
                # Sampai di akhir playlist
                if self.repeat_mode == "all":
                    first_song_node = playlist.play_from_playlist()
                    if first_song_node:
                        self.play_song(first_song_node.song, context_playlist=playlist)
                else:
                    self.is_playing = False  # Berhenti di akhir playlist

        # 3. Jika di Library (bukan playlist)
        else:
            # 3a. Jika Shuffle aktif (prioritas)
            if self.is_shuffle:
                all_songs_list = list(self.song_library.values())
                if not all_songs_list: self.is_playing = False; return
                random_song = random.choice(all_songs_list)
                self.play_song(random_song, context_playlist=None)
                return

            # 3b. Jika Shuffle non-aktif (cari lagu mirip)
            similar_song = self._find_similar_song()  # <-- PANGGIL FUNGSI YANG DIPERBARUI
            if similar_song:
                self.play_song(similar_song, context_playlist=None)
            else:
                # Sesuai PDF[cite: 39], berhenti jika tidak ada yang mirip
                self.is_playing = False

    def play_prev_song(self):
        if not self.current_song: return

        # 1. Logika jika berada di dalam Playlist (tetap sama)
        if isinstance(self.current_context, DoublyLinkedList):
            if self.is_shuffle:
                all_songs = self.current_context.view_songs()
                if not all_songs: self.is_playing = False; return
                random_song = random.choice(all_songs)
                self.play_song(random_song, context_playlist=self.current_context)
                return

            # Urutan mundur sesuai linked list
            playlist = self.current_context
            prev_node = playlist.play_prev()
            if prev_node:
                self.play_song(prev_node.song, context_playlist=playlist)

        # 2. Logika jika di Library (Sesuai PDF: Cari Lagu Mirip)
        else:
            # Jika Shuffle aktif
            if self.is_shuffle:
                all_songs_list = list(self.song_library.values())
                if not all_songs_list: self.is_playing = False; return
                random_song = random.choice(all_songs_list)
                self.play_song(random_song, context_playlist=None)
                return

            # Jika Normal: Cari lagu mirip (sama seperti Next)
            # Sesuai instruksi: "next/prev akan memutar lagu yang mirip"
            similar_song = self._find_similar_song()
            if similar_song:
                self.play_song(similar_song, context_playlist=None)
                print(f"Prev (Mirip): Memutar {similar_song.title}")
            else:
                # Jika tidak ada lagu mirip, berhenti
                self.is_playing = False
        # --- FITUR BARU: Auto Download Lirik ---
    def download_lyrics_background(self, song):
        """Mencari dan mendownload lirik di background thread."""
        # Tentukan nama file lirik (sama dengan lagu tapi akhiran .lrc)
        lrc_path = os.path.splitext(song.file_path)[0] + ".lrc"

        # Jika file sudah ada, tidak perlu download
        if os.path.exists(lrc_path):
            print(f"Lirik sudah ada di: {lrc_path}")
            return

        def run_download():
            print(f"Mencari lirik untuk: {song.title} - {song.artist}...")
            try:
                # Cari lirik (format [mm:ss.xx] Lirik)
                search_term = f"{song.title} {song.artist}"
                lrc_content = syncedlyrics.search(search_term)

                if lrc_content:
                    with open(lrc_path, "w", encoding="utf-8") as f:
                        f.write(lrc_content)
                    print("Lirik berhasil didownload!")
                else:
                    print("Lirik tidak ditemukan.")
            except Exception as e:
                print(f"Gagal download lirik: {e}")

        # Jalankan di thread terpisah agar GUI tidak macet
        t = threading.Thread(target=run_download)
        t.daemon = True  # Agar thread mati saat aplikasi ditutup
        t.start()

    def parse_lyrics(self, audio_file_path):
        """Membaca file .lrc lokal dan mengubahnya jadi dictionary."""
        lrc_path = os.path.splitext(audio_file_path)[0] + ".lrc"

        if not os.path.exists(lrc_path):
            return None

        lyrics_data = {}
        try:
            with open(lrc_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith("[") and "]" in line:
                        # Ambil waktu: [00:12.50] -> 00:12.50
                        time_part = line[1:line.find("]")]
                        text_part = line[line.find("]") + 1:].strip()

                        if not text_part: continue  # Skip baris kosong

                        # Konversi ke detik
                        try:
                            min_sec = time_part.split(":")
                            seconds = int(min_sec[0]) * 60 + float(min_sec[1])
                            lyrics_data[seconds] = text_part
                        except:
                            continue

            # Urutkan berdasarkan waktu
            return dict(sorted(lyrics_data.items()))
        except Exception as e:
            print(f"Error baca lirik: {e}")
            return None

    def user_delete_playlist(self, playlist_name):
        """Deletes a playlist by name."""
        if playlist_name in self.user_playlists:
            del self.user_playlists[playlist_name]
            self.save_data()
            return True, f"Playlist '{playlist_name}' deleted."
        return False, f"Playlist '{playlist_name}' not found."