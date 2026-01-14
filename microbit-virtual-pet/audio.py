"""
Audio System for Horror-Themed Virtual Pet
Implements creepy sound profiles using micro:bit V2 speaker
"""
from microbit import sleep
import music
import random


class AudioSystem:
    """
    Manages all audio feedback for the virtual pet.
    Uses PWM-based tone synthesis for unsettling soundscapes.
    """

    # Note frequencies (Hz) for musical composition
    NOTES = {
        'C2': 65, 'D2': 73, 'E2': 82, 'F2': 87, 'G2': 98, 'A2': 110, 'B2': 123,
        'C3': 131, 'D3': 147, 'E3': 165, 'F3': 175, 'G3': 196, 'A3': 220, 'B3': 247,
        'C4': 262, 'D4': 294, 'E4': 330, 'F4': 349, 'G4': 392, 'A4': 440, 'B4': 494,
        'C5': 523, 'D5': 587, 'E5': 659, 'F5': 698, 'G5': 784, 'A5': 880, 'B5': 988,
    }

    # Duration constants (milliseconds)
    BEAT_SHORT = 200
    BEAT_MEDIUM = 400
    BEAT_LONG = 800

    def __init__(self, enabled: bool = True):
        """
        Initialize audio system.

        Args:
            enabled: Whether audio is enabled (for testing/battery saving)
        """
        self.enabled = enabled
        self.last_sound_time = 0
        self.sound_cooldown = 100  # Minimum ms between sounds

    def play_idle_breathing(self) -> None:
        """
        Play ambient breathing sound.
        Low-frequency oscillation with irregular rhythm.
        """
        if not self.enabled:
            return

        # Irregular breathing pattern with pitch wobble
        frequencies = [
            self.NOTES['C2'] + random.randint(-5, 5),  # 65 Hz ± wobble
            self.NOTES['C2'] + random.randint(-3, 3),
            self.NOTES['G2'] + random.randint(-5, 5),  # 98 Hz ± wobble
        ]

        for freq in frequencies:
            music.pitch(freq, duration=200 + random.randint(-50, 50), wait=True)
            sleep(random.randint(50, 150))

    def play_hunger_alert(self, intensity: int) -> None:
        """
        Play escalating hunger alert based on intensity level.

        Args:
            intensity: 0-2 (mild, moderate, critical)
        """
        if not self.enabled:
            return

        if intensity == 0:
            # Mild: Whining tone sweep
            self._play_tone_sweep(300, 600, steps=8, duration=500)

        elif intensity == 1:
            # Moderate: Distorted clicking
            for _ in range(5):
                click_freq = random.randint(200, 400)
                music.pitch(click_freq, duration=50, wait=True)
                sleep(random.randint(100, 300))

        else:
            # Critical: Dissonant tritone (devil's interval)
            self._play_tritone_alarm()

    def _play_tone_sweep(self, start_freq: int, end_freq: int,
                         steps: int, duration: int) -> None:
        """
        Sweep from start frequency to end frequency.

        Args:
            start_freq: Starting frequency in Hz
            end_freq: Ending frequency in Hz
            steps: Number of steps in sweep
            duration: Total duration in milliseconds
        """
        step_size = (end_freq - start_freq) / steps
        step_duration = duration // steps

        for i in range(steps):
            freq = int(start_freq + (step_size * i))
            music.pitch(freq, duration=step_duration, wait=True)

    def _play_tritone_alarm(self) -> None:
        """
        Play tritone interval (augmented fourth) - the 'devil's interval'.
        Extremely dissonant and unsettling.
        """
        # F4 and B4 form a tritone
        base = self.NOTES['F4']
        tritone = self.NOTES['B4']

        for _ in range(3):
            music.pitch(base, duration=150, wait=False)
            music.pitch(tritone, duration=150, wait=True)
            sleep(100)

    def play_satisfaction_sound(self) -> None:
        """
        Play brief satisfaction sound after feeding/playing.
        Descending chromatic phrase with major-to-minor resolution.
        """
        if not self.enabled:
            return

        # Descending chromatic melody
        melody = [
            (self.NOTES['C5'], 150),
            (self.NOTES['B4'], 150),
            (self.NOTES['A4'], 150),
            (self.NOTES['G4'], 200),  # Major third
            (self.NOTES['E4'], 300),  # Resolve to minor
        ]

        for freq, duration in melody:
            music.pitch(freq, duration=duration, wait=True)
            sleep(50)

    def play_sickness_sound(self) -> None:
        """
        Play glitchy, corrupted sound for sickness state.
        Uses random pitch variations and stuttering.
        """
        if not self.enabled:
            return

        # Glitchy stuttering effect
        for _ in range(8):
            freq = random.randint(100, 500)
            duration = random.randint(30, 100)
            music.pitch(freq, duration=duration, wait=True)
            sleep(random.randint(20, 80))

    def play_death_sequence(self) -> None:
        """
        Play terminal death sequence.
        Glitch-style corruption with pitch drop to final thud.
        """
        if not self.enabled:
            return

        # Phase 1: Audio corruption/glitching
        for _ in range(10):
            freq = random.randint(200, 800)
            duration = random.randint(50, 150)
            music.pitch(freq, duration=duration, wait=True)
            sleep(random.randint(10, 50))

        sleep(200)

        # Phase 2: Pitch drop from A4 (440 Hz) to A1 (55 Hz)
        self._play_pitch_drop(440, 55, duration=3000)

        sleep(300)

        # Phase 3: Final percussive thud
        self._play_thud()

    def _play_pitch_drop(self, start_freq: int, end_freq: int,
                         duration: int) -> None:
        """
        Gradually drop pitch from start to end over duration.

        Args:
            start_freq: Starting frequency in Hz
            end_freq: Ending frequency in Hz
            duration: Total duration in milliseconds
        """
        steps = 30
        step_duration = duration // steps
        freq_step = (start_freq - end_freq) / steps

        for i in range(steps):
            freq = int(start_freq - (freq_step * i))
            music.pitch(freq, duration=step_duration, wait=True)

    def _play_thud(self) -> None:
        """Play low percussive thud sound"""
        music.pitch(30, duration=200, wait=True)  # Very low frequency
        sleep(100)
        music.pitch(25, duration=150, wait=True)

    def play_button_press(self) -> None:
        """
        Play subtle button feedback click.
        Short and non-intrusive.
        """
        if not self.enabled:
            return

        music.pitch(self.NOTES['C5'], duration=30, wait=True)

    def play_shake_acknowledgment(self) -> None:
        """
        Play sound when shake is detected.
        Quick rising tone.
        """
        if not self.enabled:
            return

        self._play_tone_sweep(300, 800, steps=5, duration=200)

    def play_startup_sound(self) -> None:
        """
        Play ominous startup/reboot sequence.
        Low to high sweep with unsettling finish.
        """
        if not self.enabled:
            return

        # Low rumble building up
        self._play_tone_sweep(50, 400, steps=10, duration=1000)
        sleep(200)

        # Quick descending finish (suggests something awakening)
        melody = [
            (self.NOTES['G4'], 150),
            (self.NOTES['E4'], 150),
            (self.NOTES['C4'], 200),
        ]

        for freq, duration in melody:
            music.pitch(freq, duration=duration, wait=True)

    def play_critical_warning(self) -> None:
        """
        Play urgent warning sound for critical states.
        Rapid alternating tones.
        """
        if not self.enabled:
            return

        for _ in range(4):
            music.pitch(self.NOTES['A4'], duration=100, wait=True)
            music.pitch(self.NOTES['D4'], duration=100, wait=True)

    def stop_all(self) -> None:
        """Stop all audio playback"""
        music.stop()

    def set_enabled(self, enabled: bool) -> None:
        """
        Enable or disable audio.

        Args:
            enabled: True to enable, False to disable
        """
        self.enabled = enabled
        if not enabled:
            self.stop_all()


# Audio intensity mapping for hunger states
def get_hunger_intensity(hunger_level: int) -> int:
    """
    Map hunger level to audio intensity.

    Args:
        hunger_level: Hunger value (0-100)

    Returns:
        Intensity level (0-2)
    """
    if hunger_level < 50:
        return 0  # Mild
    elif hunger_level < 80:
        return 1  # Moderate
    else:
        return 2  # Critical
