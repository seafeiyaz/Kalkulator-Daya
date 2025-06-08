# Kalkulator Rangkaian Listrik (Kalkulator Daya)

Aplikasi desktop yang dibuat dengan Python dan Tkinter untuk membantu menghitung dan menganalisis rangkaian listrik sederhana. Aplikasi ini menyediakan dua mode:
1. Input Manual: Menghitung variabel V, I, R, P dan juga total hambatan dari ekspresi rangkaian seri/paralel.
2. Input Visual: Merancang rangkaian secara visual dengan drag-and-drop komponen, lalu menganalisisnya secara otomatis.

![image](https://github.com/user-attachments/assets/15adb796-5ad7-471d-b15b-b71fd04405cf)

# What You Need
Aplikasi ini hanya membutuhkan Python 3 yang sudah terinstall. Library yang digunakan (tkinter, math, re) sudah termasuk dalam instalasi standar Python, jadi tidak perlu menginstall library tambahan.

Berikut adalah cara menginstall Python jika belum terinstall.

# Windows
1. Kunjungi situs web resmi Python di python.org/downloads/.
2. Unduh installer versi terbaru (misalnya, Python 3.12.4).
3. Jalankan file .exe yang sudah diunduh.
4. Klik "Install Now" dan ikuti prosesnya hingga selesai.

  *_*PENTING: Pada jendela instalasi pertama, pastikan Anda mencentang kotak "Add Python to PATH" di bagian bawah._*

# macOS
1. Kunjungi python.org/downloads/ dan unduh installer untuk macOS.
2. Jalankan file .pkg yang sudah diunduh.
3. Ikuti petunjuk di layar (klik "Continue", "Agree", "Install") untuk menyelesaikan instalasi.

# Linux
1. Buka terminal
``` bash
sudo apt update
sudo apt install python3 python3-tk
```

# Verifikasi Install
Untuk memastikan Python sudah terinstall dengan benar, buka Terminal atau Command Prompt dan ketik:
``` bash
python --version
```
Jika muncul Python 3.x.x, maka instalasi telah berhasil.

# Cara Menjalankan Program
Setelah Python terinstall, ikuti langkah-langkah berikut:
1. Simpan file kode dari proyek ini dengan nama ``Kalkulator Daya.py.``
2. Buka Terminal (di macOS/Linux) atau Command Prompt (di Windows).
3. Arahkan terminal ke direktori (folder) tempat Anda menyimpan file Kalkulator Daya.py.
4. Jalankan program dengan perintah di bawah ini:
``` bash
python "Kalkulator Daya.py"
```
