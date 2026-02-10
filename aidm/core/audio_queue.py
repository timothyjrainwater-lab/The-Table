"""Audio queue synchronization for voice-first interaction protocol.

This module provides audio queue management to ensure voice output takes priority
over text display. Text is delayed until voice playback completes.

VOICE-FIRST PROTOCOL:
1. Narration generated (LLM produces text)
2. TTS synthesizes audio from narration
3. Audio queued and plays
4. Text revealed ONLY after audio completes
5. User sees text + can replay audio if desired

This ensures audio is primary interaction channel, text is supplementary.
"""

from dataclasses import dataclass
from typing import Optional, Callable, List
from enum import Enum
import threading
import time


class AudioQueueStatus(str, Enum):
    """Status of audio queue items."""
    PENDING = "pending"
    SYNTHESIZING = "synthesizing"
    PLAYING = "playing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class AudioQueueItem:
    """Single audio queue item (narration + audio).

    Attributes:
        item_id: Unique identifier for queue item
        narration_text: Original narration text
        audio_bytes: Synthesized audio (None if not yet synthesized)
        status: Current status of queue item
        synthesis_start_time: When TTS synthesis began (None if not started)
        playback_start_time: When audio playback began (None if not started)
        completion_time: When audio playback completed (None if not completed)
        on_complete_callback: Called when audio playback finishes
    """
    item_id: str
    narration_text: str
    audio_bytes: Optional[bytes] = None
    status: AudioQueueStatus = AudioQueueStatus.PENDING
    synthesis_start_time: Optional[float] = None
    playback_start_time: Optional[float] = None
    completion_time: Optional[float] = None
    on_complete_callback: Optional[Callable[[], None]] = None

    def mark_synthesizing(self):
        """Mark item as currently synthesizing audio."""
        self.status = AudioQueueStatus.SYNTHESIZING
        self.synthesis_start_time = time.time()

    def mark_playing(self, audio_bytes: bytes):
        """Mark item as currently playing audio."""
        self.audio_bytes = audio_bytes
        self.status = AudioQueueStatus.PLAYING
        self.playback_start_time = time.time()

    def mark_completed(self):
        """Mark item as completed playback."""
        self.status = AudioQueueStatus.COMPLETED
        self.completion_time = time.time()
        if self.on_complete_callback:
            self.on_complete_callback()

    def mark_failed(self):
        """Mark item as failed (synthesis or playback error)."""
        self.status = AudioQueueStatus.FAILED
        self.completion_time = time.time()
        # Still trigger callback to unblock UI (fallback to text-only)
        if self.on_complete_callback:
            self.on_complete_callback()


class AudioQueue:
    """Audio queue manager for voice-first interaction protocol.

    Manages queue of narration items waiting for TTS synthesis and playback.
    Ensures text is only revealed after audio completes (voice-first UX).

    Thread-safe for concurrent synthesis and playback.
    """

    def __init__(self):
        """Initialize empty audio queue."""
        self._queue: List[AudioQueueItem] = []
        self._lock = threading.RLock()
        self._current_item: Optional[AudioQueueItem] = None

    def enqueue(
        self,
        item_id: str,
        narration_text: str,
        on_complete: Optional[Callable[[], None]] = None
    ) -> AudioQueueItem:
        """Add narration to audio queue.

        Args:
            item_id: Unique identifier for this narration
            narration_text: Text to synthesize to audio
            on_complete: Callback to trigger when audio playback finishes

        Returns:
            AudioQueueItem added to queue
        """
        item = AudioQueueItem(
            item_id=item_id,
            narration_text=narration_text,
            on_complete_callback=on_complete
        )

        with self._lock:
            self._queue.append(item)

        return item

    def get_next_pending(self) -> Optional[AudioQueueItem]:
        """Get next pending item from queue (FIFO).

        Returns:
            Next pending item, or None if queue empty
        """
        with self._lock:
            for item in self._queue:
                if item.status == AudioQueueStatus.PENDING:
                    return item
        return None

    def get_item(self, item_id: str) -> Optional[AudioQueueItem]:
        """Get queue item by ID.

        Args:
            item_id: Item identifier

        Returns:
            AudioQueueItem if found, else None
        """
        with self._lock:
            for item in self._queue:
                if item.item_id == item_id:
                    return item
        return None

    def set_current(self, item_id: str):
        """Set current item being processed.

        Args:
            item_id: Item identifier
        """
        with self._lock:
            self._current_item = self.get_item(item_id)

    def get_current(self) -> Optional[AudioQueueItem]:
        """Get currently processing item.

        Returns:
            Current item, or None if no item processing
        """
        with self._lock:
            return self._current_item

    def clear_completed(self):
        """Remove completed items from queue (cleanup)."""
        with self._lock:
            self._queue = [
                item for item in self._queue
                if item.status not in (AudioQueueStatus.COMPLETED, AudioQueueStatus.FAILED)
            ]

    def get_queue_depth(self) -> int:
        """Get number of pending/processing items.

        Returns:
            Number of items not yet completed
        """
        with self._lock:
            return len([
                item for item in self._queue
                if item.status not in (AudioQueueStatus.COMPLETED, AudioQueueStatus.FAILED)
            ])


class VoiceSyncManager:
    """Voice synchronization manager for voice-first UX.

    Coordinates TTS synthesis, audio playback, and text reveal timing.
    Ensures text only appears AFTER voice playback completes.

    Usage:
        manager = VoiceSyncManager(tts_adapter, audio_player)
        manager.queue_narration("narration_1", "Your sword strikes true!")
        # Audio plays, then text is revealed via callback
    """

    def __init__(self, tts_adapter, audio_player):
        """Initialize voice sync manager.

        Args:
            tts_adapter: TTS adapter (synthesize text -> audio)
            audio_player: Audio player (play audio bytes)
        """
        self.tts = tts_adapter
        self.audio_player = audio_player
        self.queue = AudioQueue()
        self._threads: List[threading.Thread] = []
        self._threads_lock = threading.Lock()

    def queue_narration(
        self,
        item_id: str,
        narration_text: str,
        on_voice_complete: Optional[Callable[[], None]] = None
    ):
        """Queue narration for voice-first playback.

        Steps:
        1. Add to queue
        2. Synthesize audio (TTS)
        3. Play audio
        4. Trigger callback (reveals text)

        Args:
            item_id: Unique narration ID
            narration_text: Text to speak
            on_voice_complete: Callback when audio finishes (reveals text in UI)
        """
        # Enqueue item
        item = self.queue.enqueue(item_id, narration_text, on_complete=on_voice_complete)

        # Start synthesis + playback in background thread
        t = threading.Thread(
            target=self._process_queue_item,
            args=(item,),
            daemon=True
        )
        with self._threads_lock:
            self._threads.append(t)
        t.start()

    def _process_queue_item(self, item: AudioQueueItem):
        """Process single queue item (synthesis + playback).

        Args:
            item: Queue item to process
        """
        try:
            # Mark as synthesizing
            item.mark_synthesizing()
            self.queue.set_current(item.item_id)

            # Synthesize audio
            audio_bytes = self.tts.synthesize(item.narration_text)

            # Mark as playing
            item.mark_playing(audio_bytes)

            # Play audio (blocking until complete)
            self.audio_player.play(audio_bytes)

            # Mark as completed (triggers on_complete callback)
            item.mark_completed()

        except Exception as e:
            # Synthesis or playback failed
            print(f"Voice sync error for {item.item_id}: {e}")
            item.mark_failed()

        finally:
            # Clear current item
            if self.queue.get_current() == item:
                self.queue.set_current(None)

    def wait_for_item(self, item_id: str, timeout: float = 10.0) -> bool:
        """Wait for queue item to complete (blocking).

        Args:
            item_id: Item to wait for
            timeout: Max wait time (seconds)

        Returns:
            True if completed, False if timeout
        """
        start = time.time()
        while time.time() - start < timeout:
            item = self.queue.get_item(item_id)
            if item and item.status in (AudioQueueStatus.COMPLETED, AudioQueueStatus.FAILED):
                return True
            time.sleep(0.1)
        return False

    def get_status(self, item_id: str) -> Optional[AudioQueueStatus]:
        """Get status of queue item.

        Args:
            item_id: Item identifier

        Returns:
            AudioQueueStatus if found, else None
        """
        item = self.queue.get_item(item_id)
        return item.status if item else None

    def shutdown(self, timeout: float = 5.0):
        """Join all spawned threads so the process can exit cleanly.

        Args:
            timeout: Max seconds to wait per thread
        """
        with self._threads_lock:
            threads = list(self._threads)
        for t in threads:
            t.join(timeout=timeout)
        with self._threads_lock:
            self._threads = [t for t in self._threads if t.is_alive()]


# ============================================================================
# Voice-First UI Integration Helpers
# ============================================================================

class TextRevealController:
    """Controller for revealing text after voice playback.

    Typical usage in UI:
        controller = TextRevealController()
        controller.queue_narration_with_delayed_text(
            narration_id="turn_5_attack",
            narration_text="Your blade strikes true!",
            on_text_reveal=lambda text: ui.show_text(text)
        )
    """

    def __init__(self, voice_sync_manager: VoiceSyncManager):
        """Initialize text reveal controller.

        Args:
            voice_sync_manager: Voice sync manager to use
        """
        self.voice_sync = voice_sync_manager
        self._hidden_text = {}  # item_id -> text

    def queue_narration_with_delayed_text(
        self,
        narration_id: str,
        narration_text: str,
        on_text_reveal: Callable[[str], None]
    ):
        """Queue narration with text reveal after voice completes.

        Text is hidden until voice playback finishes.

        Args:
            narration_id: Unique ID for narration
            narration_text: Text to speak + reveal
            on_text_reveal: Called with text when voice completes
        """
        # Store text as hidden
        self._hidden_text[narration_id] = narration_text

        # Define callback to reveal text after voice
        def reveal_callback():
            text = self._hidden_text.get(narration_id, "")
            on_text_reveal(text)
            # Cleanup
            if narration_id in self._hidden_text:
                del self._hidden_text[narration_id]

        # Queue narration with reveal callback
        self.voice_sync.queue_narration(
            item_id=narration_id,
            narration_text=narration_text,
            on_voice_complete=reveal_callback
        )


# ============================================================================
# Status Callback Protocol
# ============================================================================

@dataclass
class VoicePlaybackStatus:
    """Status update for voice playback progress.

    Used to notify UI of current voice playback state.
    """
    item_id: str
    status: AudioQueueStatus
    narration_text: str
    synthesis_latency_ms: Optional[float] = None  # Time to synthesize audio
    playback_duration_ms: Optional[float] = None  # Duration of audio playback

    @staticmethod
    def from_queue_item(item: AudioQueueItem) -> 'VoicePlaybackStatus':
        """Create status from queue item.

        Args:
            item: Queue item

        Returns:
            VoicePlaybackStatus
        """
        synthesis_latency = None
        if item.synthesis_start_time and item.playback_start_time:
            synthesis_latency = (item.playback_start_time - item.synthesis_start_time) * 1000

        playback_duration = None
        if item.playback_start_time and item.completion_time:
            playback_duration = (item.completion_time - item.playback_start_time) * 1000

        return VoicePlaybackStatus(
            item_id=item.item_id,
            status=item.status,
            narration_text=item.narration_text,
            synthesis_latency_ms=synthesis_latency,
            playback_duration_ms=playback_duration
        )


class VoiceStatusNotifier:
    """Notifier for voice playback status updates.

    Allows UI to subscribe to voice playback events:
    - Synthesis started
    - Playback started
    - Playback completed

    Usage:
        notifier = VoiceStatusNotifier()
        notifier.subscribe(lambda status: print(f"Voice status: {status.status}"))
        # Status updates trigger subscriber callbacks
    """

    def __init__(self):
        """Initialize voice status notifier."""
        self._subscribers: List[Callable[[VoicePlaybackStatus], None]] = []

    def subscribe(self, callback: Callable[[VoicePlaybackStatus], None]):
        """Subscribe to voice status updates.

        Args:
            callback: Called with VoicePlaybackStatus on each update
        """
        self._subscribers.append(callback)

    def notify(self, status: VoicePlaybackStatus):
        """Notify all subscribers of status update.

        Args:
            status: Current voice playback status
        """
        for callback in self._subscribers:
            callback(status)
