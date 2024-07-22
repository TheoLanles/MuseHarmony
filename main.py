import pygame
import tkinter as tk
import tkinter.filedialog
import os
import glob
from mutagen.flac import FLAC
from mutagen.mp3 import MP3
from mutagen.wave import WAVE
from mutagen.id3 import ID3, APIC
from PIL import Image, ImageTk
import io
import configparser
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from dark_title_bar import *
from threading import Thread
import time
from ttkbootstrap.themes.standard import STANDARD_THEMES
import tkinter.messagebox as messagebox
import sys
from tkinter import filedialog
import json
import wave

# Initialize Pygame
pygame.mixer.init()

restart_button = None
close_button = None

# Load the configuration file
config_file = "config/config.ini"
config = configparser.ConfigParser()
config.read(config_file)

# Get the music folder path from the configuration file
music_folder_path = config.get("settings", "music_folder_path", fallback=os.path.expanduser("~"))

# Get the default ttkbootstrap theme from the configuration file
default_theme = config.get("ttkbootstrap", "default_theme", fallback="darkly")

# Get the selected language from the configuration file
lang = config.get('language', 'lang')

# Charge le fichier de traduction pour la langue sélectionnée
def get_translations():
    global lang
    if not os.path.exists('lang'):
        os.makedirs('lang')
    with open(f'lang/{lang}.json') as f:
        translations = json.load(f)
    return translations

# Récupère la langue sélectionnée dans le fichier de configuration
def get_language():
    config = configparser.ConfigParser()
    config.read('settings.ini')
    lang = config.get('language', 'lang')
    return lang

def load_translations():
    global translations
    with open('lang/english.json') as f:
        en = json.load(f)
    with open('lang/francais.json') as f:
        fr = json.load(f)
    with open('lang/espagnol.json') as f:
        es = json.load(f)
    if get_language == 'English':
        translations = en
    elif get_language == 'Français':
        translations = fr
    elif get_language == 'Espagnol':
        translations = es

# Utilise le dictionnaire de traductions pour récupérer les chaînes de caractères traduites
translations = get_translations()
print(translations['hello'])

window_title = "MuseHarmony"
app_name = "MuseHarmony"

# Create a Tkinter window
fenetre = ttk.Window(themename=default_theme)
fenetre.title(window_title)
fenetre.iconbitmap('res/logo.ico')

dark_title_bar(fenetre)

# Set a fixed size for the window
fenetre.geometry("780x510")

# Create a dropdown list to display the playlist
dropdown_list = ttk.Treeview(fenetre, columns=("#1"), height=100 , show="headings")
dropdown_list.heading("#1", text=translations['music'])
dropdown_list.column("#1", width=300, anchor=tk.W)
dropdown_list.pack(side=tk.LEFT, padx=10, pady=6)

# Variable to store the playlist
playlist = []

# Variable to store the loop state (0: no loop, 1: loop)
loop_state = tk.IntVar(value=0)

# Variable to store the previous volume before muting
previous_volume = 1.0 # Initial volume level

def load_library():

     # Clear the dropdown list
    dropdown_list.delete(*dropdown_list.get_children())

    # Get the path of the music folder
    music_folder_path = config.get("settings", "music_folder_path")

    # List of supported audio formats
    supported_audio_formats = ['.mp3', '.flac', '.wav']

    # Traverse the music folder and add all audio files to the dropdown list and playlist
    for root, dirs, files in os.walk(music_folder_path):
        for file in files:
            if file.endswith(tuple(supported_audio_formats)):
                file_path = os.path.join(root, file)
                file_index = len(dropdown_list.get_children())
                dropdown_list.insert("", tk.END, id=file_index, values=(os.path.basename(file),))
                playlist.append(file_path)

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

def toggle_loop_key(event):
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

def update_window_title():
    global window_title, app_name
    fenetre.title(f"{app_name} - {window_title}")

# Function to open an audio file
def open_file(path):
    global file_path, current_music_info
    global window_title
    file_path = path
    base_name, ext = os.path.splitext(file_path)
    pygame.mixer.music.load(file_path)
    window_title = os.path.basename(base_name) if base_name else "MuseHarmony"
    update_window_title()

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
    elif file_path.endswith('.wav'):
     with wave.open(file_path, 'rb') as audio:
        total_time = audio.getnframes() / audio.getframerate()
        title, artist, cover_art = os.path.splitext(os.path.basename(file_path))[0], "Unknown", None
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

# Function to toggle mute
def toggle_pause():
     global is_playing

     if pygame.mixer.music.get_busy():
        pygame.mixer.music.pause()
        is_playing = False
        pause_button.config(text=translations['play'], bootstyle="outline")
     else:
        pygame.mixer.music.unpause()
        is_playing = True
        pause_button.config(text=translations['pause'], bootstyle="default")

# Function to toggle mute
def toggle_pause_key(event):
     global is_playing

     if pygame.mixer.music.get_busy():
        pygame.mixer.music.pause()
        is_playing = False
        pause_button.config(text=translations['play'], bootstyle="outline")
     else:
        pygame.mixer.music.unpause()
        is_playing = True
        pause_button.config(text=translations['pause'], bootstyle="default")

# Function to stop the music
def stop_music():
    pygame.mixer.music.stop()

# Function to play a file from the playlist
def play_file(event=None):
    global file_path
    if dropdown_list.selection():
        index = dropdown_list.selection()[0]
        if 0 <= dropdown_list.index(index) < len(playlist):
            file_path = playlist[dropdown_list.index(index)]
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

# Function to toggle mute
def toggle_mute_key(event):
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

def restart_application():
    python = sys.executable
    os.execl(python, python, *sys.argv)

def show_settings():
    global restart_button
    global close_button

    # Hide the main window elements
    dropdown_list.pack_forget()
    display_frame.pack_forget()
    progress_frame.pack_forget()
    audio_control_frame.pack_forget()

    # Create the settings UI in the main window
    label_config = ttk.Label(fenetre,  text=translations['config_path'], font=("Helvetica", 15))
    label_config.pack(side=tk.TOP, pady=5)

    def select_music_folder():
        new_music_folder_path = filedialog.askdirectory()
        if new_music_folder_path:
            music_folder_entry.delete(0, tk.END)
            music_folder_entry.insert(0, new_music_folder_path)

    # For example, add an entry to change the music folder path
    music_folder_entry = ttk.Entry(fenetre, width=30)
    music_folder_entry.pack(pady=5)
    music_folder_entry.insert(0, music_folder_path)

    modify_button = ttk.Button(fenetre,  text=translations['change'], command=select_music_folder)
    modify_button.pack(pady=10)

    label_config_theme = ttk.Label(fenetre, text=translations['config_theme'], font=("Helvetica", 15))
    label_config_theme.pack(side=tk.TOP, pady=5)

    # Create a dropdown menu for the ttkbootstrap themes
    theme_var = tk.StringVar(fenetre)
    current_theme = fenetre.style.theme_use()  # Récupérez le thème actuellement utilisé
    theme_var.set(current_theme)  # Définissez le thème actuel par défaut
    theme_dropdown = ttk.OptionMenu(fenetre, theme_var, *STANDARD_THEMES)
    theme_dropdown.pack(pady=5)

    modify_theme_button = ttk.Button(fenetre,  text=translations['change'], command=lambda: theme_settings(theme_var.get(), restart_button))
    modify_theme_button.pack(pady=10)

    label_config_lang = ttk.Label(fenetre, text=translations['config_lang'], font=('Helvetica', 15))
    label_config_lang.pack(pady=5)

    lang = ['english', 'francais', 'espagnol']
    lang_var = tk.StringVar(fenetre)
    lang_var.set(get_language)
    lang_menu = ttk.OptionMenu(fenetre, lang_var, *lang)
    lang_menu.pack(pady=5)

    modify_lang = ttk.Button(fenetre, text=translations['change'], command=lambda: save_lang(lang_var.get()))
    modify_lang.pack(pady=10)

    frame_setting = ttk.Frame(fenetre,width=990,height=19, style='dark')
    frame_setting.pack(side=tk.BOTTOM, ipady=20, padx=0)
    frame_setting.pack_propagate(0)

    # Create a button to save the settings
    save_button = ttk.Button(frame_setting, text=translations['save'], command=lambda: save_settings(music_folder_entry.get()),bootstyle=(OUTLINE))
    save_button.pack(side=tk.RIGHT,ipadx=30, padx=5)

    # Create a button to close the settings window
    close_button = ttk.Button(frame_setting, text=translations['close'], command=restore_main_window)
    close_button.pack(side=tk.RIGHT,padx=5)

    restart_button = ttk.Button(frame_setting, text=translations['restart'], command=restart_application, state=DISABLED)
    restart_button.pack(side=tk.RIGHT,padx=5)

def save_settings(new_music_folder_path):
    config.set("settings", "music_folder_path", new_music_folder_path)
    with open(config_file, "w") as configfile:
        config.write(configfile)
    global lang

    # Update the global music_folder_path variable
    global music_folder_path
    music_folder_path = new_music_folder_path

    # Reload the library with the new music folder path
    load_library()

def theme_settings(new_theme, restart_button):
    config.set("ttkbootstrap", "default_theme", new_theme)
    with open(config_file, "w") as configfile:
        config.write(configfile)

    # Update the global default_theme variable
    global default_theme
    default_theme = new_theme

     # If the theme has been changed, show a popup message to inform the user to restart the application
    if fenetre.style.theme_use() != new_theme:
        restart_button.state(['!disabled'])
        close_button.pack_forget()
    else:
        restart_button.state(['disabled'])
        close_button.pack(pady=10)
    default_theme = new_theme

    # Update the window's theme
    fenetre.change_theme(new_theme)
    
def save_lang(lang):
    config.set("language", "lang", lang)
    with open(config_file, "w") as configfile:
        config.write(configfile)

    # Update the global language variable
    global get_language
    get_language = lang
    # Reload the translations with the new language
    load_translations()
    # Hide the "Close" button and show the "Restart" button
    close_button.pack_forget()
    restart_button.state(['!disabled'])
    restart_button.pack(side=tk.RIGHT, padx=5)
    

# Bind the play_file function to the ListboxSelect event
dropdown_list.bind('<<TreeviewSelect>>', play_file)

# Create a frame for the cover art, title, and artist display
display_frame = ttk.Frame(fenetre)
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
label_title = ttk.Label(display_frame, text=translations['title'], font=("Helvetica", 12))
label_title.pack(side=tk.TOP, pady=5)

# Create a label for the artist
label_artist = ttk.Label(display_frame, text=translations['artist'], font=("Helvetica", 15, "bold"))
label_artist.pack(side=tk.TOP, pady=0)

# Create a frame for the progress bar and time display
progress_frame = tk.Frame(fenetre)
progress_frame.pack(side=tk.TOP, pady=6)

# Create a progress bar
progress_bar = ttk.Progressbar(progress_frame, orient="horizontal", length=335, mode="determinate")
progress_bar.pack(side=tk.LEFT, padx=5)

# Create a time display
label_time = tk.Label(progress_frame, text="0:00 / 0:00",  font=("Helvetica", 9))
label_time.pack(side=tk.LEFT, padx=5)

# Create a frame for the audio control buttons
audio_control_frame = ttk.Frame(fenetre,width=915,height=75, style='dark')
audio_control_frame.pack(side=tk.TOP, pady=0, padx=0)
audio_control_frame.pack_propagate(0)

pause_button = ttk.Button(audio_control_frame, text=translations['pause'], command=toggle_pause)
pause_button.pack(side=tk.LEFT, padx=5)

loop_button = ttk.Button(audio_control_frame, text=translations['loop'], command=toggle_loop)
loop_button.pack(side=tk.LEFT, padx=5)

# Create a scale for volume control
volume_scale = tk.Scale(audio_control_frame, from_=0, to=100, orient=ttk.HORIZONTAL, command=set_volume)
volume_scale.set(100)  # Set initial volume to 100%
volume_scale.pack(side=ttk.LEFT, padx=10)

# Create a button for mute/unmute
mute_button = ttk.Button(audio_control_frame, text=translations['mute'], command=toggle_mute)
mute_button.pack(side=tk.LEFT, padx=5)

settings_button = ttk.Button(audio_control_frame, text=translations['settings'], command=show_settings)
settings_button.pack(side=tk.LEFT, padx=5)

# Function to start updating the progress bar
def start_progress_update():
    update_progress_bar()

def restore_main_window():
    global restart_button
    global close_button

    # Remove the settings elements from the main window
    for widget in fenetre.winfo_children():
        if widget not in main_window_elements:
            widget.destroy()

    # Repack the main window elements
    for window_element, config in main_window_elements_pack_config:
        window_element.pack(**config)

    # Reset the restart and close buttons
    restart_button = None
    close_button = None

# Define your main window elements and their pack configurations
main_window_elements_pack_config = [
    (dropdown_list, {"side": tk.LEFT, "padx": 10, "pady": 6}),
    (display_frame, {"side": tk.TOP, "pady": 10}),
    (progress_frame, {"side": tk.TOP, "pady": 10}),
    (audio_control_frame, {"side": tk.TOP, "pady": 0, "padx": 0})
]

main_window_elements = [dropdown_list, display_frame, progress_frame, audio_control_frame]

# Start the Tkinter event loop
fenetre.after(0, start_progress_update)
fenetre.bind('<m>', toggle_mute_key)
fenetre.bind('<l>', toggle_loop_key)
fenetre.bind('<space>', toggle_pause_key)
fenetre.mainloop()
