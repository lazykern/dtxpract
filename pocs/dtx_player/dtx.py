import os
import re
import logging


def base36_to_int(s):
    """Converts a base36 string (0-9, A-Z) to an integer."""
    try:
        return int(s, 36)
    except (ValueError, TypeError):
        return 0


class Dtx:
    """
    Parses a .dtx file, processes its metadata, and calculates the precise
    timing of all musical events, including notes and BPM changes.
    """

    # Channels that do not represent playable notes and should be ignored
    # when building the list of timed events. This includes visual and
    # system channels for things like bar lines and BGA control.
    NON_NOTE_CHANNELS = {
        # Visual Layers & Control
        "04", "07", "54", "5A", "C4", "C7",
        "55", "56", "57", "58", "59", "60",
        "D5", "D6", "D7", "D8", "D9", "DA", "DB", "DC", "DD", "DE", "DF",
        # System (Bar lines, visibility toggles, etc.)
        "50", "51", "C1", "C2",
        # Sound Effect (SE) channels - these are autoplay sounds, not playable notes.
        "61", "62", "63", "64", "65", "66", "67", "68", "69",
        "70", "71", "72", "73", "74", "75", "76", "77", "78", "79",
        "80", "81", "82", "83", "84", "85", "86", "87", "88", "89",
        "90", "91", "92",
    }

    def __init__(self, dtx_path):
        """
        Initializes the Dtx object with the path to the .dtx file.

        Args:
            dtx_path (str): The full path to the .dtx file.

        Raises:
            FileNotFoundError: If the .dtx file does not exist.
        """
        if not os.path.exists(dtx_path):
            raise FileNotFoundError(f"DTX file not found: {dtx_path}")
        self.dtx_path = dtx_path
        self.directory = os.path.dirname(dtx_path) or "."

        # Metadata with default values
        self.title = "Untitled"
        self.artist = "Unknown"
        self.bpm = 120.0

        # Resource definitions
        self.wav_files = {}  # Maps WAV ID (str) to its file path
        self.bpm_changes = {}  # Maps BPM ID (str) to a BPM value (float)
        self.bar_length_changes = {}  # Maps bar number to a length multiplier (float)
        self.wav_volumes = {}  # Maps WAV ID to volume (0-100) from #VOLUME
        self.bgm_wav_id = None
        self.bgm_start_time_ms = 0.0

        # The final calculated event list
        self.timed_notes = []  # List of (time_in_ms, wav_id_str)

    def _split_line(self, line):
        """
        Helper to robustly split a DTX command line into a key and value.
        Handles commands with and without values.
        """
        # Prioritize colon as it's a more definitive separator
        if ":" in line:
            key, value = line.split(":", 1)
            return key, value
        # Fallback to the first space for commands like '#BPM 120'
        elif " " in line:
            key, value = line.split(" ", 1)
            return key, value
        # Handle commands with no value, like '#END'
        return line, ""

    def parse(self):
        """
        Parses the DTX file in two main stages:
        1. First Pass: Gathers all definitions (metadata, WAVs, BPMs, bar lengths).
        2. Second Pass: Processes the timeline, calculating the precise time
           for each event based on the current BPM and bar lengths.
        """
        logging.info(f"--- Pass 1: Parsing '{os.path.basename(self.dtx_path)}' ---")

        raw_events = []

        # --- First Pass: Gather all definitions from the file ---
        # Try to read the file with multiple encodings and choose the one that
        # produces the most valid-looking DTX command lines (starting with '#').
        best_content = None
        best_encoding = None
        max_command_lines = 0

        # Common encodings for DTX files, with cp932 (Shift-JIS) often being correct.
        for encoding in ["cp932", "utf-16-le", "utf-8-sig", "utf-8"]:
            try:
                with open(self.dtx_path, "r", encoding=encoding) as f:
                    lines = f.readlines()

                # Heuristic: The correct encoding should yield many command lines.
                command_lines = sum(1 for line in lines if line.strip().startswith("#"))

                if command_lines > max_command_lines:
                    max_command_lines = command_lines
                    best_content = lines
                    best_encoding = encoding

            except (UnicodeDecodeError, UnicodeError):
                continue  # This encoding is incorrect, try the next one.
            except Exception as e:
                logging.error(f"An unexpected error occurred while reading with {encoding}: {e}")

        if not best_content:
            logging.error("Could not read or decode the file with any supported encodings.")
            return

        content = best_content
        logging.info(
            f"Successfully read file using encoding '{best_encoding}' ({max_command_lines} command lines found)."
        )

        for line in content:
            line = line.strip()
            if not line or not line.startswith("#"):
                continue

            raw_key, raw_value = self._split_line(line[1:])

            key = raw_key.strip().upper()
            value = raw_value.strip().split(";")[0].strip()  # Remove comments

            if key == "TITLE":
                self.title = value
            elif key == "ARTIST":
                self.artist = value
            elif key == "BPM" and value:
                try:
                    self.bpm = float(value)
                except ValueError:
                    logging.warning(f"Invalid BPM value '{value}'")
            elif key.startswith("WAV") and value:
                # Normalize path separators to handle DTX files from Windows
                normalized_value = value.replace("\\", "/")
                self.wav_files[key[3:]] = os.path.join(self.directory, normalized_value)
            elif key == "BGMWAV" and value:
                self.bgm_wav_id = value
            elif key.startswith("BPM") and len(key) > 3 and value:
                try:
                    self.bpm_changes[key[3:]] = float(value)
                except ValueError:
                    logging.warning(f"Invalid BPM change value '{value}'")
            elif key.startswith("VOLUME") and len(key) > 6 and value:
                wav_id = key[6:]
                try:
                    self.wav_volumes[wav_id] = int(value)
                except (ValueError, TypeError):
                    logging.warning(
                        f"Invalid VOLUME value '{value}' for WAV ID {wav_id}"
                    )
            # Check for note/event data lines (e.g., #00108: ...)
            elif len(key) == 5 and re.match(r"^\d{3}[0-9A-Z]{2}$", key):
                bar_num = int(key[0:3])
                channel = key[3:5]

                # Handle bar length changes, which are not standard chip events
                if channel == "02":
                    if value:
                        try:
                            # Bar length is a direct float value in the DTX file
                            self.bar_length_changes[bar_num] = float(value)
                        except (ValueError, TypeError):
                            logging.warning(
                                f"Invalid bar length value '{value}' for bar {bar_num}"
                            )
                    continue  # Do not process as a note event

                # Ignore other non-note channels (visual, system, etc.)
                if channel in self.NON_NOTE_CHANNELS:
                    continue

                if not value:
                    continue

                notes = [value[i : i + 2] for i in range(0, len(value), 2)]
                if not notes:
                    continue

                total_notes = len(notes)
                for i, note_val in enumerate(notes):
                    if note_val != "00":
                        raw_events.append(
                            {
                                "bar": bar_num,
                                "channel": channel,
                                "pos": i,
                                "total_pos": total_notes,
                                "val": note_val,
                            }
                        )
        
        logging.info(f"Discovered Metadata -> Title: '{self.title}', Artist: '{self.artist}', Base BPM: {self.bpm}")

        # If BGMWAV is not specified, default to WAV01, a common convention
        if not self.bgm_wav_id and "01" in self.wav_files:
            self.bgm_wav_id = "01"
            logging.info(f"BGMWAV not specified, defaulting to WAV01.")

        logging.info(
            f"Found {len(self.wav_files)} WAVs, {len(self.bar_length_changes)} bar length changes, and {len(raw_events)} raw events."
        )

        # --- Second Pass: Calculate event timings ---
        logging.info("--- Pass 2: Calculating event timings ---")
        
        # Pre-calculate the starting beat of each bar to handle time signature changes
        max_bar = 0
        if raw_events:
            max_bar = max(e["bar"] for e in raw_events)

        bar_start_beats = {0: 0.0}
        for i in range(max_bar + 1):
            bar_length_multiplier = self.bar_length_changes.get(i, 1.0)
            beats_in_bar = 4.0 * bar_length_multiplier
            bar_start_beats[i + 1] = bar_start_beats[i] + beats_in_bar

        # Annotate each event with its precise global beat number
        for event in raw_events:
            bar_num = event["bar"]
            # Get the length of the specific bar the event is in
            bar_len_multiplier = self.bar_length_changes.get(bar_num, 1.0)
            beats_in_this_bar = 4.0 * bar_len_multiplier

            # Position within the bar (0.0 to 1.0) * beats in this bar
            event_beat_in_bar = (event["pos"] / event["total_pos"]) * beats_in_this_bar

            # Global beat is the sum of beats before this bar + beat pos in this bar
            event["global_beat"] = bar_start_beats[bar_num] + event_beat_in_bar

        # Sort events by their calculated global beat to process them chronologically
        raw_events.sort(key=lambda x: x["global_beat"])

        current_time_s = 0.0
        current_bpm = self.bpm
        last_event_beat = 0.0
        first_bgm_event_processed = False

        for event in raw_events:
            # Calculate time elapsed since the last event using the current BPM
            delta_beats = event["global_beat"] - last_event_beat
            if current_bpm > 0:
                delta_time_s = delta_beats * (60.0 / current_bpm)
            else:
                delta_time_s = 0 # Avoid division by zero if BPM is 0
            event_time_s = current_time_s + delta_time_s

            # Process the event based on its channel to see if it's a note or a BPM change
            channel, value = event["channel"], event["val"]
            
            new_bpm = -1

            if channel == "01":  # BGM event
                if not first_bgm_event_processed:
                    self.bgm_start_time_ms = event_time_s * 1000
                    first_bgm_event_processed = True
                    logging.info(f"BGM start time detected at beat {event['global_beat']:.2f} ({self.bgm_start_time_ms:.2f}ms)")
                # BGM events aren't notes, so we don't add them to the list.
            elif channel == "03":  # Direct BPM change (hexadecimal value)
                try:
                    new_bpm = float(int(value, 16))
                except (ValueError, TypeError):
                    logging.warning(f"Invalid direct BPM value '{value}'")
            elif channel == "08":  # BPM change from predefined list
                if value in self.bpm_changes:
                    new_bpm = self.bpm_changes[value]
            else:  # Any other channel is a note.
                self.timed_notes.append((event_time_s * 1000, channel, value))

            # If BPM changed, log it and update state
            if new_bpm != -1 and new_bpm != current_bpm:
                logging.info(f"BPM change at beat {event['global_beat']:.2f} ({event_time_s*1000:.2f}ms): {current_bpm:.2f} -> {new_bpm:.2f}")
                current_bpm = new_bpm

            # Update state for the next iteration
            current_time_s = event_time_s
            last_event_beat = event["global_beat"]

        self.timed_notes.sort()
        logging.info(f"Successfully parsed {len(self.timed_notes)} timed notes.")
