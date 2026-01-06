import pygame
import logging
import time
from audio import AudioManager
from display import DisplayManager

class Game:
    """Orchestrates the main game loop, input handling, and state management."""

    JUMP_AMOUNT_S = 5.0

    def __init__(self, dtx_data):
        self.dtx = dtx_data
        self.audio_manager = AudioManager(dtx_data)
        self.display_manager = DisplayManager(dtx_data)
        
        self.notes_to_play = self.dtx.timed_notes[:]
        self.song_duration_ms = self.notes_to_play[-1][0] + 3000 if self.notes_to_play else 0
        
        self.game_state = {
            "current_time_ms": 0,
            "note_index": 0,
            "hit_animations": [],
            "notes_to_play": self.notes_to_play,
            "song_duration_ms": self.song_duration_ms,
            "bgm_volume": self.audio_manager.bgm_volume,
            "se_volume": self.audio_manager.se_volume,
        }

    def run(self):
        """Starts the main playback loop."""
        self.audio_manager.load_sounds()
        if not self.audio_manager.sounds and not self.audio_manager.bgm_path:
            logging.error("No sounds were loaded. Nothing to play.")
            return

        clock = pygame.time.Clock()
        logging.info("--- Starting Playback ---")
        
        time_offset_ms = self.dtx.bgm_start_time_ms
        self.game_state["current_time_ms"] = time_offset_ms

        clock_is_audio_driven = self.audio_manager.play_bgm()
        start_ticks = pygame.time.get_ticks()

        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    running = False
                self.handle_input(event)

            # --- Update Master Clock ---
            if clock_is_audio_driven and pygame.mixer.music.get_busy():
                self.game_state["current_time_ms"] = pygame.mixer.music.get_pos() + time_offset_ms
            else:
                if clock_is_audio_driven:
                    logging.info("BGM finished. Switching to system clock.")
                    clock_is_audio_driven = False
                    start_ticks = pygame.time.get_ticks() - self.song_duration_ms
                self.game_state["current_time_ms"] = pygame.time.get_ticks() - start_ticks

            self.update_notes()
            
            self.display_manager.draw_frame(self.game_state)
            
            # --- Check for end of song ---
            if self.game_state["note_index"] >= len(self.notes_to_play) and not pygame.mixer.music.get_busy():
                logging.info("Playback finished.")
                time.sleep(2)
                running = False
            
            clock.tick(240)

        pygame.quit()
        logging.info("Player has shut down.")

    def update_notes(self):
        """Check for and trigger notes that are due."""
        current_time_ms = self.game_state["current_time_ms"]
        note_index = self.game_state["note_index"]
        
        while note_index < len(self.notes_to_play) and self.notes_to_play[note_index][0] <= current_time_ms:
            note_time, channel_id, wav_id = self.notes_to_play[note_index]
            logging.info(f"Note Trigger -> Time: {current_time_ms:.2f}ms, Scheduled: {note_time:.2f}ms, Chan: {channel_id}, WAV: {wav_id}")
            
            self.audio_manager.play_note(channel_id, wav_id, current_time_ms)
            self.game_state["hit_animations"].append({"channel_id": channel_id, "time": current_time_ms})
            
            self.game_state["note_index"] += 1
            note_index = self.game_state["note_index"]

    def handle_input(self, event):
        """Handles user input for volume, seeking, etc."""
        if event.type != pygame.KEYDOWN:
            return

        # Volume
        if event.key == pygame.K_UP:
            self.audio_manager.set_bgm_volume(min(1.0, self.audio_manager.bgm_volume + 0.1))
        elif event.key == pygame.K_DOWN:
            self.audio_manager.set_bgm_volume(max(0.0, self.audio_manager.bgm_volume - 0.1))
        elif event.key == pygame.K_PAGEUP:
            self.audio_manager.set_se_volume(min(1.0, self.audio_manager.se_volume + 0.1))
        elif event.key == pygame.K_PAGEDOWN:
            self.audio_manager.set_se_volume(max(0.0, self.audio_manager.se_volume - 0.1))
        
        self.game_state["bgm_volume"] = self.audio_manager.bgm_volume
        self.game_state["se_volume"] = self.audio_manager.se_volume

        # Seeking
        current_time_ms = self.game_state["current_time_ms"]
        new_time_ms = -1
        if event.key == pygame.K_RIGHT:
            new_time_ms = current_time_ms + (self.JUMP_AMOUNT_S * 1000)
        elif event.key == pygame.K_LEFT:
            new_time_ms = current_time_ms - (self.JUMP_AMOUNT_S * 1000)

        if new_time_ms != -1:
            self.seek(new_time_ms)
            
    def seek(self, new_time_ms):
        """Seeks to a new time in the song."""
        logging.info(f"Seek event: Jumping to {new_time_ms/1000.0:.2f}s")
        new_time_ms = max(0, min(new_time_ms, self.song_duration_ms))

        self.game_state["current_time_ms"] = new_time_ms
        
        # Resync BGM
        self.audio_manager.stop_bgm()
        music_start_pos_s = max(0, (new_time_ms - self.dtx.bgm_start_time_ms) / 1000.0)
        self.audio_manager.play_bgm(start_pos_s=music_start_pos_s)
        
        # Find new note index
        self.game_state["note_index"] = 0
        for i, note in enumerate(self.notes_to_play):
            if note[0] >= new_time_ms:
                self.game_state["note_index"] = i
                break
        
        self.audio_manager.stop_all_sounds()
        self.game_state["hit_animations"].clear()
