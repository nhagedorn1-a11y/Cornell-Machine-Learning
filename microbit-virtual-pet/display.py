"""
LED Display System for Horror-Themed Virtual Pet
Manages 5x5 LED matrix animations and visual feedback
"""
from microbit import display, Image, sleep
import random


class DisplaySystem:
    """
    Manages all visual feedback on the 5x5 LED matrix.
    Creates creepy animations and state-dependent visuals.
    """

    # Animation frame constants
    FRAME_DELAY = 200  # Default ms between animation frames

    # Custom sprite definitions (5x5 matrix, 0-9 brightness levels)
    IDLE_FRAME_1 = Image(
        "09990:"
        "90909:"
        "99999:"
        "90909:"
        "09090"
    )

    IDLE_FRAME_2 = Image(
        "09990:"
        "99999:"
        "90909:"
        "99999:"
        "09090"
    )

    # Hungry state - creature approaching
    HUNGRY_FRAME_1 = Image(
        "90009:"
        "09990:"
        "99999:"
        "09990:"
        "90009"
    )

    HUNGRY_FRAME_2 = Image(
        "09090:"
        "90909:"
        "99999:"
        "90909:"
        "09090"
    )

    HUNGRY_FRAME_3 = Image(
        "00900:"
        "09990:"
        "99999:"
        "09990:"
        "00900"
    )

    # Happy state - satisfied creature
    HAPPY_FRAME = Image(
        "09090:"
        "09090:"
        "00000:"
        "90009:"
        "09990"
    )

    # Sick state - corrupted/glitchy
    SICK_FRAME_1 = Image(
        "90909:"
        "09090:"
        "90909:"
        "09090:"
        "90909"
    )

    SICK_FRAME_2 = Image(
        "09090:"
        "90909:"
        "09090:"
        "90909:"
        "09090"
    )

    # Death state frames
    DEATH_FRAME_1 = Image(
        "90009:"
        "09090:"
        "00900:"
        "09090:"
        "90009"
    )

    DEATH_FRAME_FINAL = Image(
        "00000:"
        "00000:"
        "00900:"
        "00000:"
        "00000"
    )

    # Critical warning pattern
    WARNING_FRAME = Image(
        "90009:"
        "09090:"
        "00900:"
        "09090:"
        "90009"
    )

    def __init__(self):
        """Initialize display system"""
        self.current_frame = 0
        self.animation_counter = 0
        self.flash_state = False
        self.last_update = 0

    def show_idle_animation(self) -> None:
        """
        Display idle breathing animation.
        2-frame oscillation suggesting subtle movement.
        """
        frames = [self.IDLE_FRAME_1, self.IDLE_FRAME_2]
        display.show(frames[self.current_frame % 2])
        self.current_frame += 1

    def show_hungry_animation(self, intensity: int) -> None:
        """
        Display hunger animation with increasing aggression.

        Args:
            intensity: 0-2 (mild, moderate, critical)
        """
        if intensity == 2:
            # Critical: Rapid flashing with crawling effect
            if self.flash_state:
                display.show(self.HUNGRY_FRAME_3)
            else:
                display.show(self.WARNING_FRAME)
            self.flash_state = not self.flash_state

        elif intensity == 1:
            # Moderate: Faster animation cycle
            frames = [self.HUNGRY_FRAME_1, self.HUNGRY_FRAME_2, self.HUNGRY_FRAME_3]
            display.show(frames[self.current_frame % 3])
            self.current_frame += 1

        else:
            # Mild: Slow approach animation
            frames = [self.IDLE_FRAME_1, self.HUNGRY_FRAME_1]
            display.show(frames[self.current_frame % 2])
            self.current_frame += 1

    def show_happy_animation(self) -> None:
        """
        Display brief happiness animation.
        Shows satisfied expression.
        """
        display.show(self.HAPPY_FRAME)

    def show_sick_animation(self) -> None:
        """
        Display glitchy corruption pattern for sickness.
        Rapid alternating frames suggesting visual distortion.
        """
        frames = [self.SICK_FRAME_1, self.SICK_FRAME_2]
        display.show(frames[self.current_frame % 2])
        self.current_frame += 1

    def show_death_sequence(self) -> None:
        """
        Display death animation sequence.
        Pixel-by-pixel extinction using random walk algorithm.
        """
        # Phase 1: Rapid flickering
        for _ in range(10):
            if random.randint(0, 1):
                display.show(self.DEATH_FRAME_1)
            else:
                display.clear()
            sleep(100)

        # Phase 2: Random pixel decay
        self._pixel_decay_animation()

        # Phase 3: Final pulse before darkness
        for _ in range(3):
            display.show(self.DEATH_FRAME_FINAL)
            sleep(300)
            display.clear()
            sleep(300)

        # Phase 4: Complete darkness
        display.clear()

    def _pixel_decay_animation(self) -> None:
        """
        Randomly extinguish pixels one by one.
        Creates organic decay effect.
        """
        # Create list of all LED positions
        pixels = [(x, y) for x in range(5) for y in range(5)]
        random.shuffle(pixels)

        # Start with full brightness
        current_brightness = [[9 for _ in range(5)] for _ in range(5)]

        # Decay each pixel randomly
        for x, y in pixels:
            current_brightness[x][y] = 0

            # Convert brightness matrix to Image string
            image_str = ""
            for row in current_brightness:
                image_str += "".join(str(b) for b in row) + ":"

            display.show(Image(image_str[:-1]))  # Remove trailing colon
            sleep(random.randint(50, 150))

    def show_warning_flash(self) -> None:
        """
        Display critical warning flash.
        Rapid flashing to indicate urgent attention needed.
        """
        if self.flash_state:
            display.show(self.WARNING_FRAME)
        else:
            display.clear()
        self.flash_state = not self.flash_state

    def show_startup_sequence(self) -> None:
        """
        Display ominous startup/awakening sequence.
        Gradually illuminate the creature.
        """
        # Phase 1: Pixel-by-pixel awakening
        pixels = [(x, y) for x in range(5) for y in range(5)]
        random.shuffle(pixels)

        brightness = [[0 for _ in range(5)] for _ in range(5)]

        for x, y in pixels:
            brightness[x][y] = 9

            # Convert to Image
            image_str = ""
            for row in brightness:
                image_str += "".join(str(b) for b in row) + ":"

            display.show(Image(image_str[:-1]))
            sleep(random.randint(30, 80))

        sleep(300)

        # Phase 2: Settle into idle state
        display.show(self.IDLE_FRAME_1)
        sleep(500)

    def show_feed_feedback(self) -> None:
        """
        Display brief feeding animation.
        Quick flash to acknowledge feeding action.
        """
        # Pulse animation
        for brightness in [3, 6, 9, 6, 3]:
            image_str = f"{brightness}" * 25
            formatted = ":".join([image_str[i:i+5] for i in range(0, 25, 5)])
            display.show(Image(formatted))
            sleep(50)

        # Show happy face
        self.show_happy_animation()

    def show_play_feedback(self) -> None:
        """
        Display brief play/shake animation.
        Spinning effect.
        """
        # Spinning animation
        spin_frames = [
            Image("00900:00900:99999:00000:00000"),
            Image("00009:00090:00900:09000:90000"),
            Image("00000:00000:99999:00900:00900"),
            Image("90000:09000:00900:00090:00009"),
        ]

        for frame in spin_frames:
            display.show(frame)
            sleep(100)

        # Show happy face
        self.show_happy_animation()

    def show_text_scroll(self, text: str, delay: int = 100) -> None:
        """
        Scroll text across display.

        Args:
            text: Text to display
            delay: Delay between characters in ms
        """
        display.scroll(text, delay=delay, wait=True)

    def show_heart(self) -> None:
        """Display a heart (for special occasions)"""
        display.show(Image.HEART)

    def show_skull(self) -> None:
        """Display a skull (for death state)"""
        display.show(Image.SKULL)

    def clear(self) -> None:
        """Clear the display"""
        display.clear()

    def set_pixel(self, x: int, y: int, brightness: int) -> None:
        """
        Set individual pixel brightness.

        Args:
            x: X coordinate (0-4)
            y: Y coordinate (0-4)
            brightness: Brightness level (0-9)
        """
        display.set_pixel(x, y, brightness)

    def get_pixel(self, x: int, y: int) -> int:
        """
        Get individual pixel brightness.

        Args:
            x: X coordinate (0-4)
            y: Y coordinate (0-4)

        Returns:
            Brightness level (0-9)
        """
        return display.get_pixel(x, y)


def get_hunger_display_intensity(hunger_level: int) -> int:
    """
    Map hunger level to display intensity.

    Args:
        hunger_level: Hunger value (0-100)

    Returns:
        Display intensity level (0-2)
    """
    if hunger_level < 50:
        return 0  # Mild
    elif hunger_level < 80:
        return 1  # Moderate
    else:
        return 2  # Critical
