"""Unit tests for audio queue synchronization and voice-first protocol.

Tests verify:
- Audio queue FIFO ordering
- Voice-first protocol (text delayed until audio completes)
- Thread-safe queue operations
- Status callback notifications
- Graceful failure handling (TTS unavailable, synthesis errors)
"""

import pytest
import time
import threading
from unittest.mock import Mock, MagicMock
from typing import List

from aidm.core.audio_queue import (
    AudioQueue,
    AudioQueueItem,
    AudioQueueStatus,
    VoiceSyncManager,
    TextRevealController,
    VoicePlaybackStatus,
    VoiceStatusNotifier,
)


# ============================================================================
# AudioQueue Tests
# ============================================================================

class TestAudioQueue:
    """Test audio queue basic operations."""

    def test_enqueue_creates_pending_item(self):
        """Enqueuing creates item with PENDING status."""
        queue = AudioQueue()
        item = queue.enqueue("item_1", "Test narration")

        assert item.item_id == "item_1"
        assert item.narration_text == "Test narration"
        assert item.status == AudioQueueStatus.PENDING
        assert item.audio_bytes is None

    def test_get_next_pending_returns_fifo(self):
        """get_next_pending returns items in FIFO order."""
        queue = AudioQueue()
        item1 = queue.enqueue("item_1", "First")
        item2 = queue.enqueue("item_2", "Second")
        item3 = queue.enqueue("item_3", "Third")

        next_item = queue.get_next_pending()
        assert next_item.item_id == "item_1"

    def test_get_next_pending_skips_non_pending(self):
        """get_next_pending skips items that are not PENDING."""
        queue = AudioQueue()
        item1 = queue.enqueue("item_1", "First")
        item2 = queue.enqueue("item_2", "Second")

        # Mark first item as playing
        item1.mark_playing(b"audio_data")

        next_item = queue.get_next_pending()
        assert next_item.item_id == "item_2"

    def test_get_next_pending_returns_none_when_empty(self):
        """get_next_pending returns None when queue empty."""
        queue = AudioQueue()
        assert queue.get_next_pending() is None

    def test_get_item_by_id(self):
        """get_item retrieves item by ID."""
        queue = AudioQueue()
        queue.enqueue("item_1", "First")
        queue.enqueue("item_2", "Second")

        item = queue.get_item("item_2")
        assert item.item_id == "item_2"
        assert item.narration_text == "Second"

    def test_get_item_returns_none_for_unknown_id(self):
        """get_item returns None for unknown ID."""
        queue = AudioQueue()
        assert queue.get_item("unknown") is None

    def test_set_and_get_current(self):
        """set_current and get_current manage current item."""
        queue = AudioQueue()
        item = queue.enqueue("item_1", "Test")

        queue.set_current("item_1")
        current = queue.get_current()

        assert current.item_id == "item_1"

    def test_clear_completed_removes_finished_items(self):
        """clear_completed removes COMPLETED and FAILED items."""
        queue = AudioQueue()
        item1 = queue.enqueue("item_1", "First")
        item2 = queue.enqueue("item_2", "Second")
        item3 = queue.enqueue("item_3", "Third")

        item1.mark_completed()
        item2.mark_failed()
        # item3 remains PENDING

        queue.clear_completed()

        assert queue.get_item("item_1") is None
        assert queue.get_item("item_2") is None
        assert queue.get_item("item_3") is not None

    def test_get_queue_depth(self):
        """get_queue_depth counts non-completed items."""
        queue = AudioQueue()
        item1 = queue.enqueue("item_1", "First")
        item2 = queue.enqueue("item_2", "Second")
        item3 = queue.enqueue("item_3", "Third")

        assert queue.get_queue_depth() == 3

        item1.mark_completed()
        assert queue.get_queue_depth() == 2

        item2.mark_failed()
        assert queue.get_queue_depth() == 1


# ============================================================================
# AudioQueueItem Tests
# ============================================================================

class TestAudioQueueItem:
    """Test audio queue item state transitions."""

    def test_mark_synthesizing_sets_status_and_time(self):
        """mark_synthesizing sets status and records start time."""
        item = AudioQueueItem("item_1", "Test narration")

        before = time.time()
        item.mark_synthesizing()
        after = time.time()

        assert item.status == AudioQueueStatus.SYNTHESIZING
        assert item.synthesis_start_time is not None
        assert before <= item.synthesis_start_time <= after

    def test_mark_playing_sets_audio_and_time(self):
        """mark_playing stores audio bytes and records playback start."""
        item = AudioQueueItem("item_1", "Test narration")
        audio_data = b"mock_audio_bytes"

        before = time.time()
        item.mark_playing(audio_data)
        after = time.time()

        assert item.status == AudioQueueStatus.PLAYING
        assert item.audio_bytes == audio_data
        assert item.playback_start_time is not None
        assert before <= item.playback_start_time <= after

    def test_mark_completed_triggers_callback(self):
        """mark_completed triggers on_complete_callback."""
        callback_triggered = []

        def callback():
            callback_triggered.append(True)

        item = AudioQueueItem("item_1", "Test", on_complete_callback=callback)

        before = time.time()
        item.mark_completed()
        after = time.time()

        assert item.status == AudioQueueStatus.COMPLETED
        assert item.completion_time is not None
        assert before <= item.completion_time <= after
        assert len(callback_triggered) == 1

    def test_mark_failed_triggers_callback(self):
        """mark_failed triggers callback (for UI unblock)."""
        callback_triggered = []

        def callback():
            callback_triggered.append(True)

        item = AudioQueueItem("item_1", "Test", on_complete_callback=callback)
        item.mark_failed()

        assert item.status == AudioQueueStatus.FAILED
        assert len(callback_triggered) == 1

    def test_callback_optional(self):
        """Item works without callback (no error)."""
        item = AudioQueueItem("item_1", "Test")

        # Should not raise
        item.mark_completed()
        item.mark_failed()


# ============================================================================
# VoiceSyncManager Tests
# ============================================================================

class TestVoiceSyncManager:
    """Test voice sync manager coordination."""

    def test_queue_narration_triggers_synthesis_and_playback(self):
        """queue_narration synthesizes audio and plays it."""
        # Mock TTS and audio player
        mock_tts = Mock()
        mock_tts.synthesize.return_value = b"synthesized_audio"

        mock_player = Mock()

        manager = VoiceSyncManager(mock_tts, mock_player)

        callback_triggered = []
        def callback():
            callback_triggered.append(True)

        # Queue narration
        manager.queue_narration("item_1", "Test narration", callback)

        # Wait for background thread to process
        manager.shutdown(timeout=2.0)

        # Verify TTS synthesize called
        mock_tts.synthesize.assert_called_once_with("Test narration")

        # Verify audio player called
        mock_player.play.assert_called_once_with(b"synthesized_audio")

        # Verify callback triggered
        assert len(callback_triggered) == 1

    def test_synthesis_failure_marks_failed_and_triggers_callback(self):
        """Synthesis failure marks item as FAILED, triggers callback."""
        mock_tts = Mock()
        mock_tts.synthesize.side_effect = Exception("TTS unavailable")

        mock_player = Mock()

        manager = VoiceSyncManager(mock_tts, mock_player)

        callback_triggered = []
        def callback():
            callback_triggered.append(True)

        manager.queue_narration("item_1", "Test narration", callback)

        # Wait for background thread
        manager.shutdown(timeout=2.0)

        # Verify item marked as failed
        item = manager.queue.get_item("item_1")
        assert item.status == AudioQueueStatus.FAILED

        # Verify callback triggered (UI can fallback to text)
        assert len(callback_triggered) == 1

    def test_wait_for_item_returns_true_when_completed(self):
        """wait_for_item returns True when item completes."""
        mock_tts = Mock()
        mock_tts.synthesize.return_value = b"audio"

        mock_player = Mock()

        manager = VoiceSyncManager(mock_tts, mock_player)
        manager.queue_narration("item_1", "Test")

        result = manager.wait_for_item("item_1", timeout=1.0)
        assert result is True
        manager.shutdown(timeout=2.0)

    def test_wait_for_item_returns_false_on_timeout(self):
        """wait_for_item returns False on timeout."""
        mock_tts = Mock()
        # Simulate very slow synthesis
        def slow_synthesize(text):
            time.sleep(2.0)
            return b"audio"
        mock_tts.synthesize = slow_synthesize

        mock_player = Mock()

        manager = VoiceSyncManager(mock_tts, mock_player)
        manager.queue_narration("item_1", "Test")

        result = manager.wait_for_item("item_1", timeout=0.1)
        assert result is False
        manager.shutdown(timeout=3.0)

    def test_get_status_returns_item_status(self):
        """get_status returns correct status after completion."""
        mock_tts = Mock()
        mock_tts.synthesize.return_value = b"audio"

        mock_player = Mock()

        manager = VoiceSyncManager(mock_tts, mock_player)
        manager.queue_narration("item_1", "Test")

        # Wait for completion
        manager.wait_for_item("item_1", timeout=1.0)

        status = manager.get_status("item_1")
        assert status == AudioQueueStatus.COMPLETED
        manager.shutdown(timeout=2.0)


# ============================================================================
# TextRevealController Tests
# ============================================================================

class TestTextRevealController:
    """Test text reveal controller for voice-first protocol."""

    def test_text_hidden_until_voice_completes(self):
        """Text reveal callback only triggered after voice completes."""
        mock_tts = Mock()
        mock_tts.synthesize.return_value = b"audio"

        mock_player = Mock()

        voice_sync = VoiceSyncManager(mock_tts, mock_player)
        controller = TextRevealController(voice_sync)

        revealed_text = []

        def on_reveal(text):
            revealed_text.append(text)

        # Queue narration with delayed text
        controller.queue_narration_with_delayed_text(
            "item_1",
            "Your sword strikes the goblin!",
            on_reveal
        )

        # Wait for voice to complete
        voice_sync.wait_for_item("item_1", timeout=1.0)
        voice_sync.shutdown(timeout=2.0)

        # Now text should be revealed
        assert len(revealed_text) == 1
        assert revealed_text[0] == "Your sword strikes the goblin!"

    def test_text_cleanup_after_reveal(self):
        """Hidden text is cleaned up after reveal."""
        mock_tts = Mock()
        mock_tts.synthesize.return_value = b"audio"

        mock_player = Mock()

        voice_sync = VoiceSyncManager(mock_tts, mock_player)
        controller = TextRevealController(voice_sync)

        controller.queue_narration_with_delayed_text(
            "item_1",
            "Test narration",
            lambda text: None
        )

        # Wait for completion
        voice_sync.wait_for_item("item_1", timeout=1.0)
        voice_sync.shutdown(timeout=2.0)

        # Hidden text should be cleaned up after reveal
        assert "item_1" not in controller._hidden_text


# ============================================================================
# VoicePlaybackStatus Tests
# ============================================================================

class TestVoicePlaybackStatus:
    """Test voice playback status reporting."""

    def test_from_queue_item_pending(self):
        """from_queue_item creates status for PENDING item."""
        item = AudioQueueItem("item_1", "Test narration")

        status = VoicePlaybackStatus.from_queue_item(item)

        assert status.item_id == "item_1"
        assert status.status == AudioQueueStatus.PENDING
        assert status.narration_text == "Test narration"
        assert status.synthesis_latency_ms is None
        assert status.playback_duration_ms is None

    def test_from_queue_item_with_latency(self):
        """from_queue_item calculates synthesis latency."""
        item = AudioQueueItem("item_1", "Test")

        item.mark_synthesizing()
        time.sleep(0.1)
        item.mark_playing(b"audio")

        status = VoicePlaybackStatus.from_queue_item(item)

        assert status.synthesis_latency_ms is not None
        assert status.synthesis_latency_ms >= 100  # At least 100ms
        assert status.playback_duration_ms is None  # Not completed yet

    def test_from_queue_item_with_duration(self):
        """from_queue_item calculates playback duration."""
        item = AudioQueueItem("item_1", "Test")

        item.mark_synthesizing()
        item.mark_playing(b"audio")
        time.sleep(0.05)
        item.mark_completed()

        status = VoicePlaybackStatus.from_queue_item(item)

        assert status.playback_duration_ms is not None
        assert status.playback_duration_ms >= 50  # At least 50ms


# ============================================================================
# VoiceStatusNotifier Tests
# ============================================================================

class TestVoiceStatusNotifier:
    """Test voice status notification pub-sub."""

    def test_subscribe_and_notify(self):
        """Subscribers receive notifications."""
        notifier = VoiceStatusNotifier()

        received_statuses = []

        def subscriber(status):
            received_statuses.append(status)

        notifier.subscribe(subscriber)

        status1 = VoicePlaybackStatus(
            item_id="item_1",
            status=AudioQueueStatus.SYNTHESIZING,
            narration_text="Test"
        )

        status2 = VoicePlaybackStatus(
            item_id="item_1",
            status=AudioQueueStatus.PLAYING,
            narration_text="Test"
        )

        notifier.notify(status1)
        notifier.notify(status2)

        assert len(received_statuses) == 2
        assert received_statuses[0].status == AudioQueueStatus.SYNTHESIZING
        assert received_statuses[1].status == AudioQueueStatus.PLAYING

    def test_multiple_subscribers(self):
        """Multiple subscribers all receive notifications."""
        notifier = VoiceStatusNotifier()

        received_1 = []
        received_2 = []

        notifier.subscribe(lambda status: received_1.append(status))
        notifier.subscribe(lambda status: received_2.append(status))

        status = VoicePlaybackStatus(
            item_id="item_1",
            status=AudioQueueStatus.COMPLETED,
            narration_text="Test"
        )

        notifier.notify(status)

        assert len(received_1) == 1
        assert len(received_2) == 1


# ============================================================================
# Thread Safety Tests
# ============================================================================

class TestThreadSafety:
    """Test thread-safe queue operations."""

    def test_concurrent_enqueue(self):
        """Multiple threads can enqueue safely."""
        queue = AudioQueue()

        def enqueue_items(start_id, count):
            for i in range(count):
                queue.enqueue(f"item_{start_id}_{i}", f"Narration {i}")

        threads = [
            threading.Thread(target=enqueue_items, args=(1, 50)),
            threading.Thread(target=enqueue_items, args=(2, 50)),
            threading.Thread(target=enqueue_items, args=(3, 50)),
        ]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # Should have all 150 items
        assert queue.get_queue_depth() == 150

    def test_concurrent_get_next_pending(self):
        """Multiple threads can get_next_pending safely."""
        queue = AudioQueue()

        # Enqueue items
        for i in range(100):
            queue.enqueue(f"item_{i}", f"Narration {i}")

        retrieved_items = []
        lock = threading.Lock()

        def get_items(count):
            for _ in range(count):
                item = queue.get_next_pending()
                if item:
                    with lock:
                        retrieved_items.append(item)
                    item.mark_playing(b"audio")

        threads = [
            threading.Thread(target=get_items, args=(30,)),
            threading.Thread(target=get_items, args=(30,)),
            threading.Thread(target=get_items, args=(30,)),
        ]

        for t in threads:
            t.start()

        for t in threads:
            t.join()

        # Should have retrieved 90 unique items
        item_ids = [item.item_id for item in retrieved_items]
        assert len(item_ids) == 90
        assert len(set(item_ids)) == 90  # All unique


# ============================================================================
# Integration Tests
# ============================================================================

class TestVoiceFirstIntegration:
    """Integration tests for voice-first protocol."""

    def test_full_voice_first_flow(self):
        """Complete flow: queue → synthesize → play → reveal text."""
        # Mock dependencies
        mock_tts = Mock()
        mock_tts.synthesize.return_value = b"synthesized_audio"

        mock_player = Mock()

        # Create voice sync manager
        voice_sync = VoiceSyncManager(mock_tts, mock_player)
        controller = TextRevealController(voice_sync)

        # Track text reveal
        revealed_text = []

        # Queue narration with delayed text
        controller.queue_narration_with_delayed_text(
            "combat_1",
            "Your blade strikes the goblin's shoulder!",
            lambda text: revealed_text.append(text)
        )

        # Wait for voice-first flow to complete
        voice_sync.wait_for_item("combat_1", timeout=1.0)
        voice_sync.shutdown(timeout=2.0)

        # Verify TTS called
        mock_tts.synthesize.assert_called_once_with(
            "Your blade strikes the goblin's shoulder!"
        )

        # Verify audio played
        mock_player.play.assert_called_once_with(b"synthesized_audio")

        # Verify text revealed AFTER voice
        assert len(revealed_text) == 1
        assert revealed_text[0] == "Your blade strikes the goblin's shoulder!"

    def test_voice_first_multiple_items(self):
        """Multiple narrations queue and reveal in order."""
        mock_tts = Mock()
        mock_tts.synthesize.return_value = b"audio"

        mock_player = Mock()

        voice_sync = VoiceSyncManager(mock_tts, mock_player)
        controller = TextRevealController(voice_sync)

        revealed_order = []

        # Queue 3 narrations
        controller.queue_narration_with_delayed_text(
            "item_1", "First narration",
            lambda text: revealed_order.append("item_1")
        )
        controller.queue_narration_with_delayed_text(
            "item_2", "Second narration",
            lambda text: revealed_order.append("item_2")
        )
        controller.queue_narration_with_delayed_text(
            "item_3", "Third narration",
            lambda text: revealed_order.append("item_3")
        )

        # Wait for all to complete
        voice_sync.wait_for_item("item_1", timeout=1.0)
        voice_sync.wait_for_item("item_2", timeout=1.0)
        voice_sync.wait_for_item("item_3", timeout=1.0)
        voice_sync.shutdown(timeout=2.0)

        # All items revealed
        assert len(revealed_order) == 3

    def test_voice_failure_still_reveals_text(self):
        """Voice failure triggers text reveal (fallback to text-only)."""
        mock_tts = Mock()
        mock_tts.synthesize.side_effect = Exception("TTS unavailable")

        mock_player = Mock()

        voice_sync = VoiceSyncManager(mock_tts, mock_player)
        controller = TextRevealController(voice_sync)

        revealed_text = []

        controller.queue_narration_with_delayed_text(
            "item_1",
            "Test narration",
            lambda text: revealed_text.append(text)
        )

        # Wait for failure
        voice_sync.wait_for_item("item_1", timeout=1.0)
        voice_sync.shutdown(timeout=2.0)

        # Text should still be revealed (fallback)
        assert len(revealed_text) == 1
        assert revealed_text[0] == "Test narration"
