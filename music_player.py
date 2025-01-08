import customtkinter as ctk
import pygame
import os
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from tkinter import filedialog
from PIL import Image, ImageTk

class MusicPlayer:
    def __init__(self):
        pygame.mixer.init()
        
        # Create the main window
        self.window = ctk.CTk()
        self.window.title("")
        self.window.geometry("400x300")
        self.window.configure(fg_color="#C5E4E7")
        self.window.attributes('-alpha', 0.95)
        self.window.overrideredirect(True)
        
        # Current song state
        self.current_song = None
        self.is_playing = False
        
        # Create UI elements FIRST
        self.setup_ui()
        
        # Initialize Spotify AFTER UI is created
        self.setup_spotify()
        
        # Add timer for updates LAST
        self.update_timer = None
        self.start_update_loop()
        
        # Add window drag functionality
        self.window.bind("<Button-1>", self.start_move)
        self.window.bind("<ButtonRelease-1>", self.stop_move)
        self.window.bind("<B1-Motion>", self.do_move)

    def setup_spotify(self):
        # Spotify API credentials - replace with your own
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id="YOUR_CLIENT_ID",
            client_secret="YOUR_CLIENT_SECRET",
            redirect_uri="http://localhost:8888/callback",
            scope="user-read-playback-state user-modify-playback-state"
        ))

    def setup_ui(self):
        # Top bar with home and close buttons
        top_frame = ctk.CTkFrame(self.window, fg_color="transparent")
        top_frame.pack(fill="x", padx=15, pady=10)
        
        # Home button (Minimizes the player)
        lyrics_btn = ctk.CTkButton(
            top_frame,
            text="📄",  # Paper/lyrics icon
            width=30,
            height=30,
            corner_radius=15,
            fg_color="#A5D4D7",
            hover_color="#95C4C7",
            text_color="black",
            font=("Arial", 16),
            command=self.show_lyrics
        )
        lyrics_btn.pack(side="left")
        
        # File select button (Changed from Spotify to file selection)
        file_btn = ctk.CTkButton(
            top_frame,
            text="📂",  # Changed to folder icon
            width=30,
            height=30,
            corner_radius=15,
            fg_color="#A5D4D7",
            hover_color="#95C4C7",
            text_color="black",
            font=("Arial", 16),
            command=self.select_song
        )
        file_btn.pack(side="left", padx=10)
        
        # Close button
        close_btn = ctk.CTkButton(
            top_frame,
            text="✕",
            width=40,
            height=40,
            corner_radius=20,
            fg_color="#A5D4D7",
            hover_color="#95C4C7",
            text_color="black",
            font=("Arial", 16),
            command=self.window.quit
        )
        close_btn.pack(side="right")
        
        # Main content frame
        content_frame = ctk.CTkFrame(
            self.window,
            fg_color="#E8F4F5",
            corner_radius=30  # More rounded corners
        )
        content_frame.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # Album art and song info
        info_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        info_frame.pack(fill="x", padx=25, pady=15)
        
        # Album art (left side)
        self.art_label = ctk.CTkLabel(
            info_frame,
            text="",
            image=self.load_default_art(),
            width=60,
            height=60
        )
        self.art_label.pack(side="left")
        
        # Song info (right of album art)
        text_frame = ctk.CTkFrame(info_frame, fg_color="transparent")
        text_frame.pack(side="left", padx=(20, 0))
        
        self.song_label = ctk.CTkLabel(
            text_frame,
            text="No music playing",
            font=("Arial", 16, "bold"),
            anchor="w"
        )
        self.song_label.pack(anchor="w")
        
        self.artist_label = ctk.CTkLabel(
            text_frame,
            text="Select a song or connect Spotify",
            font=("Arial", 14),
            text_color="gray",
            anchor="w"
        )
        self.artist_label.pack(anchor="w")
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(
            content_frame,
            height=4,
            corner_radius=2,
            progress_color="#95C4C7"
        )
        self.progress_bar.pack(fill="x", padx=25, pady=15)
        self.progress_bar.set(0)
        
        # Add time label below progress bar
        self.time_label = ctk.CTkLabel(
            content_frame,
            text="0:00 / 0:00",
            font=("Arial", 12),
            text_color="gray"
        )
        self.time_label.pack(pady=(0, 10))
        
        # Control buttons with updated style
        button_style = {
            "width": 50,
            "height": 35,
            "corner_radius": 15,
            "fg_color": "#D5E5E8",
            "hover_color": "#C5D5D8",
            "text_color": "black",
            "font": ("Arial", 16, "bold")
        }
        
        # Center the control buttons
        controls_frame = ctk.CTkFrame(
            content_frame,
            fg_color="#E8F4F5",
            corner_radius=15
        )
        controls_frame.pack(fill="x", padx=25, pady=(5, 20))
        
        # Control buttons container
        buttons_container = ctk.CTkFrame(
            controls_frame,
            fg_color="transparent"
        )
        buttons_container.pack(expand=True, pady=10)
        
        # Control buttons
        self.prev_button = ctk.CTkButton(
            buttons_container,
            text="<<",
            command=self.previous_track,
            **button_style
        )
        self.prev_button.pack(side="left", padx=10)
        
        self.play_button = ctk.CTkButton(
            buttons_container,
            text=">",
            command=self.toggle_play,
            width=60,
            height=40,
            corner_radius=15,
            fg_color="#D5E5E8",
            hover_color="#C5D5D8",
            text_color="black",
            font=("Arial", 18, "bold")
        )
        self.play_button.pack(side="left", padx=10)
        
        self.next_button = ctk.CTkButton(
            buttons_container,
            text=">>",
            command=self.next_track,
            **button_style
        )
        self.next_button.pack(side="left", padx=10)

    def load_default_art(self):
        # Create a default album art (blue heart)
        return ctk.CTkImage(
            light_image=Image.new('RGB', (60, 60), '#95C4C7'),
            dark_image=Image.new('RGB', (60, 60), '#95C4C7'),
            size=(60, 60)
        )

    def connect_spotify(self):
        try:
            # Get current playback state
            current = self.sp.current_playback()
            if current and current['item']:
                self.song_label.configure(text=current['item']['name'])
                self.artist_label.configure(text=current['item']['artists'][0]['name'])
                # You could also load the album art here
        except Exception as e:
            print(f"Error connecting to Spotify: {e}")

    def start_move(self, event):
        self.x = event.x
        self.y = event.y

    def stop_move(self, event):
        self.x = None
        self.y = None

    def do_move(self, event):
        deltax = event.x - self.x
        deltay = event.y - self.y
        x = self.window.winfo_x() + deltax
        y = self.window.winfo_y() + deltay
        self.window.geometry(f"+{x}+{y}")

    def select_song(self):
        file_path = filedialog.askopenfilename(
            filetypes=[("Audio Files", "*.mp3 *.wav")]
        )
        if file_path:
            self.current_song = file_path
            song_name = os.path.basename(file_path)
            self.song_label.configure(text=song_name.split('.')[0])
            
            # Load and play the song
            pygame.mixer.music.load(file_path)
            pygame.mixer.music.play()
            self.is_playing = True
            self.play_button.configure(text="II")
            
            # Get song duration (requires mutagen)
            try:
                from mutagen.mp3 import MP3
                audio = MP3(file_path)
                self.current_song_duration = audio.info.length
            except:
                self.current_song_duration = 0
                print("Could not get song duration")
            
            # Update album art to default
            self.update_album_art()

    def toggle_play(self):
        if self.current_song:  # Local playback
            if self.is_playing:
                pygame.mixer.music.pause()
                self.play_button.configure(text=">")
            else:
                pygame.mixer.music.unpause()
                self.play_button.configure(text="II")
            self.is_playing = not self.is_playing
        else:  # Spotify playback
            try:
                current = self.sp.current_playback()
                
                # If no active device, try to find one
                if not current or not current.get('device'):
                    devices = self.sp.devices()
                    if devices['devices']:
                        # Use the first available device
                        self.sp.transfer_playback(devices['devices'][0]['id'])
                    
                # Toggle playback
                if current and current.get('is_playing', False):
                    self.sp.pause_playback()
                    self.play_button.configure(text=">")
                else:
                    self.sp.start_playback()
                    self.play_button.configure(text="II")
            except Exception as e:
                print(f"Error controlling Spotify: {e}")
                # If no Spotify device available, switch to local file selection
                self.select_song()

    def previous_track(self):
        try:
            self.sp.previous_track()
        except:
            pass

    def next_track(self):
        try:
            self.sp.next_track()
        except:
            pass
        
    def run(self):
        self.window.mainloop()

    def start_update_loop(self):
        self.update_player_state()
        # Update every second
        self.update_timer = self.window.after(1000, self.start_update_loop)

    def update_player_state(self):
        if self.current_song:  # Local playback
            if pygame.mixer.music.get_busy():
                # Update progress for local file
                pos = pygame.mixer.music.get_pos() / 1000  # Convert to seconds
                duration = self.current_song_duration
                if duration:
                    self.progress_bar.set(pos / duration)
                    self.time_label.configure(text=f"{self.format_time(pos)} / {self.format_time(duration)}")
        else:  # Spotify playback
            try:
                current = self.sp.current_playback()
                if current and current['item']:
                    # Update song info
                    song_name = current['item']['name']
                    artist_name = current['item']['artists'][0]['name']
                    
                    # Update labels if song changed
                    if self.song_label.cget("text") != song_name:
                        self.song_label.configure(text=song_name)
                        self.artist_label.configure(text=artist_name)
                        
                        # Update album art
                        album_art_url = current['item']['album']['images'][0]['url']
                        self.update_album_art(album_art_url)
                    
                    # Update progress
                    progress = current['progress_ms'] / 1000  # Convert to seconds
                    duration = current['item']['duration_ms'] / 1000
                    self.progress_bar.set(progress / duration)
                    self.time_label.configure(text=f"{self.format_time(progress)} / {self.format_time(duration)}")
                    
                    # Update play button state
                    self.play_button.configure(text="⏸" if current['is_playing'] else "▶")
            except Exception as e:
                print(f"Error updating Spotify state: {e}")

    def update_album_art(self, url=None):
        try:
            if url:
                # Download and display Spotify album art
                from urllib.request import urlopen
                from io import BytesIO
                
                image_data = urlopen(url).read()
                image = Image.open(BytesIO(image_data))
                image = image.resize((60, 60), Image.Resampling.LANCZOS)
            else:
                # Create default art
                image = Image.new('RGB', (60, 60), '#95C4C7')
                
            photo = ctk.CTkImage(
                light_image=image,
                dark_image=image,
                size=(60, 60)
            )
            self.art_label.configure(image=photo)
            self.art_label.image = photo  # Keep a reference
        except Exception as e:
            print(f"Error updating album art: {e}")

    def format_time(self, seconds):
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes}:{seconds:02d}"

    def __del__(self):
        # Clean up the update timer when the window is closed
        if self.update_timer:
            self.window.after_cancel(self.update_timer)

    def show_lyrics(self):
        # Implement lyrics functionality here
        print("Lyrics feature to be implemented")
        pass

if __name__ == "__main__":
    player = MusicPlayer()
    player.run() 
message.txt
15 KB
