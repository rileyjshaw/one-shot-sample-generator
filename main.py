import sys
from pedalboard import load_plugin
from pedalboard.io import AudioFile
from mido import Message
import argparse
import os
import numpy as np

NOTE_NAMES = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']

def midi_note_to_name(note):
    octave = (note // 12) - 1
    name = NOTE_NAMES[note % 12]
    return f"{name}{octave}"

def trim_silence(audio, threshold=1e-3, tail_duration=0.1, sample_rate=44100):
    """Trim silence from both the start and end of an audio array."""
    if audio.ndim == 1:
        audio = np.expand_dims(audio, axis=1)
    elif audio.shape[0] == 2:
        audio = audio.T

    abs_audio = np.max(np.abs(audio), axis=1)
    tail_samples = int(tail_duration * sample_rate)

    # Find the last non-silent sample from the end.
    end_idx = len(abs_audio) - 1
    for i in range(len(abs_audio) - 1, -1, -1):
        if abs_audio[i] > threshold:
            end_idx = i + 1
            break

    # Find the first non-silent sample from the start, but only up to end_idx.
    start_idx = 0
    for i in range(end_idx):
        if abs_audio[i] > threshold:
            start_idx = i
            break

    return audio[start_idx:end_idx + tail_samples]

def main():
    parser = argparse.ArgumentParser(description="Render per-note audio samples from a local instrument plugin.")
    parser.add_argument("vst_path", type=str, help="Path to the instrument plugin.")
    parser.add_argument("--plugin-name", "-p", type=str, default=None, help="Name of the plugin within the instrument file (if multiple plugins are present)")
    parser.add_argument("--output", "-o", type=str, default=None, help="Output subfolder name (defaults to plugin name)")
    parser.add_argument("--max-duration", "-t", type=float, default=12.0, help="Maximum duration in seconds (default: 12.0)")
    parser.add_argument("--note-duration", "-d", type=float, default=None, help="Duration in seconds for which the note should be held (defaults to full duration)")
    parser.add_argument("--notes", "-n", type=str, default=None, help="Comma-separated list of MIDI note numbers to render (default: all notes)")
    parser.add_argument("--keep-silence", "-s", action="store_true", help="Don’t trim silence at the start and end of samples")
    parser.add_argument("--max-attempts", "-a", type=int, default=3, help="Maximum number of attempts if output is silent (default: 3)")
    args = parser.parse_args()

    vst_path = args.vst_path
    plugin_name = args.plugin_name
    output_subfolder = args.output
    max_duration = args.max_duration
    note_duration = args.note_duration
    specific_notes = args.notes and [int(n.strip()) for n in args.notes.split(',')]
    keep_silence = args.keep_silence
    max_attempts = max(1, args.max_attempts)

    if specific_notes is not None:
        for note in specific_notes:
            if note < 0 or note > 127:
                print(f"Invalid note number {note}. Must be between 0 and 127.")
                sys.exit(1)

    if plugin_name:
        instrument = load_plugin(vst_path, plugin_name=plugin_name)
        vst_name = plugin_name
    else:
        instrument = load_plugin(vst_path)
        vst_name = os.path.splitext(os.path.basename(vst_path))[0]

    if not instrument.is_instrument:
        print("The provided plugin is not an instrument.")
        sys.exit(1)

    if not output_subfolder:
        output_subfolder = vst_name

    if note_duration is None:
        note_duration = max_duration

    output_dir = os.path.join('samples', output_subfolder)
    os.makedirs(output_dir, exist_ok=True)

    print("Opening instrument plugin. Edit settings, then close to continue.")
    instrument.show_editor()

    sample_rate = 44100

    for note in range(128):
        if specific_notes is not None and note not in specific_notes:
            continue

        midi_messages = [
            Message("note_on", note=note, velocity=100, time=0),
            Message("note_off", note=note, velocity=0, time=note_duration),
        ]

        for attempt in range(max_attempts):
            rendered_audio = instrument(
                midi_messages,
                duration=max_duration,
                sample_rate=sample_rate,
            )
            if not keep_silence:
                rendered_audio = trim_silence(rendered_audio)

            # Some plugins are tempermental and don’t print audio consistently.
            # Retry if a silent file is detected.
            if np.max(np.abs(rendered_audio)) > 1e-3:
                break
            print(f"Attempt {attempt + 1}/{max_attempts}: Note {note} ({midi_note_to_name(note)}) was silent, retrying...")
            if attempt == max_attempts - 1:
                print(f"Warning: Note {note} ({midi_note_to_name(note)}) was silent after {max_attempts} attempts")

        out_path = os.path.join(output_dir, f"{vst_name} - {note} {midi_note_to_name(note)}.wav")
        with AudioFile(out_path, "w", samplerate=sample_rate, num_channels=2) as f:
            f.write(rendered_audio)
        print(f"Saved {out_path}")

if __name__ == "__main__":
    main()
