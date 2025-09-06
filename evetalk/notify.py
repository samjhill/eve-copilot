"""
Speech notification system for EVE Copilot - Enhanced TTS with multiple engines.

This module provides text-to-speech functionality with support for multiple
TTS engines (Google TTS, Edge TTS, pyttsx3) and includes a speech queue
system for managing voice alerts with priority handling.
"""

import queue
import threading
import time
import tempfile
from typing import Optional, Dict, Any, List
import logging
import asyncio
from pathlib import Path
from abc import ABC, abstractmethod

# Try to import various TTS engines
try:
    import pyttsx3
    PYTTSX3_AVAILABLE = True
except ImportError:
    PYTTSX3_AVAILABLE = False
    logging.warning("pyttsx3 not available")

try:
    from gtts import gTTS
    GTTS_AVAILABLE = True
except ImportError:
    GTTS_AVAILABLE = False
    logging.warning("gTTS not available")

try:
    import edge_tts
    EDGE_TTS_AVAILABLE = True
except ImportError:
    EDGE_TTS_AVAILABLE = False
    logging.warning("edge-tts not available")

try:
    import pygame
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False
    logging.warning("pygame not available")

from .events import GameEvent

logger = logging.getLogger(__name__)


class TTSEngineError(Exception):
    """TTS engine related errors."""
    pass


class TTSEngine(ABC):
    """Base class for TTS engines."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize TTS engine with configuration.
        
        Args:
            config: TTS configuration dictionary
        """
        self.config = config
        self.name = "base"
        self._initialized = False
        self._init_engine()
    
    @abstractmethod
    def _init_engine(self) -> None:
        """Initialize the TTS engine. Must be implemented by subclasses."""
        pass
    
    @abstractmethod
    def speak(self, text: str) -> bool:
        """Speak the given text. Returns True if successful.
        
        Args:
            text: Text to speak
            
        Returns:
            True if speech was successful
        """
        pass
    
    def get_available_voices(self) -> List[str]:
        """Get list of available voice names.
        
        Returns:
            List of available voice names
        """
        return []
    
    def set_voice(self, voice_name: str) -> bool:
        """Set the voice to use. Returns True if successful.
        
        Args:
            voice_name: Name of voice to use
            
        Returns:
            True if voice was set successfully
        """
        return False
    
    def is_available(self) -> bool:
        """Check if this TTS engine is available.
        
        Returns:
            True if engine is available and initialized
        """
        return self._initialized
    
    def _play_audio_file(self, audio_file: Path) -> bool:
        """Play audio file using pygame. Common functionality for file-based TTS.
        
        Args:
            audio_file: Path to audio file to play
            
        Returns:
            True if playback was successful
        """
        if not PYGAME_AVAILABLE:
            logger.error("pygame not available for audio playback")
            return False
        
        try:
            pygame.mixer.music.load(str(audio_file))
            pygame.mixer.music.play()
            
            # Wait for playback to complete
            while pygame.mixer.music.get_busy():
                pygame.time.wait(100)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to play audio file: {e}")
            return False


class Pyttsx3Engine(TTSEngine):
    """pyttsx3 TTS engine (offline, basic quality)."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.name = "pyttsx3"
    
    def _init_engine(self) -> None:
        """Initialize the pyttsx3 engine."""
        if not PYTTSX3_AVAILABLE:
            logger.warning("pyttsx3 not available")
            return
        
        try:
            self.engine = pyttsx3.init()
            
            # Configure settings
            rate = self.config.get('voice_rate', 150)
            volume = self.config.get('voice_volume', 0.8)
            
            self.engine.setProperty('rate', rate)
            self.engine.setProperty('volume', volume)
            
            # Set voice
            self._set_best_voice()
            
            self._initialized = True
            logger.info("Pyttsx3 engine initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize pyttsx3: {e}")
            self.engine = None
    
    def _set_best_voice(self) -> None:
        """Set the best available voice."""
        if not self.engine:
            return
        
        try:
            voices = self.engine.getProperty('voices')
            if not voices:
                return
            
            configured_voice = self.config.get('voice', 'Samantha')
            selected_voice = None
            
            # Try configured voice first
            for voice in voices:
                if voice.name == configured_voice:
                    selected_voice = voice
                    break
            
            # Fallback to preferred voice
            if not selected_voice:
                for voice in voices:
                    if 'female' in voice.name.lower() or 'zira' in voice.name.lower():
                        selected_voice = voice
                        break
            
            # Final fallback
            if not selected_voice:
                selected_voice = voices[0]
            
            self.engine.setProperty('voice', selected_voice.id)
            logger.info(f"Pyttsx3 voice set to: {selected_voice.name}")
            
        except Exception as e:
            logger.error(f"Failed to set pyttsx3 voice: {e}")
    
    def speak(self, text: str) -> bool:
        """Speak text using pyttsx3."""
        if not self.engine:
            return False
        
        try:
            self.engine.say(text)
            self.engine.runAndWait()
            return True
        except Exception as e:
            logger.error(f"Pyttsx3 speak error: {e}")
            return False
    
    def get_available_voices(self) -> List[str]:
        """Get available pyttsx3 voices."""
        if not self.engine:
            return []
        
        try:
            voices = self.engine.getProperty('voices')
            return [voice.name for voice in voices]
        except Exception:
            return []
    
    def set_voice(self, voice_name: str) -> bool:
        """Set pyttsx3 voice."""
        if not self.engine:
            return False
        
        try:
            voices = self.engine.getProperty('voices')
            for voice in voices:
                if voice.name == voice_name:
                    self.engine.setProperty('voice', voice.id)
                    logger.info(f"Pyttsx3 voice set to: {voice_name}")
                    return True
            
            logger.warning(f"Voice '{voice_name}' not found in pyttsx3")
            return False
        except Exception as e:
            logger.error(f"Failed to set pyttsx3 voice: {e}")
            return False


class GTTSEngine(TTSEngine):
    """Google Text-to-Speech engine (online, high quality)."""
    
    def __init__(self, config: Dict[str, Any]):
        self.temp_dir = Path(tempfile.gettempdir()) / "eve_copilot_tts"
        super().__init__(config)
        self.name = "gtts"
        self.language = self.config.get('gtts_language', 'en')
        self.slow = self.config.get('gtts_slow', False)
    
    def _init_engine(self) -> None:
        """Initialize the GTTS engine."""
        if not GTTS_AVAILABLE:
            logger.warning("gTTS not available")
            return
        
        if not PYGAME_AVAILABLE:
            logger.warning("pygame not available for GTTS audio playback")
            return
        
        try:
            # Create temp directory
            self.temp_dir.mkdir(exist_ok=True)
            
            # Initialize pygame mixer
            pygame.mixer.init()
            
            self._initialized = True
            logger.info("GTTS engine initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize GTTS: {e}")
    
    def speak(self, text: str) -> bool:
        """Speak text using Google TTS."""
        if not self._initialized:
            return False
        
        try:
            # Generate speech file
            tts = gTTS(text=text, lang=self.language, slow=self.slow)
            
            # Create temporary file
            temp_file = self.temp_dir / f"speech_{hash(text)}.mp3"
            tts.save(str(temp_file))
            
            # Play audio
            success = self._play_audio_file(temp_file)
            
            # Clean up
            temp_file.unlink(missing_ok=True)
            
            return success
            
        except Exception as e:
            logger.error(f"GTTS speak error: {e}")
            return False
    
    def get_available_voices(self) -> List[str]:
        """GTTS doesn't have configurable voices, just languages."""
        return [self.language]
    
    def set_voice(self, voice_name: str) -> bool:
        """Set GTTS language (voice_name is treated as language code)."""
        try:
            self.language = voice_name
            logger.info(f"GTTS language set to: {voice_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to set GTTS language: {e}")
            return False


class EdgeTTSEngine(TTSEngine):
    """Microsoft Edge TTS engine (offline, high quality)."""
    
    def __init__(self, config: Dict[str, Any]):
        self.temp_dir = Path(tempfile.gettempdir()) / "eve_copilot_tts"
        super().__init__(config)
        self.name = "edge-tts"
        self.voice = self.config.get('edge_voice', 'en-US-AriaNeural')
        self.rate = self.config.get('edge_rate', '+0%')
        self.volume = self.config.get('edge_volume', '+0%')
    
    def _init_engine(self) -> None:
        """Initialize the Edge TTS engine."""
        if not EDGE_TTS_AVAILABLE:
            logger.warning("edge-tts not available")
            return
        
        if not PYGAME_AVAILABLE:
            logger.warning("pygame not available for Edge TTS audio playback")
            return
        
        try:
            # Create temp directory
            self.temp_dir.mkdir(exist_ok=True)
            
            # Initialize pygame mixer
            pygame.mixer.init()
            
            self._initialized = True
            logger.info("Edge TTS engine initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Edge TTS: {e}")
    
    async def _generate_speech(self, text: str) -> Optional[Path]:
        """Generate speech file asynchronously."""
        if not self._initialized:
            return None
        
        try:
            # Create temporary file
            temp_file = self.temp_dir / f"speech_{hash(text)}.mp3"
            
            # Generate speech
            communicate = edge_tts.Communicate(
                text, 
                self.voice,
                rate=self.rate,
                volume=self.volume
            )
            
            await communicate.save(str(temp_file))
            return temp_file
            
        except Exception as e:
            logger.error(f"Edge TTS generation error: {e}")
            return None
    
    def speak(self, text: str) -> bool:
        """Speak text using Edge TTS."""
        if not self._initialized:
            return False
        
        try:
            # Run async function in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            temp_file = loop.run_until_complete(self._generate_speech(text))
            loop.close()
            
            if not temp_file or not temp_file.exists():
                return False
            
            # Play audio
            success = self._play_audio_file(temp_file)
            
            # Clean up
            temp_file.unlink(missing_ok=True)
            
            return success
            
        except Exception as e:
            logger.error(f"Edge TTS speak error: {e}")
            return False
    
    async def _get_voices(self) -> List[str]:
        """Get available Edge TTS voices asynchronously."""
        if not self._initialized:
            return []
        
        try:
            voices = await edge_tts.list_voices()
            return [voice["ShortName"] for voice in voices]
        except Exception as e:
            logger.error(f"Failed to get Edge TTS voices: {e}")
            return []
    
    def get_available_voices(self) -> List[str]:
        """Get available Edge TTS voices."""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            voices = loop.run_until_complete(self._get_voices())
            loop.close()
            return voices
        except Exception as e:
            logger.error(f"Failed to get Edge TTS voices: {e}")
            return []
    
    def set_voice(self, voice_name: str) -> bool:
        """Set Edge TTS voice."""
        try:
            self.voice = voice_name
            logger.info(f"Edge TTS voice set to: {voice_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to set Edge TTS voice: {e}")
            return False


class SpeechQueue:
    """Priority queue for speech notifications."""
    
    def __init__(self):
        """Initialize speech queue."""
        self.queue = queue.PriorityQueue()
        self.processing = False
        self.worker_thread = None
        self.stop_event = threading.Event()
        
    def start(self):
        """Start the speech queue worker thread."""
        if self.processing:
            return
        
        self.processing = True
        self.stop_event.clear()
        self.worker_thread = threading.Thread(target=self._worker, daemon=True)
        self.worker_thread.start()
        logger.info("Speech queue worker started")
    
    def stop(self):
        """Stop the speech queue worker thread."""
        if not self.processing:
            return
        
        self.processing = False
        self.stop_event.set()
        
        if self.worker_thread:
            self.worker_thread.join(timeout=2)
        
        logger.info("Speech queue worker stopped")
    
    def add_speech(self, text: str, priority: int = 1, event: GameEvent = None):
        """Add a speech request to the queue.
        
        Args:
            text: Text to speak
            priority: Priority level (0=highest, 2=lowest)
            event: Associated game event
        """
        # Priority 0 = highest (safety alerts), Priority 2 = lowest (info)
        # Use negative priority so lower numbers come first
        item = (-priority, time.time(), text, event)
        self.queue.put(item)
        logger.debug(f"Added speech to queue: '{text}' (priority: {priority})")
    
    def _worker(self):
        """Worker thread that processes speech queue."""
        while self.processing and not self.stop_event.is_set():
            try:
                # Get next speech item with timeout
                item = self.queue.get(timeout=0.1)
                priority, timestamp, text, event = item
                
                # Process the speech item
                self._process_speech(text, event)
                
                # Mark task as done
                self.queue.task_done()
                
            except queue.Empty:
                continue
            except Exception as e:
                logger.error(f"Error in speech worker: {e}")
    
    def _process_speech(self, text: str, event: GameEvent):
        """Process a single speech item."""
        # This will be overridden by the SpeechNotifier
        pass


class SpeechNotifier:
    """Enhanced speech notification system with multiple TTS engines."""
    
    def __init__(self, config):
        """Initialize speech notifier.
        
        Args:
            config: Application configuration object
        """
        self.config = config
        self.speech_config = config.get_speech_config()
        self.enabled = self.speech_config.get('enabled', True)
        
        # Initialize TTS engines
        self.tts_engines = []
        self.active_engine = None
        self._init_tts_engines()
        
        # Speech queue
        self.speech_queue = SpeechQueue()
        self.speech_queue._process_speech = self._speak_text
        
        # Deduplication
        self.last_spoken = {}  # text -> timestamp
        self.dedup_window = 2.0  # seconds
        
        # Start speech queue
        if self.enabled:
            self.speech_queue.start()
    
    def is_enabled(self) -> bool:
        """Check if speech is enabled.
        
        Returns:
            True if speech is enabled and TTS engines are available
        """
        result = self.enabled and self.active_engine is not None
        logger.info(f"Speech enabled check: enabled={self.enabled}, active_engine={self.active_engine is not None}, result={result}")
        return result
    
    def _init_tts_engines(self):
        """Initialize available TTS engines in order of preference."""
        # Try to initialize engines in order of quality
        engines_to_try = [
            (EdgeTTSEngine, "edge-tts"),
            (GTTSEngine, "gtts"),
            (Pyttsx3Engine, "pyttsx3")
        ]
        
        for engine_class, engine_name in engines_to_try:
            try:
                engine = engine_class(self.speech_config)
                if engine.is_available():
                    self.tts_engines.append(engine)
                    logger.info(f"TTS engine '{engine_name}' initialized successfully")
                else:
                    logger.debug(f"TTS engine '{engine_name}' not available")
            except Exception as e:
                logger.warning(f"Failed to initialize TTS engine '{engine_name}': {e}")
        
        # Set active engine
        if self.tts_engines:
            # Try to use configured engine first
            configured_engine = self.speech_config.get('tts_engine', 'edge-tts')
            for engine in self.tts_engines:
                if engine.name == configured_engine:
                    self.active_engine = engine
                    break
            
            # Fallback to first available
            if not self.active_engine:
                self.active_engine = self.tts_engines[0]
            
            logger.info(f"Active TTS engine: {self.active_engine.name}")
        else:
            logger.warning("No TTS engines available, speech disabled")
            self.enabled = False
    
    def speak(self, text: str, priority: int = 1, event: GameEvent = None):
        """Speak text with given priority.
        
        Args:
            text: Text to speak
            priority: Priority level (0=highest, 2=lowest)
            event: Associated game event
        """
        if not self.enabled or not text:
            return
        
        # Check deduplication
        if self._is_duplicate(text):
            logger.debug(f"Skipping duplicate speech: '{text}'")
            return
        
        # Add to speech queue
        self.speech_queue.add_speech(text, priority, event)
    
    def _speak_text(self, text: str, event: GameEvent):
        """Actually speak the text using the active TTS engine."""
        if not self.active_engine:
            logger.warning("No active TTS engine available")
            return
        
        try:
            # Play priority chime if enabled
            if (event and event.priority == 0 and 
                self.speech_config.get('priority_chime', True)):
                self._play_priority_chime()
            
            # Speak the text
            success = self.active_engine.speak(text)
            
            if success:
                # Update deduplication
                self.last_spoken[text] = time.time()
                logger.debug(f"Successfully spoke: '{text}'")
            else:
                logger.warning(f"Failed to speak: '{text}'")
                
        except Exception as e:
            logger.error(f"Error in speech synthesis: {e}")
    
    def _is_duplicate(self, text: str) -> bool:
        """Check if text was recently spoken to avoid spam."""
        if text not in self.last_spoken:
            return False
        
        time_since_last = time.time() - self.last_spoken[text]
        return time_since_last < self.dedup_window
    
    def _play_priority_chime(self):
        """Play priority alert chime."""
        # This could be enhanced with actual chime sounds
        logger.debug("Playing priority chime")
    
    def get_available_engines(self) -> List[str]:
        """Get list of available TTS engine names."""
        return [engine.name for engine in self.tts_engines]
    
    def get_active_engine(self) -> Optional[str]:
        """Get name of currently active TTS engine."""
        return self.active_engine.name if self.active_engine else None
    
    def switch_engine(self, engine_name: str) -> bool:
        """Switch to a different TTS engine.
        
        Args:
            engine_name: Name of engine to switch to
            
        Returns:
            True if switch was successful
        """
        for engine in self.tts_engines:
            if engine.name == engine_name:
                self.active_engine = engine
                logger.info(f"Switched to TTS engine: {engine_name}")
                return True
        
        logger.warning(f"TTS engine '{engine_name}' not available")
        return False
    
    def get_engine_info(self) -> Dict[str, Any]:
        """Get information about all TTS engines."""
        info = {
            'active_engine': self.get_active_engine(),
            'available_engines': self.get_available_engines(),
            'enabled': self.enabled,
            'queue_size': self.speech_queue.queue.qsize() if self.speech_queue else 0
        }
        
        # Add engine-specific info
        for engine in self.tts_engines:
            info[f'{engine.name}_voices'] = engine.get_available_voices()
        
        return info
    
    def shutdown(self):
        """Shutdown the speech notifier."""
        if self.speech_queue:
            self.speech_queue.stop()
        logger.info("Speech notifier shutdown complete")
