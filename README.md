# One-shot sample generator

Render per-note audio samples from a local VST or AU instrument plugin.

## Usage

```bash
# Clone the repository
git clone https://github.com/rileyjshaw/one-shot-sample-generator.git
cd one-shot-sample-generator

# Set up Python environment
python -m venv venv
source venv/bin/activate  # On Windows, use venv\Scripts\activate
pip install -r requirements.txt

# Run the script
python main.py path/to/instrument.vst3  # On Mac, the plugin path is typically ~/Library/Audio/Plug-Ins/VST3/
```

## Options

```bash
--plugin-name, -p    Name of the plugin within the instrument file (if multiple plugins are present)
--output, -o         Output subfolder name (defaults to plugin name)
--max-duration, -t   Maximum duration in seconds (default: 12.0)
--note-duration, -d  Duration in seconds for which the note should be held (defaults to full duration)
--notes, -n          Comma-separated list of MIDI note numbers to render (default: all notes)
--keep-silence, -s   Don’t trim silence at the start and end of samples
--max-attempts, -a   Maximum number of attempts if output is silent (default: 3)
```

## License

[GNU General Public License v3.0](https://www.gnu.org/licenses/gpl-3.0.en.html)
