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

# Initialize Pygame
pygame.mixer.init()

# Create a Tkinter window
fenetre = ttk.Window(themename='darkly')
fenetre.title("Lecteur de Musique")
fenetre.iconbitmap('res/logo.ico')

dark_title_bar(fenetre)

# Set a fixed size for the window
fenetre.geometry("860x510")

# Load the configuration file
config_file = "config/config.ini"
config = configparser.ConfigParser()
config.read(config_file)

# Get the music folder path from the configuration file
music_folder_path = config.get("settings", "music_folder_path", fallback=os.path.expanduser("~"))

# Create a dropdown list to display the playlist
dropdown_list = tk.Listbox(fenetre, width=55, height=25)
dropdown_list.pack(side=tk.LEFT, padx=10, ipady=30)

# Variable to store the playlist
playlist = []

# Variable to store the loop state (0: no loop, 1: loop)
loop_state = tk.IntVar(value=0)

# Function to toggle loop state
def toggle_loop():
    global loop_state
    if loop_state.get() == 0:
        loop_state.set(1)
        loop_label.config(text="Loop: ON")
        loop_button.config(bootstyle="outline")
        play_music_loop()
        
        
    else:
        loop_state.set(0)
        loop_label.config(text="Loop: OFF")
        loop_button.config(bootstyle="default")
        pygame.mixer.music.play()

# Function to start playing the music either normally or in loop
def play_music_loop():
    global loop_state
    if loop_state.get() == 1:
        pygame.mixer.music.set_endevent(pygame.constants.USEREVENT)
        pygame.mixer.music.play(-1)  # -1 will play the music in an infinite loop
    else:
        pygame.mixer.music.play()

# Function to load the library
def load_library():
    global music_folder_path, playlist, dropdown_list
    # Scan the directory and add all audio files to the playlist
    for extension in ['*.flac', '*.mp3']:
        for file in glob.glob(os.path.join(music_folder_path, extension)):
            playlist.append(file)

    # Update the dropdown list
    dropdown_list.delete(0, tk.END)
    for file in playlist:
        dropdown_list.insert(tk.END, os.path.basename(file))

# Load the library at startup
load_library()

# Variable to store the file path of the audio file
file_path = None

# Variable to store the information about the current music
current_music_info = {"total_time": 0}

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
        title = audio.tags.get('title', [''])[0]
        artist = audio.tags.get('artist', [''])[0]
        cover_art = audio.pictures
        total_time = audio.info.length
    elif file_path.endswith('.mp3'):
        audio = MP3(file_path)
        title = audio.get('TIT2', [''])[0]
        artist = audio.get('TPE1', [''])[0]
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

    # Check if there is a selection in the dropdown list
    if dropdown_list.curselection():
        # Get the index of the selected track
        index = dropdown_list.curselection()[0]

        # Check if the index is within the valid range
        if 0 <= index < len(playlist):
            file_path = playlist[index]

            # Stop the current music
            stop_music()

            # Open and play the new track
            open_file(file_path)
            play_music()

            # Start updating the progress bar
            update_progress_bar()

# Function to update the progress bar
def update_progress_bar():
    global file_path, loop_state
    if file_path:
        # Get the current position of the track
        current_time = pygame.mixer.music.get_pos() / 1000

        # Get the total time from current_music_info
        total_time = current_music_info["total_time"]

        if current_time >= total_time:
            if loop_state.get() == 1:
                # Reset the progress bar and timer
                progress_bar['value'] = 0
                label_time.config(text="0:00 / 0:00")
                # Restart the music
                pygame.mixer.music.rewind()
                play_music()
            else:
                # Stop the music and reset the progress bar and timer
                stop_music()
                progress_bar['value'] = 0
                label_time.config(text="0:00 / 0:00")
            return

        # Update the progress bar only if total_time is not zero
        if total_time > 0:
            # Update the progress bar
            progress_bar['value'] = current_time / total_time * 100

            # Update the time display
            current_time_min = int(current_time // 60)
            current_time_sec = int(current_time % 60)
            total_time_min = int(total_time // 60)
            total_time_sec = int(total_time % 60)
            label_time.config(text=f"{current_time_min:02d}:{current_time_sec:02d} / {total_time_min:02d}:{total_time_sec:02d}")

        # Call this function again after 100ms
        fenetre.after(100, update_progress_bar)

# Function to resume playing the music from the current position
def resume_music():
    pygame.mixer.music.unpause()

# Bind the play_file function to the ListboxSelect event
dropdown_list.bind('<<ListboxSelect>>', play_file)

# Create a frame for the cover art, title, and artist display
display_frame = tk.Frame(fenetre)
display_frame.pack(side=tk.TOP, pady=10)

# Create a label for the cover art
label_cover_art = tk.Label(display_frame)
label_cover_art.pack(side=tk.TOP, pady=10)

# Create a label for the title
label_title = tk.Label(display_frame, text="", font=("Helvetica", 12))
label_title.pack(side=tk.TOP, pady=5)

# Create a label for the artist
label_artist = tk.Label(display_frame, text="", font=("Helvetica", 15, "bold"))
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
audio_control_frame.pack(side=tk.TOP, pady=10)

# Create buttons to open, play, and stop the music, and load the library
open_button = ttk.Button(audio_control_frame, text="Load Library", command=load_library, bootstyle=(OUTLINE))
open_button.pack(side=tk.LEFT, padx=5)

pause_button = ttk.Button(audio_control_frame, text="Pause", command=pause_music)
pause_button.pack(side=tk.LEFT, padx=5)

resume_button = ttk.Button(audio_control_frame, text="Play", command=resume_music)
resume_button.pack(side=tk.LEFT, padx=5)

loop_button = ttk.Button(audio_control_frame, text="Loop", command=toggle_loop)
loop_button.pack(side=tk.LEFT, padx=5)

loop_label = tk.Label(audio_control_frame, text="Loop: OFF")
loop_label.pack(side=tk.LEFT, padx=5)

# Function to start updating the progress bar
def start_progress_update():
    update_progress_bar()

# Start the Tkinter event loop
fenetre.after(0, start_progress_update)
fenetre.mainloop()
