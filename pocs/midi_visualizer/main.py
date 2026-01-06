

import pygame
import mido

def main():
    pygame.init()

    # Screen dimensions
    screen_width = 1024
    screen_height = 300
    screen = pygame.display.set_mode((screen_width, screen_height))
    pygame.display.set_caption("MIDI Visualizer")

    # Colors
    white = (255, 255, 255)
    black = (0, 0, 0)
    gray = (150, 150, 150)
    blue = (100, 100, 255)

    # --- Keyboard Drawing Setup ---
    # Map MIDI note numbers to rectangles
    key_map = {}
    pressed_keys = set()

    # Standard piano layout
    white_key_notes = [i for i in range(128) if (i % 12) not in [1, 3, 6, 8, 10]]
    black_key_notes = [i for i in range(128) if (i % 12) in [1, 3, 6, 8, 10]]

    # visible keyboard range
    start_note = 21  # A0
    end_note = 108 # C8
    
    visible_white_keys = [note for note in white_key_notes if start_note <= note <= end_note]
    
    if not visible_white_keys:
        print("No white keys in the specified range.")
        return

    white_key_width = screen_width / len(visible_white_keys)
    white_key_height = screen_height
    black_key_width = white_key_width * 0.65
    black_key_height = screen_height * 0.6

    # Create white key rects
    for i, note in enumerate(visible_white_keys):
        rect = pygame.Rect(i * white_key_width, 0, white_key_width, white_key_height)
        key_map[note] = {'rect': rect, 'color': white, 'type': 'white'}

    # Create black key rects
    for i, note in enumerate(visible_white_keys[:-1]):
        # Check if a black key should be between this white key and the next
        if (note + 1) in black_key_notes:
            black_note = note + 1
            if start_note <= black_note <= end_note:
                rect = pygame.Rect(i * white_key_width + (white_key_width - black_key_width/2), 0, black_key_width, black_key_height)
                key_map[black_note] = {'rect': rect, 'color': black, 'type': 'black'}

    # --- MIDI setup with mido ---
    midi_input = None
    try:
        inport_names = mido.get_input_names()
        if not inport_names:
            print("No MIDI input devices found.")
        else:
            print("Available MIDI input devices:")
            for name in inport_names:
                print(f"  - {name}")
            
            # Attempt to open the first port that contains "Minilab" or just the first port
            port_name = next((name for name in inport_names if "Minilab" in name), inport_names[0])
            
            print(f"Opening MIDI port: {port_name}")
            midi_input = mido.open_input(port_name)
            # Clear any stale messages in the input buffer
            for _ in midi_input.iter_pending():
                pass

    except Exception as e:
        print(f"Error opening MIDI port: {e}")


    # --- Main Loop ---
    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        # --- MIDI Input ---
        if midi_input:
            for msg in midi_input.iter_pending():
                if msg.type == 'note_on' and msg.velocity > 0:
                    pressed_keys.add(msg.note)
                elif msg.type == 'note_off' or (msg.type == 'note_on' and msg.velocity == 0):
                    if msg.note in pressed_keys:
                        pressed_keys.remove(msg.note)

        # --- Drawing ---
        screen.fill(gray)

        # Draw white keys first
        for note, key_data in key_map.items():
            if key_data['type'] == 'white':
                color = blue if note in pressed_keys else key_data['color']
                pygame.draw.rect(screen, color, key_data['rect'])
                pygame.draw.rect(screen, black, key_data['rect'], 1) # border

        # Draw black keys on top
        for note, key_data in key_map.items():
            if key_data['type'] == 'black':
                color = blue if note in pressed_keys else key_data['color']
                pygame.draw.rect(screen, color, key_data['rect'])
                pygame.draw.rect(screen, black, key_data['rect'], 1) # border

        pygame.display.flip()

    # --- Cleanup ---
    if midi_input:
        midi_input.close()
    pygame.quit()

if __name__ == '__main__':
    main()

