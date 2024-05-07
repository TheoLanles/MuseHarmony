import pygame
import tkinter as tk
import tkinter.filedialog
import os
import glob
from mutagen.flac import FLAC
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC
from PIL import Image, ImageTk
import io
import configparser
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from dark_title_bar import *
from threading import Thread
import time

# Initialize Pygame
pygame.mixer.init()

# Create a Tkinter window
fenetre = ttk.Window(themename='darkly')
fenetre.title("Lecteur de Musique")
fenetre.iconbitmap('res/logo.ico')

dark_title_bar(fenetre)

# Set a fixed size for the window
fenetre.geometry("900x510")

# Load the configuration file
config_file = "config/config.ini"
config = configparser.ConfigParser()
config.read(config_file)

# Get the music folder path from the configuration file
music_folder_path = config.get("settings", "music_folder_path", fallback=os.path.expanduser("~")) 

# Create a dropdown list to display the playlist
dropdown_list = tk.Listbox(fenetre, width=55, height=30)
dropdown_list.pack(side=tk.LEFT, padx=10, pady=6)

# Variable to store the playlist
playlist = []

# Variable to store the loop state (0: no loop, 1: loop)
loop_state = tk.IntVar(value=0)

# Variable to store the previous volume before muting
previous_volume = 1 # Initial volume level

# Function to load the library
def load_library():
    global playlist
    # Scan the directory and add all audio files to the playlist
    playlist = []
    for extension in ['*.flac', '*.mp3']:
        playlist.extend(glob.glob(os.path.join(music_folder_path, extension)))

    # Update the dropdown list
    dropdown_list.delete(0, tk.END)
    dropdown_list.insert(tk.END, *[os.path.basename(file) for file in playlist])

# Variable to store the file path of the audio file
file_path = None

# Variable to store the information about the current music
current_music_info = {"total_time": 0}

# Load the library at startup
load_library()

# Function to toggle loop state
def toggle_loop():
    global loop_state
    loop_state.set(not loop_state.get())
    loop_button.config(bootstyle="outline" if loop_state.get() else "default")
    play_music_loop()

# Function to start the application
def start_application():
    # Load the library in a separate thread
    load_thread = Thread(target=load_library)
    load_thread.start()
    
# Function to start playing the music either normally or in loop
def play_music_loop():
    if loop_state.get():
        pygame.mixer.music.set_endevent(pygame.constants.USEREVENT)
        pygame.mixer.music.play(-1)  # -1 will play the music in an infinite loop
    else:
        pygame.mixer.music.play()

DEFAULT_COVER_PATH = "res/default.png"
DEFAULT_STARTUP_IMAGE_PATH = "res/default.png" 

# Function to open an audio file
def open_file(path):
    global file_path, current_music_info
    file_path = path
    pygame.mixer.music.load(file_path)

    # Initialize total_time
    total_time = 0

      # Extract metadata from the audio file
    if file_path.endswith('.flac'):
        audio = FLAC(file_path)
        title = audio.tags.get('title', ['Unknown'])[0]
        artist = audio.tags.get('artist', ['Unknown'])[0]
        cover_art = audio.pictures
        total_time = audio.info.length
    elif file_path.endswith('.mp3'):
        audio = MP3(file_path)
        title = audio.get('TIT2', ['Unknown'])[0]
        artist = audio.get('TPE1', ['Unknown'])[0]
        cover_art = audio.tags.getall('APIC') if audio.tags.getall('APIC') else None
        total_time = audio.info.length
    else:
        title = ""
        artist = ""
        cover_art = None

    # Update total time if it is greater than zero
    if total_time > 0:
        current_music_info["total_time"] = total_time

    # Update the user interface
    label_title.config(text=title)
    label_artist.config(text=artist)
    if cover_art:
        image_data = cover_art[0].data
        image = Image.open(io.BytesIO(image_data))
    else:
        image = Image.open(DEFAULT_COVER_PATH)
    image = image.resize((300, 300))
    image_tk = ImageTk.PhotoImage(image)
    label_cover_art.config(image=image_tk)
    label_cover_art.image = image_tk

    # Set the progress bar to the beginning
    progress_bar['value'] = 0

    # Update the progress bar and time display
    update_progress_bar()

# Function to play the music
def play_music():
    pygame.mixer.music.play()

# Function to stop the music
def pause_music():
    pygame.mixer.music.pause()

# Function to stop the music
def stop_music():
    pygame.mixer.music.stop()

# Function to play a file from the playlist
def play_file(event=None):
    global file_path
    if dropdown_list.curselection():
        index = dropdown_list.curselection()[0]
        if 0 <= index < len(playlist):
            file_path = playlist[index]
            stop_music()
            open_file(file_path)
            play_music()
            update_progress_bar()

# Function to update the progress bar
def update_progress_bar():
    if file_path:
        current_time = pygame.mixer.music.get_pos() / 1000
        total_time = current_music_info["total_time"]

        if current_time >= total_time:
            if loop_state.get():
                progress_bar['value'] = 0
                label_time.config(text="0:00 / 0:00")
                pygame.mixer.music.rewind()
                play_music()
            else:
                stop_music()
                progress_bar['value'] = 0
                label_time.config(text="0:00 / 0:00")
            return

        if total_time > 0:
            progress_bar['value'] = current_time / total_time * 100
            current_time_min = int(current_time // 60)
            current_time_sec = int(current_time % 60)
            total_time_min = int(total_time // 60)
            total_time_sec = int(total_time % 60)
            label_time.config(text=f"{current_time_min:02d}:{current_time_sec:02d} / {total_time_min:02d}:{total_time_sec:02d}")
        fenetre.after(100, update_progress_bar)

# Function to resume playing the music from the current position
def resume_music():
    pygame.mixer.music.unpause()

# Function to set the volume
def set_volume(volume):
    global previous_volume
    volume_level = float(volume) / 100  # Convert scale value to a float between 0 and 1
    pygame.mixer.music.set_volume(volume_level * 2)

# Function to toggle mute
def toggle_mute():
    if pygame.mixer.music.get_volume() > 0:
        pygame.mixer.music.set_volume(0)
        mute_button.config(text="Unmute", bootstyle="outline")
        volume_scale.set(0)
        volume_scale.config(state="disabled")
    else:
        pygame.mixer.music.set_volume(previous_volume)
        mute_button.config(text="Mute", bootstyle="default")
        volume_scale.config(state="normal")
        volume_scale.set(100)


# Bind the play_file function to the ListboxSelect event
dropdown_list.bind('<<ListboxSelect>>', play_file)

# Create a frame for the cover art, title, and artist display
display_frame = tk.Frame(fenetre)
display_frame.pack(side=tk.TOP, pady=10)

# Create a label for the cover art
label_cover_art = tk.Label(display_frame)
label_cover_art.pack(side=tk.TOP, pady=10)
default_startup_image = Image.open(DEFAULT_STARTUP_IMAGE_PATH)
default_startup_image = default_startup_image.resize((300, 300))  # Resize the image as needed
default_startup_image_tk = ImageTk.PhotoImage(default_startup_image)
label_cover_art.config(image=default_startup_image_tk)
label_cover_art.image = default_startup_image_tk

# Create a label for the title
label_title = tk.Label(display_frame, text="Title", font=("Helvetica", 12))
label_title.pack(side=tk.TOP, pady=5)

# Create a label for the artist
label_artist = tk.Label(display_frame, text="Artist", font=("Helvetica", 15, "bold"))
label_artist.pack(side=tk.TOP, pady=3)

# Create a frame for the progress bar and time display
progress_frame = tk.Frame(fenetre)
progress_frame.pack(side=tk.TOP, pady=10)

# Create a progress bar
progress_bar = ttk.Progressbar(progress_frame, orient="horizontal", length=400, mode="determinate")
progress_bar.pack(side=tk.LEFT, padx=5)

# Create a time display
label_time = tk.Label(progress_frame, text="0:00 / 0:00",  font=("Helvetica", 9))
label_time.pack(side=tk.LEFT, padx=5)

# Create a frame for the audio control buttons
audio_control_frame = tk.Frame(fenetre)
audio_control_frame.pack(side=tk.TOP, pady=10, padx=0)

# Create buttons to open, play, and stop the music, and load the library
open_button = ttk.Button(audio_control_frame, text="Load Library", command=load_library, bootstyle=(OUTLINE))
open_button.pack(side=tk.LEFT, padx=5)

pause_button = ttk.Button(audio_control_frame, text="Pause", command=pause_music)
pause_button.pack(side=tk.LEFT, padx=5)

resume_button = ttk.Button(audio_control_frame, text="Play", command=resume_music)
resume_button.pack(side=tk.LEFT, padx=5)

loop_button = ttk.Button(audio_control_frame, text="Loop", command=toggle_loop)
loop_button.pack(side=tk.LEFT, padx=5)

# Create a scale for volume control
volume_scale = ttk.Scale(audio_control_frame, from_=0, to=100, orient=tk.HORIZONTAL, command=set_volume)
volume_scale.set(100)  # Set initial volume to 100%
volume_scale.pack(side=tk.LEFT, padx=10)

# Create a button for mute/unmute
mute_button = ttk.Button(audio_control_frame, text="Mute", command=toggle_mute)
mute_button.pack(side=tk.LEFT, padx=5)

# Function to start updating the progress bar
def start_progress_update():
    update_progress_bar()

# Start the Tkinter event loop
fenetre.after(0, start_progress_update)
fenetre.mainloop()
