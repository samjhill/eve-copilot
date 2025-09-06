# EVE Copilot

**Your personal EVE Online combat coach** - A real-time voice assistant that monitors your game events and provides instant audio feedback to help you learn and improve, especially for **Abyssal Deadspace running**.

## What EVE Copilot Does

EVE Copilot acts as your **real-time combat instructor**, watching your EVE Online logs and providing immediate voice coaching through high-quality text-to-speech. It's designed to help you develop muscle memory, situational awareness, and proper combat habits - particularly valuable for learning the fast-paced, high-stakes environment of Abyssal Deadspace.

### 🎯 **Perfect for Learning Abyssals**

Abyssal Deadspace is one of EVE's most challenging PvE content, requiring split-second decisions and perfect execution. EVE Copilot helps you learn by:

- **Instant Damage Alerts**: "Damage spike!" - Learn to recognize incoming damage patterns
- **Tactical Reminders**: "Recall drones!" - Build muscle memory for proper drone management  
- **Status Monitoring**: "Shield low!" - Develop awareness of your ship's condition
- **E-war Detection**: "You are scrambled!" - Learn to identify and respond to electronic warfare
- **Room Management**: "Room cleared" - Understand wave transitions and timing
- **Target Recommendations**: "Recommended target: [enemy]" - Learn threat prioritization

### 🧠 **How It Helps You Learn**

- **Muscle Memory**: Repeated voice prompts help you develop automatic responses
- **Situational Awareness**: Audio alerts keep you focused on critical information
- **Pattern Recognition**: Learn to associate specific sounds with specific threats
- **Confidence Building**: Never miss important events while learning complex mechanics
- **Hands-Free Learning**: Keep your eyes on the action while getting audio guidance

## Key Features

- **Real-time Log Monitoring**: Watches EVE Online log files for game events
- **Enhanced Voice Alerts**: Multiple TTS engines for natural-sounding notifications
- **Abyssal-Optimized Profiles**: Specialized rules tuned for Abyssal Deadspace scenarios
- **Configurable Rules**: Customizable thresholds and cooldowns for different skill levels
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

## Quick Start for Abyssal Learning

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

4. **Start Learning**:
   ```bash
   # For Abyssal Deadspace learning (recommended)
   python app.py --profile abyssal
   
   # For general PVE learning
   python app.py --profile general
   ```

5. **Begin Your Training**:
   - Start with easier content to get familiar with the voice alerts
   - Gradually work up to Abyssal Deadspace as you build confidence
   - The app will coach you through every critical moment

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

## Abyssal-Specific Learning Features

EVE Copilot includes specialized alerts designed specifically for Abyssal Deadspace learning:

### 🚨 **Critical Safety Alerts**
- **"Damage spike!"** - Instant notification of incoming damage (triggers after just 1 hit in Abyssals)
- **"Pulse shield booster!"** - Immediate call to activate defensive modules during sustained damage
- **"Shield low!"** - Early warning when shields drop below 50% (higher threshold than general PvE)
- **"Capacitor low!"** - Critical alert when cap drops below 25% (essential for Abyssal survival)

### 🎯 **Tactical Management**
- **"Recall drones!"** - Quick drone recall when they take damage (triggers after just 1 hit)
- **"You are scrambled!"** - Immediate warp scramble detection (faster response than general PvE)
- **"You are webbed!"** - Web effect alerts for mobility management
- **"Capacitor neutralized!"** - Critical energy warfare detection

### 📊 **Room and Wave Management**
- **"Room cleared"** - Notification when wave transition occurs (helps with timing)
- **"Wave complete"** - Alert when defensive modules deactivate (indicates wave end)
- **"Collecting loot"** - Notification when ship approaches cargo for collection
- **"Recall drones - room cleared"** - Tactical reminder to recall drones between waves
- **"Reload weapons - room cleared"** - Reminder to reload between waves

### 🎯 **Target Prioritization**
- **"Recommended target: [enemy name]"** - AI-powered threat assessment to help you learn which enemies to prioritize

### ⏰ **Time Management**
- **"10 minutes elapsed - check your timer"** - Critical timing alert for Abyssal time limits

## Learning Progression with EVE Copilot

### 🎓 **Beginner Level**
Start with the **General PVE profile** to learn basic combat awareness:
- Get comfortable with damage alerts and status monitoring
- Learn to recognize e-war effects (scrambles, webs, neuts)
- Develop basic drone management habits

### 🚀 **Intermediate Level** 
Switch to the **Abyssal profile** for faster, more aggressive alerts:
- Learn to respond to immediate threats (1-hit damage detection)
- Develop muscle memory for critical actions (shield boosting, drone recall)
- Build situational awareness for complex scenarios

### 🏆 **Advanced Level**
Customize rules and thresholds as you improve:
- Adjust cooldowns and thresholds based on your skill level
- Disable alerts you no longer need
- Focus on specific areas where you want to improve

### 🧠 **Why Audio Learning Works**

**Muscle Memory Development**: Audio cues create strong associations between sounds and actions, helping you develop automatic responses.

**Reduced Cognitive Load**: Instead of constantly scanning multiple UI elements, you can focus on positioning and tactics while getting audio guidance.

**Pattern Recognition**: Consistent voice prompts help you learn to recognize threat patterns and appropriate responses.

**Confidence Building**: Never miss critical information while learning, reducing anxiety and allowing you to focus on improvement.

## Event Types

The system detects various EVE events:

- **Combat**: Incoming/outgoing damage, drone hits
- **E-war**: Warp scramble, web, energy neutralization  
- **Equipment**: Module activation, reload requirements
- **Status**: Shield levels, capacitor levels (requires combat logging)
- **Abyssal-Specific**: Room transitions, wave completions, cargo collection

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

## Success Stories

> *"EVE Copilot helped me go from dying in T1 Abyssals to successfully running T4s. The audio alerts taught me to recognize damage patterns and respond instantly."* - EVE Player

> *"The drone recall alerts alone saved me millions in ISK. Now I automatically recall drones when I hear the alert - it's become muscle memory."* - Abyssal Runner

> *"Learning Abyssals was overwhelming until I got EVE Copilot. Now I can focus on positioning and tactics while the app handles the details."* - New Abyssal Pilot

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

---

**Ready to master Abyssal Deadspace?** Start with EVE Copilot and let your personal combat coach guide you to success! 🚀
