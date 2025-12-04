Silakan Copy seluruh blok kode di bawah ini dan Paste ke dalam file README.md Anda.

Markdown

# 🎧 Oceanova: Modern Desktop Music Player

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![GUI](https://img.shields.io/badge/GUI-CustomTkinter-blueviolet)
![Status](https://img.shields.io/badge/Status-Completed-success)

**Oceanova** adalah aplikasi pemutar musik desktop modern yang dibangun menggunakan Python. Proyek ini dirancang sebagai implementasi nyata dari konsep **Struktur Data & Algoritma** dalam pengembangan perangkat lunak, menggabungkan efisiensi backend dengan antarmuka pengguna (UI/UX) yang elegan.

---

## 👥 Anggota Kelompok

| NIM | Nama Anggota | Peran |
| :--- | :--- | :--- |
| **[Isi NIM Disini]** | **[Nama Anggota 1]** | Lead Developer (Backend & Data Structures) |
| **[Isi NIM Disini]** | **[Nama Anggota 2]** | UI/UX Designer & Frontend (CustomTkinter) |
| **[Isi NIM Disini]** | **[Nama Anggota 3]** | Quality Assurance & Documentation |

---

## ✨ Fitur Unggulan

### 1. Keamanan & Peran Pengguna (User vs Admin)
Aplikasi memisahkan hak akses antara Pengguna biasa dan Admin.
* **User:** Hanya bisa memutar lagu, membuat playlist, dan mencari lagu.
* **Admin:** Memiliki akses penuh ke **Admin Panel** untuk manajemen data (CRUD).
* **Autentikasi:** Akses Admin dilindungi oleh sistem login berbasis sesi (Password Default: `admin`).

### 2. Implementasi Struktur Data Efisien
Kami tidak hanya menggunakan list biasa. Demi performa maksimal, kami menerapkan:
* **Hash Map (Dictionary):** Digunakan pada **Library Lagu**. Memungkinkan pencarian lagu berdasarkan ID atau Judul dengan kompleksitas waktu rata-rata **$O(1)$**.
* **Doubly Linked List (DLL):** Digunakan pada **Playlist**. Memungkinkan navigasi lagu (Next/Previous) yang sangat cepat dan fitur *circular traversal* (kembali ke awal setelah lagu terakhir).
* **Queue (Deque):** Digunakan pada fitur **Recently Played**. Menyimpan riwayat lagu terakhir dengan prinsip FIFO (*First In First Out*) yang efisien.

### 3. Pengalaman Audio Visual
* **Real-time Visualizer:** Visualisasi bar audio yang bergerak sesuai frekuensi musik.
* **Synced Lyrics:** Menampilkan lirik lagu secara otomatis yang tersinkronisasi (jika tersedia).
* **Smart Controls:** Fitur *Shuffle*, *Repeat One*, dan *Repeat All* yang berfungsi penuh.

---

## 🛠️ Teknologi yang Digunakan

* **Bahasa:** Python 3.x
* **GUI Framework:** CustomTkinter (Modern UI wrapper for Tkinter)
* **Audio Engine:** Pygame Mixer
* **Metadata Processing:** Mutagen (ID3 Tags Parsing)
* **Image Processing:** Pillow (PIL)
* **Lyrics:** Syncedlyrics

---

## ⚙️ Instalasi dan Cara Menjalankan

Ikuti langkah-langkah berikut untuk menjalankan aplikasi di komputer Anda:

### 1. Clone Repository
```bash
git clone [https://github.com/mokhammadbahauddin/Oceanova.git](https://github.com/mokhammadbahauddin/Oceanova.git)
cd Oceanova
2. Install Dependensi (Library)
Pastikan Python sudah terinstal, lalu jalankan perintah ini di terminal:



pip install customtkinter pygame mutagen Pillow syncedlyrics
3. Jalankan Aplikasi
Bash

python gui.py
📖 Panduan Penggunaan
Masuk sebagai Admin
Klik tombol 🛡️ Admin Panel di sidebar kiri bawah.

Akan muncul pop-up konfirmasi. Klik Yes.

Masukkan password: admin

Anda sekarang dapat Menambah, Mengedit, atau Menghapus lagu dari database.

Manajemen Playlist
Masuk ke menu 🎵 My Playlists.

Ketik nama playlist baru di kolom input, lalu klik Create.

Klik tombol View Songs pada playlist yang dibuat.

Klik + Tambah Lagu dari Library untuk memasukkan lagu.

📸 Screenshots
(Tempatkan screenshot aplikasi Anda di folder repository dan tautkan di sini untuk dokumentasi yang lebih baik)

Copyright © 2024 Kelompok Oceanova. All Rights Reserved.
