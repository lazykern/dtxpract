import pygame

class DisplayManager:
    """Handles all visual rendering for the game."""

    # --- Constants for Visualization ---
    SCREEN_WIDTH = 800
    SCREEN_HEIGHT = 600
    JUDGMENT_LINE_Y = SCREEN_HEIGHT - 100
    NOTE_HIGHWAY_TOP_Y = 50
    SCROLL_TIME_MS = 1500
    PROGRESS_BAR_WIDTH = 20
    LANE_WIDTH = 40

    # Colors
    COLOR_BACKGROUND = (0, 0, 0)
    COLOR_LANE_SEPARATOR = (50, 50, 50)
    COLOR_JUDGMENT_LINE = (255, 255, 255)
    COLOR_TEXT = (220, 220, 255)

    # Standard DTX Layout
    LAYOUT_STANDARD = [
        {"name": "L.Cym", "channels": ["1A"], "color": (255, 105, 180)},
        {"name": "H.H.", "channels": ["11", "18"], "color": (0, 180, 255)},
        {"name": "Snare", "channels": ["12"], "color": (255, 0, 100)},
        {"name": "L.Foot", "channels": ["1B", "1C"], "color": (255, 255, 255)},
        {"name": "H.Tom", "channels": ["14"], "color": (0, 220, 0)},
        {"name": "Kick", "channels": ["13"], "color": (255, 255, 255)},
        {"name": "L.Tom", "channels": ["15"], "color": (255, 0, 0)},
        {"name": "F.Tom", "channels": ["17"], "color": (255, 165, 0)},
        {"name": "R.Cym", "channels": ["16"], "color": (0, 180, 255)},
        {"name": "Ride", "channels": ["19"], "color": (0, 180, 255)},
    ]

    # GM Sorted Layout
    # Order: Kick(36), Snare(38), F.Tom(41), H.H.Closed(42), Pedal(44), L.Tom(45), H.H.Open(46), H.Tom(48), Crash(49), Ride(51), R.Cym(57)
    LAYOUT_GM = [
        {"name": "Kick", "channels": ["13"], "color": (255, 255, 255), "is_black_key": False},     # 36 C1
        {"name": "Snare", "channels": ["12"], "color": (255, 0, 100), "is_black_key": False},      # 38 D1
        {"name": "F.Tom", "channels": ["17"], "color": (255, 165, 0), "is_black_key": False},      # 41 F1
        {"name": "H.H.C", "channels": ["11"], "color": (0, 180, 255), "is_black_key": True},       # 42 F#1
        {"name": "Pedal", "channels": ["1B", "1C"], "color": (255, 255, 255), "is_black_key": True},# 44 G#1
        {"name": "L.Tom", "channels": ["15"], "color": (255, 0, 0), "is_black_key": False},        # 45 A1
        {"name": "H.H.O", "channels": ["18"], "color": (0, 200, 255), "is_black_key": True},       # 46 A#1
        {"name": "H.Tom", "channels": ["14"], "color": (0, 220, 0), "is_black_key": False},        # 48 C2
        {"name": "L.Cym", "channels": ["1A"], "color": (255, 105, 180), "is_black_key": True},     # 49 C#2
        {"name": "Ride", "channels": ["19"], "color": (0, 180, 255), "is_black_key": True},        # 51 D#2
        {"name": "R.Cym", "channels": ["16"], "color": (0, 180, 255), "is_black_key": False},      # 57 A2
    ]

    LAYOUTS = {
        "STANDARD": LAYOUT_STANDARD,
        "GM": LAYOUT_GM
    }

    NOTE_TYPE_COLORS = {
        "18": (100, 220, 255), "1B": (255, 105, 180),
        "13": (200, 0, 200), "1C": (200, 0, 200),
    }

    def __init__(self, dtx_data):
        self.dtx = dtx_data
        self.screen = pygame.display.set_mode((self.SCREEN_WIDTH, self.SCREEN_HEIGHT))
        pygame.display.set_caption(f"Playing: {self.dtx.title} - {self.dtx.artist}")
        self.font = pygame.font.Font(None, 28)
        self.small_font = pygame.font.Font(None, 24)
        
        self.current_layout_name = "STANDARD"
        self._update_layout()

    def _update_layout(self):
        """Updates internal mappings based on the current layout."""
        self.lanes = self.LAYOUTS[self.current_layout_name]
        self.num_lanes = len(self.lanes)
        self.note_highway_width = self.num_lanes * self.LANE_WIDTH
        self.note_highway_x_start = (self.SCREEN_WIDTH - self.note_highway_width) // 2

        self.channel_to_lane_map = {
            channel: i for i, lane in enumerate(self.lanes) for channel in lane["channels"]
        }

    def toggle_layout(self):
        """Switches between available layouts."""
        names = list(self.LAYOUTS.keys())
        idx = names.index(self.current_layout_name)
        self.current_layout_name = names[(idx + 1) % len(names)]
        self._update_layout()

    def draw_frame(self, game_state):
        """Draws a single frame of the game."""
        self.screen.fill(self.COLOR_BACKGROUND)
        self._draw_lanes_and_judgment_line()
        
        pressed = game_state.get("pressed_channels", set())
        self._draw_lane_indicators_with_state(pressed)
        
        self._draw_notes(game_state["current_time_ms"], game_state["notes_to_play"], game_state["note_index"])
        self._draw_hit_animations(game_state["current_time_ms"], game_state["hit_animations"])
        self._draw_progress_bar(game_state["current_time_ms"], game_state["song_duration_ms"])
        self._draw_info_text(game_state)
        pygame.display.flip()

    def _draw_lanes_and_judgment_line(self):
        # Draw lane backgrounds for black keys
        for i, lane in enumerate(self.lanes):
            if lane.get("is_black_key", False):
                x_start = self.note_highway_x_start + i * self.LANE_WIDTH
                y_top = self.NOTE_HIGHWAY_TOP_Y
                height = self.JUDGMENT_LINE_Y - self.NOTE_HIGHWAY_TOP_Y
                
                bg_rect = pygame.Rect(x_start, y_top, self.LANE_WIDTH, height)
                
                # Darker solid background as requested
                pygame.draw.rect(self.screen, (20, 20, 35), bg_rect)

        # Draw separators
        for i in range(self.num_lanes + 1):
            x = self.note_highway_x_start + i * self.LANE_WIDTH
            pygame.draw.line(self.screen, self.COLOR_LANE_SEPARATOR, (x, self.NOTE_HIGHWAY_TOP_Y), (x, self.JUDGMENT_LINE_Y), 1)
        start_x = self.note_highway_x_start
        end_x = self.note_highway_x_start + self.note_highway_width
        pygame.draw.line(self.screen, self.COLOR_JUDGMENT_LINE, (start_x, self.JUDGMENT_LINE_Y), (end_x, self.JUDGMENT_LINE_Y), 3)

    def _draw_lane_indicators(self):
        y_pos = self.JUDGMENT_LINE_Y + 5
        pressed_channels = getattr(self, "current_pressed_channels", set()) 
        # Hack: The display manager doesn't strictly have access to game_state in this method signature
        # But we pass game_state to draw_frame. let's fetch it from there or update signature.
        # Actually simplest is to handle it in draw_frame or update this method signature.
        # But wait, draw_frame calls this. I need to pass the pressed state.
        pass

    def _draw_lane_indicators_with_state(self, pressed_channels):
        y_pos = self.JUDGMENT_LINE_Y + 5
        for i, lane_def in enumerate(self.lanes):
            x_pos = self.note_highway_x_start + i * self.LANE_WIDTH
            
            # Check if any channel in this lane is pressed
            is_pressed = any(ch in pressed_channels for ch in lane_def["channels"])
            
            if is_pressed:
                # Draw Beam / Highlight
                # Beam effect
                beam_rect = pygame.Rect(x_pos, self.NOTE_HIGHWAY_TOP_Y, self.LANE_WIDTH, self.JUDGMENT_LINE_Y - self.NOTE_HIGHWAY_TOP_Y)
                s = pygame.Surface((self.LANE_WIDTH, beam_rect.height), pygame.SRCALPHA)
                s.fill((255, 255, 255, 40)) # Light transparent white
                self.screen.blit(s, (x_pos, self.NOTE_HIGHWAY_TOP_Y))
                
                # Active Indicator
                rect = pygame.Rect(x_pos + 2, y_pos, self.LANE_WIDTH - 4, 15)
                pygame.draw.rect(self.screen, (255, 255, 255), rect) # Bright white when pressed
            else:
                rect = pygame.Rect(x_pos + 2, y_pos, self.LANE_WIDTH - 4, 15)
                pygame.draw.rect(self.screen, lane_def["color"], rect)
            
            # Draw lane name
            text = self.small_font.render(lane_def["name"], True, (150, 150, 150))
            text = pygame.transform.rotate(text, 90)
            text_rect = text.get_rect(center=(x_pos + self.LANE_WIDTH // 2, y_pos + 40))
            self.screen.blit(text, text_rect)

    def _draw_notes(self, current_time_ms, notes_to_play, note_index):
        highway_height = self.JUDGMENT_LINE_Y - self.NOTE_HIGHWAY_TOP_Y
        for i in range(note_index, len(notes_to_play)):
            note = notes_to_play[i]
            if note.get("hit", False):
                continue
                
            note_time = note["time"]
            channel_id = note["channel"]
            
            time_until_hit = note_time - current_time_ms
            if time_until_hit > self.SCROLL_TIME_MS:
                break
            if time_until_hit >= 0:
                progress = 1.0 - (time_until_hit / self.SCROLL_TIME_MS)
                y_pos = self.NOTE_HIGHWAY_TOP_Y + (progress * highway_height)
                if channel_id in self.channel_to_lane_map:
                    lane_index = self.channel_to_lane_map[channel_id]
                    color = self.NOTE_TYPE_COLORS.get(channel_id, self.lanes[lane_index]["color"])
                    x_pos = self.note_highway_x_start + lane_index * self.LANE_WIDTH
                    note_rect = pygame.Rect(x_pos + 2, y_pos - 3, self.LANE_WIDTH - 4, 7)
                    if channel_id == "18":
                        pygame.draw.rect(self.screen, color, note_rect, 2)
                    elif channel_id == "1B":
                        pedal_rect = pygame.Rect(x_pos + 2, y_pos - 1, self.LANE_WIDTH - 4, 3)
                        pygame.draw.rect(self.screen, color, pedal_rect)
                    else:
                        pygame.draw.rect(self.screen, color, note_rect)

    def _draw_hit_animations(self, current_time_ms, hit_animations):
        ANIMATION_DURATION_MS = 80
        for anim in hit_animations[:]:
            if current_time_ms - anim["time"] > ANIMATION_DURATION_MS:
                hit_animations.remove(anim)
                continue
            channel_id = anim["channel_id"]
            if channel_id in self.channel_to_lane_map:
                lane_index = self.channel_to_lane_map[channel_id]
                note_color = self.NOTE_TYPE_COLORS.get(channel_id, self.lanes[lane_index]["color"])
                color = tuple(min(c + 80, 255) for c in note_color)
                x_pos = self.note_highway_x_start + lane_index * self.LANE_WIDTH
                rect = pygame.Rect(x_pos, self.JUDGMENT_LINE_Y - 50, self.LANE_WIDTH, 50)
                pygame.draw.rect(self.screen, color, rect)

    def _draw_progress_bar(self, current_time_ms, song_duration_ms):
        if song_duration_ms > 0:
            progress_bar_x = self.note_highway_x_start + self.note_highway_width + 10
            progress_bar_height = self.JUDGMENT_LINE_Y - self.NOTE_HIGHWAY_TOP_Y
            bg_rect = pygame.Rect(progress_bar_x, self.NOTE_HIGHWAY_TOP_Y, self.PROGRESS_BAR_WIDTH, progress_bar_height)
            pygame.draw.rect(self.screen, self.COLOR_LANE_SEPARATOR, bg_rect)
            progress = current_time_ms / song_duration_ms
            fill_height = progress * progress_bar_height
            fill_rect = pygame.Rect(progress_bar_x, self.JUDGMENT_LINE_Y - fill_height, self.PROGRESS_BAR_WIDTH, fill_height)
            pygame.draw.rect(self.screen, (180, 180, 40), fill_rect)

    def _draw_info_text(self, s):
        texts = [
            f"Time: {s['current_time_ms'] / 1000.0:.2f}s / {s['song_duration_ms'] / 1000.0:.2f}s",
            f"Notes: {s['note_index']} / {len(s['notes_to_play'])}",
            f"BPM: {self.dtx.bpm:.2f}",
            f"BGM Vol: {s['bgm_volume'] * 100:.0f}%",
            f"SE Vol: {s['se_volume'] * 100:.0f}%",
            f"Layout: {self.current_layout_name} (Toggle: V)",
            f"Mode: {'AUTO' if s.get('auto_mode', True) else 'MANUAL'} (Toggle: A)",
            f"Judgment: {s.get('last_judgment', '')}",
            f"{s.get('midi_status', 'MIDI: ???')}",
        ]
        for i, text in enumerate(texts):
            surface = self.font.render(text, True, self.COLOR_TEXT)
            self.screen.blit(surface, (10, 10 + i * 30))
