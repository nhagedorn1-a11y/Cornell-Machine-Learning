"""
Huggy Wuggy Virtual Pet - Main Application
Horror-themed Tamagotchi-style game for BBC micro:bit V2

Controls:
- Button A: Feed the creature
- Button B: Play with the creature (or shake device)
- A+B (hold 2s): Reset/Factory reset
- Shake: Play interaction

Author: Claude Code
Version: 1.0.0
"""
from microbit import running_time, sleep, display, button_a, button_b
from pet import VirtualPet, PetState
from display import DisplaySystem, get_hunger_display_intensity
from audio import AudioSystem, get_hunger_intensity
from input_handler import InputHandler


class VirtualPetGame:
    """
    Main game controller integrating all subsystems.
    Manages game loop and coordinates between pet logic, display, and audio.
    """

    # Game loop timing
    UPDATE_INTERVAL = 100      # Update every 100ms (10 FPS)
    ANIMATION_INTERVAL = 500   # Animate every 500ms
    AUDIO_INTERVAL = 3000      # Play ambient audio every 3s
    STATS_DISPLAY_INTERVAL = 10000  # Show stats every 10s

    def __init__(self, audio_enabled: bool = True):
        """
        Initialize the game.

        Args:
            audio_enabled: Whether to enable audio (disable for testing/battery)
        """
        # Initialize subsystems
        self.pet = VirtualPet()
        self.display_system = DisplaySystem()
        self.audio_system = AudioSystem(enabled=audio_enabled)
        self.input_handler = InputHandler()

        # Timing variables
        self.last_update_time = 0
        self.last_animation_time = 0
        self.last_audio_time = 0
        self.last_stats_time = 0
        self.game_start_time = 0

        # Game state
        self.running = True
        self.audio_enabled = audio_enabled

    def start(self) -> None:
        """Start the game with intro sequence"""
        # Show startup animation
        self.display_system.show_startup_sequence()

        if self.audio_enabled:
            self.audio_system.play_startup_sound()

        sleep(500)

        # Display welcome message
        self.display_system.show_text_scroll("HUGGY", delay=150)
        sleep(300)

        # Initialize timing
        self.game_start_time = running_time()
        self.last_update_time = self.game_start_time
        self.last_animation_time = self.game_start_time
        self.last_audio_time = self.game_start_time
        self.last_stats_time = self.game_start_time

        # Enter main loop
        self.run_game_loop()

    def run_game_loop(self) -> None:
        """Main game loop"""
        while self.running:
            current_time = running_time()

            # Update pet state
            if current_time - self.last_update_time >= self.UPDATE_INTERVAL:
                self.update_pet(current_time)
                self.last_update_time = current_time

            # Handle input
            self.handle_input(current_time)

            # Update animations
            if current_time - self.last_animation_time >= self.ANIMATION_INTERVAL:
                self.update_display(current_time)
                self.last_animation_time = current_time

            # Play ambient audio
            if current_time - self.last_audio_time >= self.AUDIO_INTERVAL:
                self.play_ambient_audio(current_time)
                self.last_audio_time = current_time

            # Periodic stats display
            if current_time - self.last_stats_time >= self.STATS_DISPLAY_INTERVAL:
                self.show_stats_briefly()
                self.last_stats_time = current_time

            # Small delay to prevent CPU overuse
            sleep(10)

    def update_pet(self, current_time: int) -> None:
        """
        Update pet state and handle state transitions.

        Args:
            current_time: Current timestamp in milliseconds
        """
        previous_state = self.pet.state
        self.pet.update(current_time)

        # Detect state transitions
        if previous_state != self.pet.state:
            self.on_state_change(previous_state, self.pet.state, current_time)

    def on_state_change(self, old_state: int, new_state: int, current_time: int) -> None:
        """
        Handle state transitions with appropriate feedback.

        Args:
            old_state: Previous state
            new_state: New state
            current_time: Current timestamp
        """
        # Update pet's state entry time
        self.pet.state_entry_time = current_time

        # Play transition audio
        if new_state == PetState.HUNGRY:
            if self.audio_enabled:
                intensity = get_hunger_intensity(int(self.pet.hunger))
                self.audio_system.play_hunger_alert(intensity)

        elif new_state == PetState.SICK:
            if self.audio_enabled:
                self.audio_system.play_sickness_sound()

        elif new_state == PetState.HAPPY:
            if self.audio_enabled:
                self.audio_system.play_satisfaction_sound()

        elif new_state == PetState.DEATH:
            self.on_death()

    def on_death(self) -> None:
        """Handle creature death"""
        # Play death sequence
        if self.audio_enabled:
            self.audio_system.play_death_sequence()

        self.display_system.show_death_sequence()

        sleep(1000)

        # Show final stats
        stats = self.pet.get_stats_summary()
        self.display_system.show_text_scroll(
            f"AGE:{stats['age']}s INT:{stats['interactions']}",
            delay=100
        )

        sleep(500)

        # Show skull and wait for reset
        self.display_system.show_skull()
        self.wait_for_reset()

    def handle_input(self, current_time: int) -> None:
        """
        Process user input and trigger appropriate actions.

        Args:
            current_time: Current timestamp in milliseconds
        """
        inputs = self.input_handler.update()

        # Long press = factory reset
        if inputs['long_press']:
            self.trigger_reset()
            return

        # Emergency care (A+B combo)
        if inputs['combo']:
            if self.pet.emergency_care(current_time):
                if self.audio_enabled:
                    self.audio_system.play_critical_warning()
                    self.audio_system.play_satisfaction_sound()
                self.display_system.show_feed_feedback()

        # Feed (Button A)
        elif inputs['button_a']:
            if self.pet.feed(current_time):
                if self.audio_enabled:
                    self.audio_system.play_button_press()
                    self.audio_system.play_satisfaction_sound()
                self.display_system.show_feed_feedback()

        # Play (Button B or Shake)
        elif inputs['button_b'] or inputs['shake']:
            if self.pet.play(current_time):
                if self.audio_enabled:
                    if inputs['shake']:
                        self.audio_system.play_shake_acknowledgment()
                    else:
                        self.audio_system.play_button_press()
                    self.audio_system.play_satisfaction_sound()
                self.display_system.show_play_feedback()

    def update_display(self, current_time: int) -> None:
        """
        Update LED display based on current pet state.

        Args:
            current_time: Current timestamp in milliseconds
        """
        state = self.pet.state

        if state == PetState.IDLE:
            self.display_system.show_idle_animation()

        elif state == PetState.HUNGRY:
            intensity = get_hunger_display_intensity(int(self.pet.hunger))
            self.display_system.show_hungry_animation(intensity)

        elif state == PetState.HAPPY:
            self.display_system.show_happy_animation()

        elif state == PetState.SICK:
            self.display_system.show_sick_animation()

        elif state == PetState.DEATH:
            # Death animation handled in on_death()
            pass

    def play_ambient_audio(self, current_time: int) -> None:
        """
        Play ambient background audio based on state.

        Args:
            current_time: Current timestamp in milliseconds
        """
        if not self.audio_enabled or not self.pet.is_alive:
            return

        state = self.pet.state

        if state == PetState.IDLE:
            self.audio_system.play_idle_breathing()

        elif state == PetState.HUNGRY:
            intensity = get_hunger_intensity(int(self.pet.hunger))
            self.audio_system.play_hunger_alert(intensity)

        elif state == PetState.SICK:
            self.audio_system.play_sickness_sound()

    def show_stats_briefly(self) -> None:
        """Briefly display pet stats"""
        stats = self.pet.get_stats_summary()

        # Clear display
        self.display_system.clear()
        sleep(200)

        # Show hunger level as bar graph
        hunger_bars = int(stats['hunger'] / 20)  # 0-5 bars
        for i in range(5):
            brightness = 9 if i < hunger_bars else 0
            for x in range(5):
                self.display_system.set_pixel(x, i, brightness)

        sleep(1000)

    def trigger_reset(self) -> None:
        """Trigger factory reset with confirmation"""
        # Show warning
        self.display_system.show_text_scroll("RESET?", delay=100)

        # Play ominous sound
        if self.audio_enabled:
            self.audio_system.play_death_sequence()

        # Wait for confirmation
        sleep(500)

        # Reset pet
        self.pet.reset()

        # Restart game
        self.start()

    def wait_for_reset(self) -> None:
        """Wait for user to reset after death"""
        while True:
            # Check for A+B long press
            if button_a.is_pressed() and button_b.is_pressed():
                sleep(2000)
                if button_a.is_pressed() and button_b.is_pressed():
                    self.trigger_reset()
                    return

            sleep(100)

    def toggle_audio(self) -> None:
        """Toggle audio on/off"""
        self.audio_enabled = not self.audio_enabled
        self.audio_system.set_enabled(self.audio_enabled)

        if self.audio_enabled:
            self.display_system.show_text_scroll("SOUND ON", delay=80)
        else:
            self.display_system.show_text_scroll("SOUND OFF", delay=80)


def main():
    """Entry point for the application"""
    try:
        # Create and start game
        # Set audio_enabled=False for silent mode (battery saving)
        game = VirtualPetGame(audio_enabled=True)
        game.start()

    except KeyboardInterrupt:
        # Handle Ctrl+C gracefully
        display.clear()
        print("Game terminated by user")

    except Exception as e:
        # Handle any errors
        display.clear()
        display.scroll(f"ERROR: {str(e)}", delay=100)
        print(f"Error: {e}")


# Run the game
if __name__ == "__main__":
    main()
