import time
import psutil
import pygetwindow as gw
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
from comtypes import CLSCTX_ALL
from ctypes import cast, POINTER
from plyer import notification
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def is_youtube_active():
    """Check if a YouTube tab or app is active."""
    windows = gw.getAllTitles()
    for window in windows:
        if "YouTube" in window:
            return True
    return False

def is_spotify_running():
    """Check if the Spotify application is running."""
    for process in psutil.process_iter(['name']):
        if process.info['name'] and "Spotify.exe" in process.info['name']:
            return True
    return False

def get_spotify_session():
    """Retrieve the audio session for Spotify."""
    sessions = AudioUtilities.GetAllSessions()
    for session in sessions:
        if session.Process and session.Process.name() == "Spotify.exe":
            return session
    return None

def mute_spotify(mute=True):
    """Mute or unmute Spotify."""
    session = get_spotify_session()
    if session:
        volume = session.SimpleAudioVolume
        volume.SetMute(mute, None)
        state = "Muted" if mute else "Unmuted"
        logging.info(f"Spotify has been {state}.")
        notification.notify(
            title="Spotify Control",
            message=f"Spotify has been {state} due to active YouTube.",
            timeout=3
        )
    else:
        logging.error("Spotify session not found.")

def main():
    spotify_muted = False
    while True:
        youtube_active = is_youtube_active()
        spotify_running = is_spotify_running()

        if youtube_active and spotify_running and not spotify_muted:
            mute_spotify(True)
            spotify_muted = True
        elif not youtube_active and spotify_running and spotify_muted:
            mute_spotify(False)
            spotify_muted = False

        time.sleep(5)  # Check every 5 seconds

if __name__ == "__main__":
    main()
