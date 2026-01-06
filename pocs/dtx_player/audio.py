import os
import pygame
import logging

class AudioManager:
    """Handles loading and playback of all audio, including BGM and sound effects."""

    # --- Sound Mechanics Configuration ---
    POLYPHONY_LIMIT = 4
    CHOKE_MAP = {
        "11": ["18"],  # Closed HH chokes Open HH
        "1B": ["18"],  # Pedal HH chokes Open HH
    }

    def __init__(self, dtx_data):
        self.dtx = dtx_data
        self.sounds = {}
        self.bgm_path = None
        self.bgm_volume = 0.7
        self.se_volume = 1.0

        # Fade envelope settings (ms)
        self.se_fade_in_ms = 10
        self.se_fade_out_ms = 100
        self.bgm_fade_ms = 400

        # --- Audio State Management ---
        self.active_poly_sounds = {}
        self.active_choke_sounds = {}
        self.CHOKEABLE_CHANNELS = list(
            set(
                choked
                for choker, choked_list in self.CHOKE_MAP.items()
                for choked in choked_list
            )
        )

        print("\nInitializing Pygame audio...")
        pygame.mixer.pre_init(44100, -16, 2, 1024)
        pygame.init()
        pygame.mixer.set_num_channels(64)
        print("Pygame audio initialized.")

    def load_sounds(self):
        """Loads all audio files defined in the DTX data into memory."""
        logging.info("--- Loading Audio Files ---")
        for wav_id, path in self.dtx.wav_files.items():
            if not os.path.exists(path):
                logging.warning(f"Audio file not found for WAV ID {wav_id}: {path}")
                continue
            if wav_id == self.dtx.bgm_wav_id:
                self.bgm_path = path
                continue
            try:
                sound = pygame.mixer.Sound(path)
                self.sounds[wav_id] = sound
            except pygame.error as e:
                logging.warning(f"Could not load '{os.path.basename(path)}'. Error: {e}")

        if self.bgm_path:
            try:
                pygame.mixer.music.load(self.bgm_path)
                pygame.mixer.music.set_volume(self.bgm_volume)
                logging.info(f"BGM loaded. Volume set to {self.bgm_volume * 100:.0f}%.")
            except pygame.error as e:
                logging.warning(f"Could not load BGM '{os.path.basename(self.bgm_path)}'. Error: {e}")
                self.bgm_path = None
        logging.info(f"{len(self.sounds)} sound effects loaded.")

    def play_bgm(self, start_pos_s=0):
        if self.bgm_path:
            try:
                pygame.mixer.music.play(start=start_pos_s, fade_ms=self.bgm_fade_ms)
                return True
            except pygame.error as e:
                logging.error(f"Could not play BGM. Error: {e}")
        return False

    def stop_bgm(self):
        if self.bgm_path:
            pygame.mixer.music.fadeout(self.bgm_fade_ms)
            
    def set_bgm_volume(self, volume):
        self.bgm_volume = volume
        if self.bgm_path:
            pygame.mixer.music.set_volume(self.bgm_volume)

    def set_se_volume(self, volume):
        self.se_volume = volume

    def play_note(self, channel_id, wav_id, current_time_ms):
        """Plays a note with choke and polyphony logic."""
        if wav_id not in self.sounds:
            return

        sound_to_play = self.sounds[wav_id]

        # 1. --- Choke Logic ---
        if channel_id in self.CHOKE_MAP:
            for choked_channel_id in self.CHOKE_MAP[channel_id]:
                if choked_channel_id in self.active_choke_sounds:
                    channel_to_stop = self.active_choke_sounds.pop(choked_channel_id)
                    if channel_to_stop and channel_to_stop.get_busy():
                        logging.debug(f"Choke: Note {channel_id} stopping active sound on channel {choked_channel_id}")
                        channel_to_stop.fadeout(self.se_fade_out_ms)

        # 2. --- Polyphony & Playback Logic ---
        if channel_id not in self.active_poly_sounds:
            self.active_poly_sounds[channel_id] = []

        playing_instances = self.active_poly_sounds[channel_id]
        playing_instances = [item for item in playing_instances if item[0].get_busy()]

        if len(playing_instances) >= self.POLYPHONY_LIMIT:
            playing_instances.sort(key=lambda x: x[1])
            oldest_channel, oldest_time = playing_instances.pop(0)
            logging.debug(f"Polyphony: Chan {channel_id} limit reached. Stealing voice from note played at {oldest_time:.2f}ms.")
            oldest_channel.fadeout(self.se_fade_out_ms)

        wav_vol_percent = self.dtx.wav_volumes.get(wav_id, 100)
        final_volume = self.se_volume * (wav_vol_percent / 100.0)
        sound_to_play.set_volume(final_volume)
        new_channel = sound_to_play.play(fade_ms=self.se_fade_in_ms)

        if new_channel:
            playing_instances.append((new_channel, current_time_ms))
            if channel_id in self.CHOKEABLE_CHANNELS:
                self.active_choke_sounds[channel_id] = new_channel

        self.active_poly_sounds[channel_id] = playing_instances

    def stop_all_sounds(self):
        """Stops all currently playing sound effects immediately."""
        pygame.mixer.stop()
        self.active_poly_sounds.clear()
        self.active_choke_sounds.clear()
        logging.info("All active sounds stopped for seek.")
