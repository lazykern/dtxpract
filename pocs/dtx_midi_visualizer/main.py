
import pygame
import time
import sys
import os
from dtx import Dtx

# --- Mappings and Constants ---
DTX_TO_GM_MAP = {
    '11': 36, '12': 38, '13': 48, '14': 51, '15': 41,
    '16': 49, '17': 45, '18': 46, '1A': 42, '1B': 43, '1C': 40,
}

NOTE_VISUAL_DURATION_MS = 100
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 600
KEYBOARD_HEIGHT = 100
NOTE_SPEED = 0.3  # pixels per millisecond
VISIBLE_TIME_WINDOW_MS = 2000  # Show notes up to 2 seconds in the future
JUDGEMENT_LINE_Y = SCREEN_HEIGHT - KEYBOARD_HEIGHT - 20 # 20px above the keyboard

def get_note_events_from_dtx(dtx_file):
    """Parses a DTX file and returns a sorted list of (timestamp_ms, midi_note) events."""
    d = Dtx(dtx_file)
    d.parse()
    note_events = []
    for timestamp_ms, channel, _ in d.timed_notes:
        midi_note = DTX_TO_GM_MAP.get(channel.upper())
        if midi_note:
            note_events.append((timestamp_ms, midi_note))
    note_events.sort()
    return note_events

def main():
    pygame.init()

    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("DTX MIDI Visualizer")

    # Colors
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    GRAY = (30, 30, 30)
    BLUE = (100, 100, 255)
    RED = (255, 50, 50)
    NOTE_COLOR = (200, 50, 200) # Magenta for falling notes

    # --- Keyboard Drawing Setup ---
    key_map = {}
    pressed_keys = set()
    note_off_events = []

    white_key_notes = [i for i in range(128) if (i % 12) not in [1, 3, 6, 8, 10]]
    start_note, end_note = 21, 108
    visible_white_keys = [note for note in white_key_notes if start_note <= note <= end_note]
    
    if not visible_white_keys:
        print("No white keys in the specified range.")
        return

    white_key_width = SCREEN_WIDTH / len(visible_white_keys)
    black_key_width = white_key_width * 0.65
    keyboard_y_pos = SCREEN_HEIGHT - KEYBOARD_HEIGHT

    for i, note in enumerate(visible_white_keys):
        rect = pygame.Rect(i * white_key_width, keyboard_y_pos, white_key_width, KEYBOARD_HEIGHT)
        key_map[note] = {'rect': rect, 'color': WHITE, 'type': 'white'}

    black_key_notes_in_range = [note for note in range(start_note, end_note + 1) if (note % 12) in [1, 3, 6, 8, 10]]
    for note in black_key_notes_in_range:
        preceding_white_key_index = -1
        for i, wn in enumerate(visible_white_keys):
            if wn > note: break
            preceding_white_key_index = i
        
        if preceding_white_key_index != -1:
            x_pos = (preceding_white_key_index + 1) * white_key_width - (black_key_width / 2)
            rect = pygame.Rect(x_pos, keyboard_y_pos, black_key_width, KEYBOARD_HEIGHT * 0.6)
            key_map[note] = {'rect': rect, 'color': BLACK, 'type': 'black'}

    # --- DTX Loading ---
    script_dir = os.path.dirname(__file__) if '__file__' in locals() else '.'
    default_dtx_path = os.path.join(script_dir, 'song.dtx')
    dtx_path = sys.argv[1] if len(sys.argv) > 1 else default_dtx_path

    try:
        print(f"Loading DTX file: {dtx_path}")
        song_notes = get_note_events_from_dtx(dtx_path)
        if not song_notes:
            print("No drum notes found in the DTX file.")
            return
        last_note_time = song_notes[-1][0] if song_notes else 0
    except Exception as e:
        print(f"Error loading DTX file: {e}")
        return

    # --- Main Loop ---
    clock = pygame.time.Clock()
    start_time = pygame.time.get_ticks()
    running = True
    note_index = 0

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        current_time = pygame.time.get_ticks() - start_time

        # --- Note Player Logic ---
        while note_index < len(song_notes) and song_notes[note_index][0] <= current_time:
            _, note = song_notes[note_index]
            pressed_keys.add(note)
            note_off_events.append((current_time + NOTE_VISUAL_DURATION_MS, note))
            note_index += 1

        note_off_events.sort()
        while note_off_events and note_off_events[0][0] <= current_time:
            _, note_to_turn_off = note_off_events.pop(0)
            if note_to_turn_off in pressed_keys:
                pressed_keys.remove(note_to_turn_off)
        
        # --- Drawing ---
        screen.fill(GRAY)

        # Draw judgment line
        pygame.draw.line(screen, RED, (0, JUDGEMENT_LINE_Y), (SCREEN_WIDTH, JUDGEMENT_LINE_Y), 2)
        
        # Draw falling notes
        for timestamp_ms, note in song_notes:
            time_delta = timestamp_ms - current_time
            if 0 < time_delta < VISIBLE_TIME_WINDOW_MS:
                key_data = key_map.get(note)
                if key_data:
                    y_pos = JUDGEMENT_LINE_Y - (time_delta * NOTE_SPEED)
                    note_rect = pygame.Rect(key_data['rect'].x, y_pos, key_data['rect'].width, 5)
                    pygame.draw.rect(screen, NOTE_COLOR, note_rect)
        
        # Draw keyboard
        for note, key_data in key_map.items():
            if key_data['type'] == 'white':
                color = BLUE if note in pressed_keys else key_data['color']
                pygame.draw.rect(screen, color, key_data['rect'])
                pygame.draw.rect(screen, BLACK, key_data['rect'], 1)

        for note, key_data in key_map.items():
            if key_data['type'] == 'black':
                color = BLUE if note in pressed_keys else key_data['color']
                pygame.draw.rect(screen, color, key_data['rect'])

        pygame.display.flip()

        # Exit condition
        if note_index >= len(song_notes) and not note_off_events:
            time.sleep(1)
            running = False

        clock.tick(120)

    pygame.quit()

if __name__ == '__main__':
    main()
