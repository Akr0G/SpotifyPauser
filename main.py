import time
import psutil
import pygetwindow as gw
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from plyer import notification
import logging
import win32gui
import win32con
import threading
from contextlib import contextmanager
import sys

# Logging setup
logging.basicConfig(
    level=logging.INFO, 
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('spotify_mute.log', mode='a', encoding='utf-8')
    ]
)

# Configuration
YOUTUBE_TITLES = [
    "youtube",
    "youtube - google chrome",
    "youtube music",
    "chrome - youtube",
    "youtube - microsoft edge",
    "youtube - firefox",
    "youtube - opera",
    "youtube.com",
    "music.youtube.com"
]

SPOTIFY_PROCESS_NAMES = ["spotify.exe", "spotifywebhelper.exe"]
CHECK_INTERVAL = 2  # seconds
NOTIFICATION_COOLDOWN = 10  # seconds between notifications

class SpotifyMuteController:
    def __init__(self):
        self.spotify_muted = False
        self.last_notification = 0
        self.session_cache = None
        self.session_cache_time = 0
        self.lock = threading.Lock()
        
    def get_active_window_title(self):
        """Get the title of the currently active window"""
        try:
            hwnd = win32gui.GetForegroundWindow()
            if hwnd:
                # Get window text with proper error handling
                length = win32gui.GetWindowTextLength(hwnd)
                if length > 0:
                    title = win32gui.GetWindowText(hwnd)
                    return title.strip()
        except Exception as e:
            logging.debug(f"Error getting active window title: {e}")
        return ""

    def is_youtube_focused(self):
        """Check if a YouTube window is currently focused"""
        try:
            active_title = self.get_active_window_title().lower()
            if not active_title:
                return False
                
            # Check for exact matches and partial matches
            for yt_title in YOUTUBE_TITLES:
                if (active_title == yt_title or 
                    active_title.startswith(yt_title + " ") or
                    yt_title in active_title):
                    logging.debug(f"YouTube detected in window: '{active_title}'")
                    return True
                    
            # Additional check for YouTube URLs in title
            if "youtube.com" in active_title or "youtu.be" in active_title:
                logging.debug(f"YouTube URL detected in window: '{active_title}'")
                return True
                
        except Exception as e:
            logging.error(f"Error checking YouTube focus: {e}")
        return False

    def is_spotify_running(self):
        """Check if Spotify is currently running"""
        try:
            for proc in psutil.process_iter(['name', 'pid']):
                try:
                    proc_name = proc.info['name']
                    if proc_name and proc_name.lower() in [name.lower() for name in SPOTIFY_PROCESS_NAMES]:
                        return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
        except Exception as e:
            logging.error(f"Error checking Spotify process: {e}")
        return False

    def get_spotify_session(self, force_refresh=False):
        """Get Spotify audio session with caching"""
        current_time = time.time()
        
        # Use cached session if it's recent and not forcing refresh
        if (not force_refresh and 
            self.session_cache and 
            current_time - self.session_cache_time < 5):
            return self.session_cache
            
        try:
            sessions = AudioUtilities.GetAllSessions()
            for session in sessions:
                if session.Process:
                    proc_name = session.Process.name().lower()
                    if proc_name in [name.lower() for name in SPOTIFY_PROCESS_NAMES]:
                        self.session_cache = session
                        self.session_cache_time = current_time
                        return session
        except Exception as e:
            logging.error(f"Error getting Spotify session: {e}")
            
        # Clear cache if no session found
        self.session_cache = None
        return None

    def is_spotify_playing_audio(self):
        """Check if Spotify is actively playing audio"""
        try:
            session = self.get_spotify_session()
            if session and hasattr(session, 'SimpleAudioVolume'):
                # Check if the session has volume > 0 and is not muted
                volume = session.SimpleAudioVolume
                return volume.GetMasterVolume() > 0 and not volume.GetMute()
        except Exception as e:
            logging.debug(f"Error checking Spotify audio state: {e}")
        return False

    @contextmanager
    def safe_spotify_operation(self):
        """Context manager for safe Spotify operations"""
        try:
            with self.lock:
                yield
        except Exception as e:
            logging.error(f"Spotify operation failed: {e}")
            # Clear cache on error
            self.session_cache = None

    def mute_spotify(self, mute=True):
        """Mute or unmute Spotify with improved error handling"""
        with self.safe_spotify_operation():
            session = self.get_spotify_session(force_refresh=True)
            if not session:
                logging.warning("Spotify session not found. Is Spotify running and playing audio?")
                return False

            try:
                volume = session.SimpleAudioVolume
                current_mute = volume.GetMute()
                
                if current_mute != mute:
                    volume.SetMute(mute, None)
                    state = "Muted" if mute else "Unmuted"
                    logging.info(f"Spotify {state} successfully.")
                    self.send_notification(f"Spotify {state}", 
                                         f"Spotify has been {state} due to YouTube {'focus' if mute else 'unfocus'}.")
                    return True
                else:
                    logging.debug(f"Spotify already {'muted' if mute else 'unmuted'}. No action taken.")
                    return True
                    
            except Exception as e:
                logging.error(f"Failed to {'mute' if mute else 'unmute'} Spotify: {e}")
                return False

    def send_notification(self, title, message):
        """Send notification with cooldown to prevent spam"""
        current_time = time.time()
        if current_time - self.last_notification >= NOTIFICATION_COOLDOWN:
            try:
                notification.notify(
                    title=title,
                    message=message,
                    timeout=3,
                    app_name="Spotify Auto Mute"
                )
                self.last_notification = current_time
            except Exception as e:
                logging.error(f"Failed to send notification: {e}")

    def run(self):
        """Main execution loop"""
        logging.info("Starting Spotify-YouTube auto-mute script...")
        logging.info("Press Ctrl+C to stop the script")
        
        if not self.check_dependencies():
            return
            
        consecutive_errors = 0
        max_consecutive_errors = 5
        
        try:
            while True:
                try:
                    youtube_active = self.is_youtube_focused()
                    spotify_running = self.is_spotify_running()
                    
                    # Reset error counter on successful iteration
                    consecutive_errors = 0
                    
                    if youtube_active and spotify_running and not self.spotify_muted:
                        logging.info("YouTube active and Spotify running. Muting Spotify...")
                        if self.mute_spotify(True):
                            self.spotify_muted = True
                            
                    elif not youtube_active and spotify_running and self.spotify_muted:
                        logging.info("YouTube not active, Spotify running, and Spotify muted. Unmuting Spotify...")
                        if self.mute_spotify(False):
                            self.spotify_muted = False
                            
                    elif not spotify_running and self.spotify_muted:
                        # Reset mute state if Spotify is not running
                        logging.info("Spotify not running. Resetting mute state.")
                        self.spotify_muted = False
                        
                    else:
                        logging.debug(f"Status - YouTube: {youtube_active}, Spotify: {spotify_running}, Muted: {self.spotify_muted}")

                except Exception as e:
                    consecutive_errors += 1
                    logging.error(f"Exception in main loop (#{consecutive_errors}): {e}")
                    
                    if consecutive_errors >= max_consecutive_errors:
                        logging.critical(f"Too many consecutive errors ({consecutive_errors}). Stopping script.")
                        break
                    
                    # Clear caches on error
                    self.session_cache = None

                time.sleep(CHECK_INTERVAL)
                
        except KeyboardInterrupt:
            logging.info("Script stopped by user")
        except Exception as e:
            logging.critical(f"Critical error: {e}")
        finally:
            # Cleanup: unmute Spotify if it was muted
            if self.spotify_muted:
                logging.info("Cleaning up: Unmuting Spotify...")
                self.mute_spotify(False)

    def check_dependencies(self):
        """Check if all required dependencies are available"""
        try:
            # Test audio utilities
            AudioUtilities.GetAllSessions()
            logging.info("Audio utilities available")
            
            # Test window functions
            win32gui.GetForegroundWindow()
            logging.info("Window utilities available")
            
            return True
            
        except Exception as e:
            logging.error(f"Dependency check failed: {e}")
            logging.error("Make sure you're running as administrator and all required packages are installed")
            return False

def main():
    """Entry point"""
    try:
        controller = SpotifyMuteController()
        controller.run()
    except Exception as e:
        logging.critical(f"Failed to start application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()