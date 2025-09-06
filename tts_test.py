#!/usr/bin/env python3
"""
TTS Engine Test Script for EVE Copilot
Test and configure different text-to-speech engines
"""

import sys
import os
import asyncio
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from evetalk.config import Config
from evetalk.notify import SpeechNotifier, EdgeTTSEngine, GTTSEngine, Pyttsx3Engine


def test_tts_engines():
    """Test all available TTS engines."""
    print("=" * 60)
    print("EVE Copilot TTS Engine Test")
    print("=" * 60)
    
    # Load configuration
    try:
        config = Config("config/app.yml")
        speech_config = config.get_speech_config()
        print(f"Configuration loaded from config/app.yml")
    except Exception as e:
        print(f"Failed to load config: {e}")
        print("Using default configuration")
        speech_config = {
            'enabled': True,
            'tts_engine': 'edge-tts',
            'voice': 'Samantha',
            'voice_rate': 150,
            'voice_volume': 0.8,
            'edge_voice': 'en-US-AriaNeural',
            'edge_rate': '+0%',
            'edge_volume': '+0%',
            'gtts_language': 'en',
            'gtts_slow': False
        }
    
    print(f"\nSpeech Configuration:")
    for key, value in speech_config.items():
        print(f"  {key}: {value}")
    
    # Test individual engines
    print("\n" + "=" * 60)
    print("Testing Individual TTS Engines")
    print("=" * 60)
    
    # Test Edge TTS
    print("\n1. Testing Edge TTS Engine...")
    edge_engine = EdgeTTSEngine(speech_config)
    if edge_engine.is_available():
        print("  ✓ Edge TTS is available")
        print(f"  Available voices: {len(edge_engine.get_available_voices())}")
        if edge_engine.get_available_voices():
            print(f"  Sample voices: {', '.join(edge_engine.get_available_voices()[:3])}")
        
        # Test speech
        test_text = "Edge TTS test successful. This engine provides high quality neural voices."
        print(f"  Testing speech: '{test_text}'")
        if edge_engine.speak(test_text):
            print("  ✓ Edge TTS speech test passed")
        else:
            print("  ✗ Edge TTS speech test failed")
    else:
        print("  ✗ Edge TTS is not available")
    
    # Test Google TTS
    print("\n2. Testing Google TTS Engine...")
    gtts_engine = GTTSEngine(speech_config)
    if gtts_engine.is_available():
        print("  ✓ Google TTS is available")
        print(f"  Language: {gtts_engine.language}")
        
        # Test speech
        test_text = "Google TTS test successful. This engine provides high quality online voices."
        print(f"  Testing speech: '{test_text}'")
        if gtts_engine.speak(test_text):
            print("  ✓ Google TTS speech test passed")
        else:
            print("  ✗ Google TTS speech test failed")
    else:
        print("  ✗ Google TTS is not available")
    
    # Test pyttsx3
    print("\n3. Testing pyttsx3 Engine...")
    pyttsx3_engine = Pyttsx3Engine(speech_config)
    if pyttsx3_engine.is_available():
        print("  ✓ pyttsx3 is available")
        voices = pyttsx3_engine.get_available_voices()
        print(f"  Available voices: {len(voices)}")
        if voices:
            print(f"  Sample voices: {', '.join(voices[:3])}")
        
        # Test speech
        test_text = "Pyttsx3 test successful. This is the fallback offline engine."
        print(f"  Testing speech: '{test_text}'")
        if pyttsx3_engine.speak(test_text):
            print("  ✓ pyttsx3 speech test passed")
        else:
            print("  ✗ pyttsx3 speech test failed")
    else:
        print("  ✗ pyttsx3 is not available")
    
    # Test integrated speech notifier
    print("\n" + "=" * 60)
    print("Testing Integrated Speech Notifier")
    print("=" * 60)
    
    try:
        speech_notifier = SpeechNotifier(config)
        print(f"✓ Speech notifier initialized successfully")
        print(f"  Active engine: {speech_notifier.get_active_engine()}")
        print(f"  Available engines: {', '.join(speech_notifier.get_available_engines())}")
        
        # Test integrated speech
        test_text = "Integrated speech test successful. EVE Copilot is ready for action."
        print(f"\nTesting integrated speech: '{test_text}'")
        speech_notifier.speak(test_text, priority=2)
        
        # Wait a moment for speech to complete
        import time
        time.sleep(3)
        
        print("  ✓ Integrated speech test completed")
        
        # Cleanup
        speech_notifier.shutdown()
        
    except Exception as e:
        print(f"✗ Failed to test integrated speech notifier: {e}")
    
    print("\n" + "=" * 60)
    print("TTS Engine Test Complete")
    print("=" * 60)
    
    print("\nRecommendations:")
    print("1. Edge TTS: Best quality, works offline, recommended for most users")
    print("2. Google TTS: High quality, requires internet, good alternative")
    print("3. pyttsx3: Basic quality, works offline, fallback option")
    
    print("\nTo change TTS engines, edit config/app.yml and set 'tts_engine'")
    print("Available options: edge-tts, gtts, pyttsx3")


def list_edge_voices():
    """List all available Edge TTS voices."""
    print("=" * 60)
    print("Available Edge TTS Voices")
    print("=" * 60)
    
    try:
        import edge_tts
        
        async def get_voices():
            voices = await edge_tts.list_voices()
            return voices
        
        # Run async function
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        voices = loop.run_until_complete(get_voices())
        loop.close()
        
        # Group voices by language
        voices_by_lang = {}
        for voice in voices:
            lang = voice.get("Locale", "Unknown")
            if lang not in voices_by_lang:
                voices_by_lang[lang] = []
            voices_by_lang[lang].append(voice["ShortName"])
        
        # Display voices
        for lang in sorted(voices_by_lang.keys()):
            print(f"\n{lang}:")
            voices_list = voices_by_lang[lang]
            for i, voice in enumerate(voices_list):
                if i % 3 == 0:
                    print("  ", end="")
                print(f"{voice:<20}", end="")
                if i % 3 == 2 or i == len(voices_list) - 1:
                    print()
        
        print(f"\nTotal voices: {len(voices)}")
        print("\nTo use a specific voice, set 'edge_voice' in config/app.yml")
        print("Example: edge_voice: 'en-US-AriaNeural'")
        
    except ImportError:
        print("edge-tts not available. Install with: pip install edge-tts")
    except Exception as e:
        print(f"Error listing voices: {e}")


def main():
    """Main function."""
    if len(sys.argv) > 1 and sys.argv[1] == "voices":
        list_edge_voices()
    else:
        test_tts_engines()


if __name__ == "__main__":
    main()
