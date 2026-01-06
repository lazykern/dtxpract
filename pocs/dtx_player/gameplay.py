import sys
import pygame
try:
    import pygame.midi
except ImportError:
    pass
import logging
import time
from audio import AudioManager
from display import DisplayManager

class Game:
    """Orchestrates the main game loop, input handling, and state management."""

    JUMP_AMOUNT_S = 5.0

    # GM Map: MIDI Note -> DTX Channel
    GM_MIDI_MAP = {
        36: "13", # Kick
        38: "12", # Snare
        41: "17", # F.Tom
        42: "11", # HHC
        44: "1B", # Pedal Hi-Hat (Mapped to Left Pedal/Foot channel)
        45: "15", # L.Tom
        46: "18", # HHO
        48: "14", # H.Tom
        49: "1A", # H.Cym (Left Cymbal)
        51: "19", # Ride
        57: "16", # R.Cym
    }

    def __init__(self, dtx_data):
        self.dtx = dtx_data
        self.audio_manager = AudioManager(dtx_data)
        self.display_manager = DisplayManager(dtx_data)
        
        # Convert tuples to dicts for mutable state
        self.notes_to_play = [
            {"time": t, "channel": c, "wav": w, "hit": False, "judged": False} 
            for t, c, w in self.dtx.timed_notes
        ]
        
        self.song_duration_ms = self.notes_to_play[-1]["time"] + 3000 if self.notes_to_play else 0
        
        self.auto_mode = True # Default to Auto
        self.last_judgment = ""

        # MIDI Init
        self.midi_input = None
        self.midi_status = "MIDI: Init..."
        try:
            import mido
            inputs = mido.get_input_names()
            logging.info(f"Available MIDI Inputs: {inputs}")
            
            target_port = None
            # Filter out "Midi Through" if possible, unless it's the only one
            for name in inputs:
                if "Through" not in name:
                    target_port = name
                    break
            
            if not target_port and inputs:
                target_port = inputs[0]
            
            if target_port:
                self.midi_input = mido.open_input(target_port)
                logging.info(f"Opened MIDI Input: {target_port}")
                self.midi_status = f"MIDI: {target_port}"
            else:
                self.midi_status = "MIDI: No Devices Found"
                
        except Exception as e:
            logging.error(f"Failed to initialize MIDI: {e}")
            self.midi_status = "MIDI: Error"

        self.game_state = {
            "current_time_ms": 0,
            "note_index": 0,
            "hit_animations": [],
            "notes_to_play": self.notes_to_play,
            "song_duration_ms": self.song_duration_ms,
            "bgm_volume": self.audio_manager.bgm_volume,
            "se_volume": self.audio_manager.se_volume,
            "auto_mode": self.auto_mode,
            "last_judgment": "",
            "midi_status": self.midi_status,
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
            current_tick = pygame.time.get_ticks()
            for event in pygame.event.get():
                if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                    running = False
                self.handle_input(event)
            
            # Handle MIDI
            self.process_midi_input()

            # --- Update Master Clock ---
            if clock_is_audio_driven and pygame.mixer.music.get_busy():
                self.game_state["current_time_ms"] = pygame.mixer.music.get_pos() + time_offset_ms
            else:
                if clock_is_audio_driven:
                    logging.info("BGM finished. Switching to system clock.")
                    clock_is_audio_driven = False
                    start_ticks = current_tick - self.song_duration_ms
                self.game_state["current_time_ms"] = current_tick - start_ticks

            self.update_notes()
            
            self.display_manager.draw_frame(self.game_state)
            
            # --- Check for end of song ---
            if self.game_state["note_index"] >= len(self.notes_to_play) and not pygame.mixer.music.get_busy():
                # If we are in Manual mode, we might still have unjudged notes?
                # Simple check for now
                if self.game_state["current_time_ms"] > self.song_duration_ms:
                    logging.info("Playback finished.")
                    time.sleep(2)
                    running = False
            
            clock.tick(240) # High loop rate for input precision

        if self.midi_input:
            self.midi_input.close()
        pygame.quit()
        logging.info("Player has shut down.")

    def process_midi_input(self):
        if not self.midi_input:
            return
        
        # iter_pending is non-blocking
        for msg in self.midi_input.iter_pending():
            if msg.type == 'note_on' and msg.velocity > 0:
                logging.info(f"MIDI Note On: {msg.note} Vel: {msg.velocity}")
                if msg.note in self.GM_MIDI_MAP:
                    val = self.GM_MIDI_MAP[msg.note]
                    self.trigger_manual_note(val)
                else:
                    logging.info(f"Unmapped MIDI Note: {msg.note}")

    def trigger_manual_note(self, channel_id):
        current_time = self.game_state["current_time_ms"]
        
        if self.auto_mode:
             logging.info(f"Manual input on {channel_id} ignored (Auto Mode is ON)")
             # We could optionally trigger a 'ghost' sound here if desired
             return 

        # Judgment Window (ms)
        PERFECT = 30
        GREAT = 60
        GOOD = 100
        POOR = 150
        
        # Find the best candidate note to hit
        # We search primarily around the current note_index
        # But for early hits, we might need to look ahead
        # For late hits, we check unjudged notes behind?
        
        # Search window in notes list: simplistic
        # Start a bit back
        start_idx = max(0, self.game_state["note_index"] - 10)
        end_idx = min(len(self.notes_to_play), self.game_state["note_index"] + 20)
        
        best_note = None
        min_diff = 10000
        
        for i in range(start_idx, end_idx):
            note = self.notes_to_play[i]
            if note["channel"] == channel_id and not note["judged"]:
                diff = abs(note["time"] - current_time)
                if diff < min_diff:
                    min_diff = diff
                    best_note = note

        if best_note and min_diff <= POOR:
            # Hit!
            best_note["hit"] = True
            best_note["judged"] = True
            
            # Determine Judgment
            judgment = "MISS"
            if min_diff <= PERFECT:
                judgment = "PERFECT"
            elif min_diff <= GREAT:
                judgment = "GREAT"
            elif min_diff <= GOOD:
                judgment = "GOOD"
            else:
                judgment = "POOR"
            
            self.last_judgment = judgment
            self.game_state["last_judgment"] = judgment
            
            # Play Sound
            self.audio_manager.play_note(best_note["channel"], best_note["wav"], current_time)
            self.game_state["hit_animations"].append({"channel_id": channel_id, "time": current_time})
            logging.info(f"Manual Hit! {judgment} ({max(0, min_diff):.2f}ms diff)")
            
        else:
            # Ghost hit (pressed but no note near)
            # Maybe play default sound? For now, silence.
            pass

    def update_notes(self):
        """Check for and trigger notes that are due."""
        current_time_ms = self.game_state["current_time_ms"]
        note_index = self.game_state["note_index"]
        
        # We need to process notes that have passed
        MISS_WINDOW = 150.0

        processed_count = 0
        
        # We scan from current index. 
        # In Auto Mode, we play everything.
        # In Manual Mode, we play 'BGM' chips and Mark 'Miss' on Drum chips.
        
        # Important: Don't just stop at current_time. If we missed a note, we need to process it.
        # But sorting ensures we process in order.
        
        while note_index < len(self.notes_to_play):
            note = self.notes_to_play[note_index]
            note_time = note["time"]
            
            # If the note is in the future beyond relevant timing, stop
            if note_time > current_time_ms + 10: # Small buffer
                break
            
            # Note is visible/audible now or past
            
            # 1. AUTO MODE or BGM Channel (Channels usually < 10 or specific?)
            # Actually DTX separates BGM (01) from playable.
            # But the user wants "Auto Mode" which plays DRUMS too.
            playable_channels = set(self.GM_MIDI_MAP.values())
            is_playable = note["channel"] in playable_channels
            
            should_auto_play = self.auto_mode or (not is_playable)
            
            if should_auto_play:
                if not note["judged"]:
                     # Play it
                     logging.info(f"Auto Trigger -> Time: {current_time_ms:.2f}ms, Sched: {note_time:.2f}ms, Chan: {note['channel']}")
                     self.audio_manager.play_note(note["channel"], note["wav"], current_time_ms)
                     self.game_state["hit_animations"].append({"channel_id": note["channel"], "time": current_time_ms})
                     note["judged"] = True
                     note["hit"] = True 
                
                # Advance index since we handled it
                note_index += 1

            else:
                # MANUAL MODE for Playable Note
                if note["judged"]:
                    # Already hit manualy (or missed)
                    note_index += 1
                else:
                    # Not judged yet.
                    # If time has passed MISS_WINDOW, it's a MISS.
                    if current_time_ms > note_time + MISS_WINDOW:
                        note["judged"] = True
                        note["hit"] = False # Visual miss (doesn't disappear? or maybe distinct visual)
                        self.last_judgment = "MISS"
                        self.game_state["last_judgment"] = "MISS"
                        logging.info(f"Miss! Note passed.")
                        note_index += 1
                    else:
                        # Still valid for hit. Do not increment index so we keep checking it?
                        # ACTUALLY, checking index[0] is correct.
                        # If filtering, we should just break loop if top note is not ready to be missed.
                        break
        
        self.game_state["note_index"] = note_index

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

        elif event.key == pygame.K_v:
            self.display_manager.toggle_layout()
            
        elif event.key == pygame.K_a:
            self.auto_mode = not self.auto_mode
            self.game_state["auto_mode"] = self.auto_mode
            logging.info(f"Auto Mode: {self.auto_mode}")

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
            if note["time"] >= new_time_ms:
                self.game_state["note_index"] = i
                break
            # Logic: If skipped, mark as handled? Or reset?
            # Ideally reset state
            note["judged"] = False
            note["hit"] = False
        
        self.audio_manager.stop_all_sounds()
        self.game_state["hit_animations"].clear()
