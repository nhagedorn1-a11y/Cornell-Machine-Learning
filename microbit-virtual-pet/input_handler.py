"""
Input Handler for Virtual Pet
Manages button inputs and accelerometer-based gestures with debouncing
"""
from microbit import button_a, button_b, accelerometer, running_time
import random


class InputHandler:
    """
    Handles all user input with proper debouncing and gesture detection.
    Prevents button mashing and provides smooth interaction.
    """

    # Debounce and cooldown constants (milliseconds)
    BUTTON_DEBOUNCE = 50       # Minimum time between button state changes
    BUTTON_COOLDOWN = 500      # Minimum time between button actions
    COMBO_WINDOW = 300         # Time window for A+B combo detection
    LONG_PRESS_DURATION = 2000 # Duration for long press detection

    # Shake detection thresholds
    SHAKE_THRESHOLD = 1500     # Acceleration magnitude for shake detection
    SHAKE_COOLDOWN = 1000      # Minimum time between shake detections

    def __init__(self):
        """Initialize input handler"""
        # Button states
        self.button_a_pressed = False
        self.button_b_pressed = False
        self.last_button_a_time = 0
        self.last_button_b_time = 0
        self.last_action_time = 0

        # Combo detection
        self.combo_start_time = 0
        self.combo_active = False

        # Long press detection
        self.long_press_start = 0
        self.long_press_triggered = False

        # Shake detection
        self.last_shake_time = 0
        self.shake_count = 0

        # Accelerometer baseline
        self.baseline_x = 0
        self.baseline_y = 0
        self.baseline_z = 0
        self._calibrate_accelerometer()

    def _calibrate_accelerometer(self) -> None:
        """Calibrate accelerometer baseline (device at rest)"""
        # Take average of a few samples
        samples = 5
        total_x = total_y = total_z = 0

        for _ in range(samples):
            total_x += accelerometer.get_x()
            total_y += accelerometer.get_y()
            total_z += accelerometer.get_z()

        self.baseline_x = total_x // samples
        self.baseline_y = total_y // samples
        self.baseline_z = total_z // samples

    def update(self) -> dict:
        """
        Update input state and detect gestures.

        Returns:
            Dictionary of detected inputs:
            {
                'button_a': bool,
                'button_b': bool,
                'combo': bool,
                'shake': bool,
                'long_press': bool
            }
        """
        current_time = running_time()
        result = {
            'button_a': False,
            'button_b': False,
            'combo': False,
            'shake': False,
            'long_press': False
        }

        # Check for cooldown period
        if current_time - self.last_action_time < self.BUTTON_COOLDOWN:
            return result

        # Detect button presses with debouncing
        button_a_state = button_a.is_pressed()
        button_b_state = button_b.is_pressed()

        # Button A handling
        if button_a_state and not self.button_a_pressed:
            if current_time - self.last_button_a_time > self.BUTTON_DEBOUNCE:
                self.button_a_pressed = True
                self.last_button_a_time = current_time
                self._check_combo_start(current_time)

        elif not button_a_state and self.button_a_pressed:
            self.button_a_pressed = False

        # Button B handling
        if button_b_state and not self.button_b_pressed:
            if current_time - self.last_button_b_time > self.BUTTON_DEBOUNCE:
                self.button_b_pressed = True
                self.last_button_b_time = current_time
                self._check_combo_start(current_time)

        elif not button_b_state and self.button_b_pressed:
            self.button_b_pressed = False

        # Combo detection (A+B pressed simultaneously)
        if self.button_a_pressed and self.button_b_pressed:
            if not self.combo_active:
                result['combo'] = True
                self.combo_active = True
                self.last_action_time = current_time
        else:
            self.combo_active = False

        # Individual button actions (only if not combo)
        if not result['combo']:
            if self.button_a_pressed and current_time - self.last_button_a_time < 100:
                result['button_a'] = True
                self.last_action_time = current_time

            if self.button_b_pressed and current_time - self.last_button_b_time < 100:
                result['button_b'] = True
                self.last_action_time = current_time

        # Long press detection (for reset)
        if self.button_a_pressed and self.button_b_pressed:
            if self.long_press_start == 0:
                self.long_press_start = current_time

            if not self.long_press_triggered:
                if current_time - self.long_press_start > self.LONG_PRESS_DURATION:
                    result['long_press'] = True
                    self.long_press_triggered = True
        else:
            self.long_press_start = 0
            self.long_press_triggered = False

        # Shake detection
        shake_detected = self._detect_shake(current_time)
        if shake_detected:
            result['shake'] = True
            self.last_action_time = current_time

        return result

    def _check_combo_start(self, current_time: int) -> None:
        """
        Check if combo window should be started.

        Args:
            current_time: Current timestamp in milliseconds
        """
        if self.combo_start_time == 0:
            self.combo_start_time = current_time

        # Reset combo window if too much time passed
        if current_time - self.combo_start_time > self.COMBO_WINDOW:
            self.combo_start_time = current_time

    def _detect_shake(self, current_time: int) -> bool:
        """
        Detect shake gesture using accelerometer.

        Args:
            current_time: Current timestamp in milliseconds

        Returns:
            True if shake detected
        """
        # Check cooldown
        if current_time - self.last_shake_time < self.SHAKE_COOLDOWN:
            return False

        # Get current acceleration
        x = accelerometer.get_x()
        y = accelerometer.get_y()
        z = accelerometer.get_z()

        # Calculate deviation from baseline
        dx = abs(x - self.baseline_x)
        dy = abs(y - self.baseline_y)
        dz = abs(z - self.baseline_z)

        # Calculate total magnitude of shake
        magnitude = (dx * dx + dy * dy + dz * dz) ** 0.5

        # Check if magnitude exceeds threshold
        if magnitude > self.SHAKE_THRESHOLD:
            self.last_shake_time = current_time
            self.shake_count += 1
            return True

        return False

    def get_shake_count(self) -> int:
        """Get total number of shakes detected"""
        return self.shake_count

    def reset_shake_count(self) -> None:
        """Reset shake counter"""
        self.shake_count = 0

    def is_button_a_pressed(self) -> bool:
        """Check if button A is currently pressed"""
        return button_a.is_pressed()

    def is_button_b_pressed(self) -> bool:
        """Check if button B is currently pressed"""
        return button_b.is_pressed()

    def get_tilt_angle(self) -> tuple:
        """
        Get current tilt angles.

        Returns:
            Tuple of (pitch, roll) in degrees
        """
        x = accelerometer.get_x()
        y = accelerometer.get_y()
        z = accelerometer.get_z()

        # Calculate pitch and roll (simplified)
        # These are approximations
        pitch = int((x / 1000) * 90)  # -90 to +90 degrees
        roll = int((y / 1000) * 90)   # -90 to +90 degrees

        return (pitch, roll)

    def is_upside_down(self) -> bool:
        """
        Check if device is upside down.

        Returns:
            True if upside down
        """
        z = accelerometer.get_z()
        return z < -500  # Threshold for upside down detection

    def is_face_up(self) -> bool:
        """
        Check if device is face up (flat on surface).

        Returns:
            True if face up
        """
        z = accelerometer.get_z()
        return z > 500 and abs(accelerometer.get_x()) < 200 and abs(accelerometer.get_y()) < 200

    def is_face_down(self) -> bool:
        """
        Check if device is face down.

        Returns:
            True if face down
        """
        z = accelerometer.get_z()
        return z < -500 and abs(accelerometer.get_x()) < 200 and abs(accelerometer.get_y()) < 200


class GestureDetector:
    """
    Advanced gesture detection for special interactions.
    Optional extension for future features.
    """

    def __init__(self):
        """Initialize gesture detector"""
        self.gesture_buffer = []
        self.max_buffer_size = 20

    def add_reading(self, x: int, y: int, z: int) -> None:
        """
        Add accelerometer reading to gesture buffer.

        Args:
            x: X-axis acceleration
            y: Y-axis acceleration
            z: Z-axis acceleration
        """
        self.gesture_buffer.append((x, y, z))

        # Keep buffer size limited
        if len(self.gesture_buffer) > self.max_buffer_size:
            self.gesture_buffer.pop(0)

    def detect_pattern(self, pattern_name: str) -> bool:
        """
        Detect specific gesture pattern.

        Args:
            pattern_name: Name of pattern to detect

        Returns:
            True if pattern detected
        """
        # Placeholder for future gesture recognition
        # Could detect patterns like:
        # - "circle" - circular motion
        # - "shake_x" - shake along X axis
        # - "flip" - 180 degree flip
        return False

    def clear_buffer(self) -> None:
        """Clear gesture buffer"""
        self.gesture_buffer = []
