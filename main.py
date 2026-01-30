#Youtube Video Downloader

#imports
import os
import sys
import re
import tkinter as tk
from tkinter import ttk, messagebox
from yt_dlp import YoutubeDL
import subprocess
import threading


# 🧼 Sanitize file name for Windows
def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "", name)

# 📁 Open folder
def open_folder(path):
    path = os.path.abspath(path)
    if sys.platform == "win32":
        subprocess.run(["explorer", path])
    elif sys.platform == "darwin":
        subprocess.run(["open", path])
    else:
        subprocess.run(["xdg-open", path])

# 🔁 Download logic in thread
def start_download():
    url = url_entry.get()
    format_choice = format_var.get()
    selected_quality = quality_var.get()

    if not url:
        messagebox.showerror("Error", "Please enter a valid URL")
        return

    # 🧹 Reset UI
    download_btn.config(state="disabled")
    open_btn.config(state="disabled")
    status_label.config(text="Starting download...", fg="blue")
    progress_bar["value"] = 0
    window.update_idletasks()

    try:
        # ⏳ Get title
        with YoutubeDL() as ydl:
            info = ydl.extract_info(url, download=False)
            title = sanitize_filename(info.get("title", "video"))
            ext = "mp3" if format_choice == "Audio (MP3)" else "mp4"

        out_dir = os.path.join("downloads", "audio" if format_choice == "Audio (MP3)" else "video")
        os.makedirs(out_dir, exist_ok=True)
        output_template = os.path.join(out_dir, f"{title}.%(ext)s")

        def hook(d):
            if d['status'] == 'downloading':
                total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                downloaded = d.get('downloaded_bytes', 0)
                if total > 0:
                    percent = int((downloaded / total) * 100)
                    progress_bar["value"] = percent
                    window.update_idletasks()
            elif d['status'] == 'finished':
                status_label.config(text="Processing...", fg="orange")
                window.update_idletasks()

        ydl_opts = {
            "outtmpl": output_template,
            "progress_hooks": [hook],
            "quiet": True,
        }

        # 🔉 Audio Only
        if format_choice == "Audio (MP3)":
            ydl_opts.update({
                "format": "bestaudio/best",
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": selected_quality.rstrip(" kbps"),
                    },
                    {
                        "key": "EmbedThumbnail",
                    },
                ],
                "writethumbnail": True,
                "postprocessor_args": [
                    "-id3v2_version", "3"
                ],
            })

        # 🎞️ Video Only (no audio)
        elif format_choice == "Video (No Audio)":
            ydl_opts.update({
                "format": f"bestvideo[ext=mp4][height<={selected_quality.rstrip('p')}]"
            })

        # 🎬 Video + Audio
        elif format_choice == "Video + Audio":
            ydl_opts.update({
                "format": f"bestvideo[ext=mp4][height<={selected_quality.rstrip('p')}] + bestaudio[ext=m4a]/bestaudio",
                "merge_output_format": "mp4",
                "postprocessors": [{
                    "key": "FFmpegVideoConvertor",
                    "preferedformat": "mp4"
                }]
            })

        # 🧲 Run download
        with YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # ✅ Success
        progress_bar["value"] = 100
        status_label.config(text="✅ Download Complete", fg="green")
        open_btn.config(state="normal")
        global last_download_folder
        last_download_folder = out_dir
        url_entry.delete(0, tk.END)

    except Exception as e:
        print("Error:", e)
        status_label.config(text="❌ Download Failed", fg="red")
    finally:
        download_btn.config(state="normal")

# 👆 Start thread
def download():
    status_label.config(text="", fg="blue")
    progress_bar["value"] = 0
    open_btn.config(state="disabled")
    threading.Thread(target=start_download).start()

# 🔄 On format selection change
def on_format_change(event=None):
    selected_format = format_var.get()
    if selected_format == "Audio (MP3)":
        quality_label.config(text="Select Audio Quality:")
        quality_menu["values"] = ["128 kbps", "192 kbps", "320 kbps"]
        quality_var.set("192 kbps")
    else:
        quality_label.config(text="Select Max Video Quality:")
        quality_menu["values"] = ["144p", "240p", "360p", "480p", "720p", "1080p", "1440p", "2160p"]
        quality_var.set("1080p")

# 🎨 GUI Setup
window = tk.Tk()
window.title("Video Downloader")
window.geometry("460x320")  # Width x Height

tk.Label(window, text="Video URL:").pack(pady=5)
url_entry = tk.Entry(window, width=55)
url_entry.pack(pady=5)

tk.Label(window, text="Select Format:").pack()
format_var = tk.StringVar(value="Audio (MP3)")
format_menu = ttk.Combobox(window, textvariable=format_var, state="readonly",
                           values=["Audio (MP3)", "Video (No Audio)", "Video + Audio"])
format_menu.pack(pady=5)
format_menu.bind("<<ComboboxSelected>>", on_format_change)

quality_label = tk.Label(window, text="Select Quality:")
quality_label.pack()
quality_var = tk.StringVar()
quality_menu = ttk.Combobox(window, textvariable=quality_var, state="readonly")
quality_menu.pack(pady=3)

download_btn = tk.Button(window, text="Download", command=download, bg="blue", fg="white", width=20)
download_btn.pack(pady=10)

progress_bar = ttk.Progressbar(window, orient="horizontal", length=300, mode="determinate")
progress_bar.pack(pady=5)

status_label = tk.Label(window, text="")
status_label.pack(pady=5)

last_download_folder = ""
def show_folder():
    if last_download_folder:
        open_folder(last_download_folder)

open_btn = tk.Button(window, text="Show in Folder", command=show_folder, state="disabled")
open_btn.pack(pady=5)

# Initial quality options
on_format_change()

window.mainloop()
