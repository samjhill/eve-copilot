# EVE Copilot

A log-driven voice assistant for EVE Online that monitors game events and provides real-time voice alerts with **high-quality, natural-sounding text-to-speech**.

## Features

- **Real-time Log Monitoring**: Watches EVE Online log files for game events
- **Enhanced Voice Alerts**: Multiple TTS engines for natural-sounding notifications
- **Configurable Rules**: Customizable thresholds and cooldowns
- **Scenario Profiles**: Pre-configured rules for different activities (General PVE, Abyssal Running)
- **Cross-platform**: Works on macOS and Windows

## TTS Engine Options

EVE Copilot now supports multiple text-to-speech engines for better voice quality:

### 🎯 **Edge TTS (Recommended)**
- **Quality**: Neural voices with natural intonation
- **Availability**: Works offline, no internet required
- **Voices**: 400+ voices in 140+ languages
- **Best for**: Most users, highest quality experience

### 🌐 **Google TTS**
- **Quality**: High-quality online voices
- **Availability**: Requires internet connection
- **Languages**: 50+ languages supported
- **Best for**: Users with stable internet, alternative to Edge TTS

### 💻 **pyttsx3 (Fallback)**
- **Quality**: Basic system voices
- **Availability**: Works offline, uses system voices
- **Voices**: Depends on operating system
- **Best for**: Fallback when other engines fail

## Quick Start

1. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure EVE Logs**:
   - Edit `config/app.yml` and set `eve_logs_path` to your EVE logs directory
   - **IMPORTANT**: Enable combat logging in EVE Online for low health alerts to work!

3. **Test TTS Engines**:
   ```bash
   # Test all TTS engines
   python tts_test.py
   
   # List available Edge TTS voices
   python tts_test.py voices
   ```

4. **Run the Application**:
   ```bash
   python app.py
   ```

## Configuration

### EVE Logs Path

**Windows**: `%USERPROFILE%\Documents\EVE\logs\Chatlogs`  
**macOS**: `~/Documents/EVE/logs/Gamelogs`

### TTS Configuration

Edit `config/app.yml` to customize your TTS experience:

```yaml
speech:
  enabled: true
  
  # Choose your preferred TTS engine
  tts_engine: "edge-tts"  # Options: edge-tts, gtts, pyttsx3
  
  # Edge TTS settings (highest quality)
  edge_voice: "en-US-AriaNeural"  # Neural voice
  edge_rate: "+0%"                 # Speed: -50% to +50%
  edge_volume: "+0%"               # Volume: -50% to +50%
  
  # Google TTS settings
  gtts_language: "en"              # Language code
  gtts_slow: false                 # Slower speech for clarity
  
  # pyttsx3 settings (fallback)
  voice: "Samantha"                # System voice name
  voice_rate: 150                  # Words per minute
  voice_volume: 0.8                # Volume level
```

### Combat Logging Requirement

**Low health alerts (shield, capacitor) require combat logging to be enabled in EVE Online:**

1. In EVE Online, go to **Settings** → **General**
2. Look for **"Combat Log"** or **"Save combat log to file"**
3. **Enable** this option
4. Set the log file path to a directory EVE Copilot can monitor

Without combat logging enabled, EVE only generates chat logs, not combat events.

## Event Types

The system detects various EVE events:

- **Combat**: Incoming/outgoing damage, drone hits
- **E-war**: Warp scramble, web, energy neutralization
- **Equipment**: Module activation, reload requirements
- **Status**: Shield levels, capacitor levels (requires combat logging)

## Voice Prompts

- **Damage Alerts**: "Damage spike", "Pulse shield booster"
- **E-war Alerts**: "You are scrambled", "You are webbed"
- **Equipment**: "Reload now", "Module active"
- **Status**: "Shield low", "Capacitor low"

## TTS Troubleshooting

### Edge TTS Issues
- **No voices available**: Run `python tts_test.py voices` to see available voices
- **Audio not playing**: Ensure pygame is installed: `pip install pygame`

### Google TTS Issues
- **No internet**: Switch to Edge TTS or pyttsx3
- **Audio not playing**: Check pygame installation

### pyttsx3 Issues
- **No voices**: Check system voice settings
- **Poor quality**: This is expected - switch to Edge TTS for better quality

## Development

### Project Structure

```
evetalk/
├── config.py      # Configuration management
├── engine.py      # Rules engine
├── events.py      # Event parsing and creation
├── notify.py      # Enhanced TTS system
├── parse.py       # Log file parsing
├── ui.py          # System tray interface
└── watcher.py     # File monitoring
```

### Testing TTS

```bash
# Test individual engines
python tts_test.py

# List Edge TTS voices
python tts_test.py voices

# Run full application tests
python run_tests.py
```

## Requirements

- Python 3.11+
- EVE Online with combat logging enabled
- Audio output capability
- Internet connection (for Google TTS, optional for Edge TTS)
