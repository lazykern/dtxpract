import pygame

class DisplayManager:
    """Handles all visual rendering for the game."""

    # --- Constants for Visualization ---
    SCREEN_WIDTH = 800
    SCREEN_HEIGHT = 600
    NUM_LANES = 10
    LANE_WIDTH = 40
    NOTE_HIGHWAY_WIDTH = NUM_LANES * LANE_WIDTH
    NOTE_HIGHWAY_X_START = (SCREEN_WIDTH - NOTE_HIGHWAY_WIDTH) // 2
    JUDGMENT_LINE_Y = SCREEN_HEIGHT - 100
    NOTE_HIGHWAY_TOP_Y = 50
    SCROLL_TIME_MS = 1500
    PROGRESS_BAR_WIDTH = 20

    # Colors
    COLOR_BACKGROUND = (0, 0, 0)
    COLOR_LANE_SEPARATOR = (50, 50, 50)
    COLOR_JUDGMENT_LINE = (255, 255, 255)
    COLOR_TEXT = (220, 220, 255)

    LANE_DEFINITIONS = [
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
    CHANNEL_TO_LANE_MAP = {
        channel: i for i, lane in enumerate(LANE_DEFINITIONS) for channel in lane["channels"]
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

    def draw_frame(self, game_state):
        """Draws a single frame of the game."""
        self.screen.fill(self.COLOR_BACKGROUND)
        self._draw_lanes_and_judgment_line()
        self._draw_lane_indicators()
        self._draw_notes(game_state["current_time_ms"], game_state["notes_to_play"], game_state["note_index"])
        self._draw_hit_animations(game_state["current_time_ms"], game_state["hit_animations"])
        self._draw_progress_bar(game_state["current_time_ms"], game_state["song_duration_ms"])
        self._draw_info_text(game_state)
        pygame.display.flip()

    def _draw_lanes_and_judgment_line(self):
        for i in range(self.NUM_LANES + 1):
            x = self.NOTE_HIGHWAY_X_START + i * self.LANE_WIDTH
            pygame.draw.line(self.screen, self.COLOR_LANE_SEPARATOR, (x, self.NOTE_HIGHWAY_TOP_Y), (x, self.JUDGMENT_LINE_Y), 1)
        start_x = self.NOTE_HIGHWAY_X_START
        end_x = self.NOTE_HIGHWAY_X_START + self.NOTE_HIGHWAY_WIDTH
        pygame.draw.line(self.screen, self.COLOR_JUDGMENT_LINE, (start_x, self.JUDGMENT_LINE_Y), (end_x, self.JUDGMENT_LINE_Y), 3)

    def _draw_lane_indicators(self):
        y_pos = self.JUDGMENT_LINE_Y + 5
        for i, lane_def in enumerate(self.LANE_DEFINITIONS):
            x_pos = self.NOTE_HIGHWAY_X_START + i * self.LANE_WIDTH
            rect = pygame.Rect(x_pos + 2, y_pos, self.LANE_WIDTH - 4, 15)
            pygame.draw.rect(self.screen, lane_def["color"], rect)

    def _draw_notes(self, current_time_ms, notes_to_play, note_index):
        highway_height = self.JUDGMENT_LINE_Y - self.NOTE_HIGHWAY_TOP_Y
        for i in range(note_index, len(notes_to_play)):
            note_time, channel_id, _ = notes_to_play[i]
            time_until_hit = note_time - current_time_ms
            if time_until_hit > self.SCROLL_TIME_MS:
                break
            if time_until_hit >= 0:
                progress = 1.0 - (time_until_hit / self.SCROLL_TIME_MS)
                y_pos = self.NOTE_HIGHWAY_TOP_Y + (progress * highway_height)
                if channel_id in self.CHANNEL_TO_LANE_MAP:
                    lane_index = self.CHANNEL_TO_LANE_MAP[channel_id]
                    color = self.NOTE_TYPE_COLORS.get(channel_id, self.LANE_DEFINITIONS[lane_index]["color"])
                    x_pos = self.NOTE_HIGHWAY_X_START + lane_index * self.LANE_WIDTH
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
            if channel_id in self.CHANNEL_TO_LANE_MAP:
                lane_index = self.CHANNEL_TO_LANE_MAP[channel_id]
                note_color = self.NOTE_TYPE_COLORS.get(channel_id, self.LANE_DEFINITIONS[lane_index]["color"])
                color = tuple(min(c + 80, 255) for c in note_color)
                x_pos = self.NOTE_HIGHWAY_X_START + lane_index * self.LANE_WIDTH
                rect = pygame.Rect(x_pos, self.JUDGMENT_LINE_Y - 50, self.LANE_WIDTH, 50)
                pygame.draw.rect(self.screen, color, rect)

    def _draw_progress_bar(self, current_time_ms, song_duration_ms):
        if song_duration_ms > 0:
            progress_bar_x = self.NOTE_HIGHWAY_X_START + self.NOTE_HIGHWAY_WIDTH + 10
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
        ]
        for i, text in enumerate(texts):
            surface = self.font.render(text, True, self.COLOR_TEXT)
            self.screen.blit(surface, (10, 10 + i * 30))
