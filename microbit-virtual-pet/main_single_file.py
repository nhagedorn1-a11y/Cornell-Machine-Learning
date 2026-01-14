"""
Huggy Wuggy Virtual Pet - Single File Version
Horror-themed Tamagotchi-style game for BBC micro:bit V2

Controls:
- Button A: Feed the creature
- Button B: Play with the creature
- Shake: Play interaction
- A+B (hold 2s): Reset/Factory reset

Simply copy this ENTIRE file and paste it into https://python.microbit.org/
Then click "Download" to flash it to your micro:bit!

Author: Claude Code
Version: 1.0.0
"""
from microbit import *
import random
import music


# ============================================================================
# PET STATE MANAGEMENT
# ============================================================================

class PetState:
    """Enumeration of possible pet states"""
    IDLE = 0
    HUNGRY = 1
    SICK = 2
    HAPPY = 3
    DEATH = 4


class VirtualPet:
    """Core virtual pet logic with finite state machine"""

    HUNGER_THRESHOLD = 30000
    CRITICAL_THRESHOLD = 60000
    HAPPY_DURATION = 5000
    DEATH_TIMER = 90000
    HUNGER_DECAY_RATE = 1.5
    HAPPINESS_DECAY_RATE = 0.8
    HEALTH_DECAY_RATE = 0.5

    def __init__(self):
        self.state = PetState.IDLE
        self.previous_state = None
        self.hunger = 50
        self.happiness = 70
        self.health = 100
        self.age = 0
        self.last_feed_time = 0
        self.last_play_time = 0
        self.state_entry_time = 0
        self.death_timer = 0
        self.is_alive = True
        self.is_critical = False
        self.interaction_count = 0

    def update(self, current_time):
        if not self.is_alive:
            return

        time_since_feed = current_time - self.last_feed_time
        time_since_play = current_time - self.last_play_time
        time_in_state = current_time - self.state_entry_time
        self.age = current_time // 1000

        # Decay stats
        hunger_increase = (time_since_feed / 1000) * self.HUNGER_DECAY_RATE
        self.hunger = min(100, self.hunger + hunger_increase * 0.01)

        happiness_decrease = (time_since_play / 1000) * self.HAPPINESS_DECAY_RATE
        self.happiness = max(0, self.happiness - happiness_decrease * 0.01)

        if self.hunger > 70 or self.happiness < 30:
            health_decrease = self.HEALTH_DECAY_RATE * 0.1
            self.health = max(0, self.health - health_decrease)

        # State transitions
        if self.health <= 0 or time_since_feed > self.DEATH_TIMER:
            self._transition_to_state(PetState.DEATH)
            self.is_alive = False
            return

        if self.health < 30 or (self.hunger > 80 and self.happiness < 20):
            self._transition_to_state(PetState.SICK)
            return

        if self.state == PetState.HAPPY and time_in_state > self.HAPPY_DURATION:
            self._transition_to_state(PetState.IDLE)
            return

        if self.hunger > 70:
            self._transition_to_state(PetState.HUNGRY)
            self.is_critical = self.hunger > 85
            return

        if self.state != PetState.HAPPY and self.hunger < 50 and self.happiness > 40:
            self._transition_to_state(PetState.IDLE)

    def _transition_to_state(self, new_state):
        if self.state != new_state:
            self.previous_state = self.state
            self.state = new_state
            self.state_entry_time = 0

    def feed(self, current_time):
        if not self.is_alive or self.state == PetState.DEATH:
            return False

        self.hunger = max(0, self.hunger - 30)
        if self.hunger > 60:
            self.health = min(100, self.health + 10)

        self.last_feed_time = current_time
        self.interaction_count += 1
        self._transition_to_state(PetState.HAPPY)
        return True

    def play(self, current_time):
        if not self.is_alive or self.state == PetState.DEATH:
            return False

        self.happiness = min(100, self.happiness + 25)
        self.health = min(100, self.health + 5)
        self.hunger = min(100, self.hunger + 10)
        self.last_play_time = current_time
        self.interaction_count += 1
        self._transition_to_state(PetState.HAPPY)
        return True

    def emergency_care(self, current_time):
        if not self.is_alive or self.state == PetState.DEATH:
            return False

        self.hunger = max(0, self.hunger - 40)
        self.happiness = min(100, self.happiness + 30)
        self.health = min(100, self.health + 20)
        self.last_feed_time = current_time
        self.last_play_time = current_time
        self.interaction_count += 1
        self.is_critical = False
        self._transition_to_state(PetState.HAPPY)
        return True

    def reset(self):
        self.__init__()


# ============================================================================
# AUDIO SYSTEM
# ============================================================================

class AudioSystem:
    """Manages all audio feedback"""

    NOTES = {
        'C2': 65, 'D2': 73, 'E2': 82, 'F2': 87, 'G2': 98, 'A2': 110,
        'C3': 131, 'D3': 147, 'E3': 165, 'F3': 175, 'G3': 196, 'A3': 220,
        'C4': 262, 'D4': 294, 'E4': 330, 'F4': 349, 'G4': 392, 'A4': 440,
        'C5': 523, 'D5': 587, 'E5': 659, 'F5': 698, 'G5': 784, 'A5': 880,
    }

    def __init__(self, enabled=True):
        self.enabled = enabled

    def play_idle_breathing(self):
        if not self.enabled:
            return
        frequencies = [
            self.NOTES['C2'] + random.randint(-5, 5),
            self.NOTES['C2'] + random.randint(-3, 3),
            self.NOTES['G2'] + random.randint(-5, 5),
        ]
        for freq in frequencies:
            music.pitch(freq, duration=200 + random.randint(-50, 50), wait=True)
            sleep(random.randint(50, 150))

    def play_hunger_alert(self, intensity):
        if not self.enabled:
            return

        if intensity == 0:
            self._play_tone_sweep(300, 600, 8, 500)
        elif intensity == 1:
            for _ in range(5):
                music.pitch(random.randint(200, 400), duration=50, wait=True)
                sleep(random.randint(100, 300))
        else:
            self._play_tritone_alarm()

    def _play_tone_sweep(self, start_freq, end_freq, steps, duration):
        step_size = (end_freq - start_freq) / steps
        step_duration = duration // steps
        for i in range(steps):
            freq = int(start_freq + (step_size * i))
            music.pitch(freq, duration=step_duration, wait=True)

    def _play_tritone_alarm(self):
        base = self.NOTES['F4']
        tritone = self.NOTES['B4']
        for _ in range(3):
            music.pitch(base, duration=150, wait=False)
            music.pitch(tritone, duration=150, wait=True)
            sleep(100)

    def play_satisfaction_sound(self):
        if not self.enabled:
            return
        melody = [
            (self.NOTES['C5'], 150),
            (self.NOTES['A4'], 150),
            (self.NOTES['G4'], 200),
            (self.NOTES['E4'], 300),
        ]
        for freq, dur in melody:
            music.pitch(freq, duration=dur, wait=True)
            sleep(50)

    def play_sickness_sound(self):
        if not self.enabled:
            return
        for _ in range(8):
            music.pitch(random.randint(100, 500), duration=random.randint(30, 100), wait=True)
            sleep(random.randint(20, 80))

    def play_death_sequence(self):
        if not self.enabled:
            return

        # Glitching
        for _ in range(10):
            music.pitch(random.randint(200, 800), duration=random.randint(50, 150), wait=True)
            sleep(random.randint(10, 50))

        sleep(200)

        # Pitch drop
        self._play_pitch_drop(440, 55, 3000)
        sleep(300)

        # Thud
        music.pitch(30, duration=200, wait=True)

    def _play_pitch_drop(self, start_freq, end_freq, duration):
        steps = 30
        step_duration = duration // steps
        freq_step = (start_freq - end_freq) / steps
        for i in range(steps):
            freq = int(start_freq - (freq_step * i))
            music.pitch(freq, duration=step_duration, wait=True)

    def play_startup_sound(self):
        if not self.enabled:
            return
        self._play_tone_sweep(50, 400, 10, 1000)


# ============================================================================
# DISPLAY SYSTEM
# ============================================================================

class DisplaySystem:
    """Manages LED matrix animations"""

    IDLE_FRAME_1 = Image("09990:90909:99999:90909:09090")
    IDLE_FRAME_2 = Image("09990:99999:90909:99999:09090")
    HUNGRY_FRAME_1 = Image("90009:09990:99999:09990:90009")
    HUNGRY_FRAME_2 = Image("09090:90909:99999:90909:09090")
    HUNGRY_FRAME_3 = Image("00900:09990:99999:09990:00900")
    HAPPY_FRAME = Image("09090:09090:00000:90009:09990")
    SICK_FRAME_1 = Image("90909:09090:90909:09090:90909")
    SICK_FRAME_2 = Image("09090:90909:09090:90909:09090")
    WARNING_FRAME = Image("90009:09090:00900:09090:90009")

    def __init__(self):
        self.current_frame = 0
        self.flash_state = False

    def show_idle_animation(self):
        frames = [self.IDLE_FRAME_1, self.IDLE_FRAME_2]
        display.show(frames[self.current_frame % 2])
        self.current_frame += 1

    def show_hungry_animation(self, intensity):
        if intensity == 2:
            if self.flash_state:
                display.show(self.HUNGRY_FRAME_3)
            else:
                display.show(self.WARNING_FRAME)
            self.flash_state = not self.flash_state
        elif intensity == 1:
            frames = [self.HUNGRY_FRAME_1, self.HUNGRY_FRAME_2, self.HUNGRY_FRAME_3]
            display.show(frames[self.current_frame % 3])
            self.current_frame += 1
        else:
            frames = [self.IDLE_FRAME_1, self.HUNGRY_FRAME_1]
            display.show(frames[self.current_frame % 2])
            self.current_frame += 1

    def show_happy_animation(self):
        display.show(self.HAPPY_FRAME)

    def show_sick_animation(self):
        frames = [self.SICK_FRAME_1, self.SICK_FRAME_2]
        display.show(frames[self.current_frame % 2])
        self.current_frame += 1

    def show_death_sequence(self):
        # Flickering
        for _ in range(10):
            if random.randint(0, 1):
                display.show(Image.SKULL)
            else:
                display.clear()
            sleep(100)

        # Fade out
        for _ in range(3):
            display.show(Image("00000:00000:00900:00000:00000"))
            sleep(300)
            display.clear()
            sleep(300)

    def show_startup_sequence(self):
        display.show(Image.ALL_CLOCKS, delay=100)
        display.show(self.IDLE_FRAME_1)

    def show_feed_feedback(self):
        for brightness in [3, 6, 9, 6, 3]:
            img_str = str(brightness) * 25
            formatted = ":".join([img_str[i:i+5] for i in range(0, 25, 5)])
            display.show(Image(formatted))
            sleep(50)
        self.show_happy_animation()

    def show_play_feedback(self):
        display.show(Image.ALL_ARROWS, delay=100)
        self.show_happy_animation()


# ============================================================================
# INPUT HANDLER
# ============================================================================

class InputHandler:
    """Handles button and accelerometer input with debouncing"""

    BUTTON_DEBOUNCE = 50
    BUTTON_COOLDOWN = 500
    SHAKE_THRESHOLD = 1500
    SHAKE_COOLDOWN = 1000
    LONG_PRESS_DURATION = 2000

    def __init__(self):
        self.button_a_pressed = False
        self.button_b_pressed = False
        self.last_button_a_time = 0
        self.last_button_b_time = 0
        self.last_action_time = 0
        self.last_shake_time = 0
        self.long_press_start = 0
        self.long_press_triggered = False

    def update(self):
        current_time = running_time()
        result = {
            'button_a': False,
            'button_b': False,
            'combo': False,
            'shake': False,
            'long_press': False
        }

        if current_time - self.last_action_time < self.BUTTON_COOLDOWN:
            return result

        # Button handling
        button_a_state = button_a.is_pressed()
        button_b_state = button_b.is_pressed()

        if button_a_state and not self.button_a_pressed:
            if current_time - self.last_button_a_time > self.BUTTON_DEBOUNCE:
                self.button_a_pressed = True
                self.last_button_a_time = current_time
        elif not button_a_state:
            self.button_a_pressed = False

        if button_b_state and not self.button_b_pressed:
            if current_time - self.last_button_b_time > self.BUTTON_DEBOUNCE:
                self.button_b_pressed = True
                self.last_button_b_time = current_time
        elif not button_b_state:
            self.button_b_pressed = False

        # Combo detection
        if self.button_a_pressed and self.button_b_pressed:
            result['combo'] = True
            self.last_action_time = current_time
        else:
            if self.button_a_pressed and current_time - self.last_button_a_time < 100:
                result['button_a'] = True
                self.last_action_time = current_time
            if self.button_b_pressed and current_time - self.last_button_b_time < 100:
                result['button_b'] = True
                self.last_action_time = current_time

        # Long press detection
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
        if current_time - self.last_shake_time > self.SHAKE_COOLDOWN:
            x = accelerometer.get_x()
            y = accelerometer.get_y()
            z = accelerometer.get_z()
            magnitude = (x*x + y*y + z*z) ** 0.5
            if magnitude > self.SHAKE_THRESHOLD:
                result['shake'] = True
                self.last_shake_time = current_time
                self.last_action_time = current_time

        return result


# ============================================================================
# MAIN GAME
# ============================================================================

class VirtualPetGame:
    """Main game controller"""

    UPDATE_INTERVAL = 100
    ANIMATION_INTERVAL = 500
    AUDIO_INTERVAL = 3000

    def __init__(self, audio_enabled=True):
        self.pet = VirtualPet()
        self.display_sys = DisplaySystem()
        self.audio_sys = AudioSystem(enabled=audio_enabled)
        self.input_handler = InputHandler()
        self.last_update_time = 0
        self.last_animation_time = 0
        self.last_audio_time = 0
        self.running = True

    def start(self):
        self.display_sys.show_startup_sequence()
        self.audio_sys.play_startup_sound()
        sleep(500)
        display.scroll("HUGGY", delay=150)

        self.last_update_time = running_time()
        self.last_animation_time = running_time()
        self.last_audio_time = running_time()

        self.run_game_loop()

    def run_game_loop(self):
        while self.running:
            current_time = running_time()

            if current_time - self.last_update_time >= self.UPDATE_INTERVAL:
                previous_state = self.pet.state
                self.pet.update(current_time)

                if previous_state != self.pet.state:
                    self.pet.state_entry_time = current_time
                    if self.pet.state == PetState.DEATH:
                        self.on_death()

                self.last_update_time = current_time

            self.handle_input(current_time)

            if current_time - self.last_animation_time >= self.ANIMATION_INTERVAL:
                self.update_display()
                self.last_animation_time = current_time

            if current_time - self.last_audio_time >= self.AUDIO_INTERVAL:
                self.play_ambient_audio()
                self.last_audio_time = current_time

            sleep(10)

    def handle_input(self, current_time):
        inputs = self.input_handler.update()

        if inputs['long_press']:
            self.trigger_reset()
            return

        if inputs['combo']:
            if self.pet.emergency_care(current_time):
                self.audio_sys.play_satisfaction_sound()
                self.display_sys.show_feed_feedback()
        elif inputs['button_a']:
            if self.pet.feed(current_time):
                self.audio_sys.play_satisfaction_sound()
                self.display_sys.show_feed_feedback()
        elif inputs['button_b'] or inputs['shake']:
            if self.pet.play(current_time):
                self.audio_sys.play_satisfaction_sound()
                self.display_sys.show_play_feedback()

    def update_display(self):
        state = self.pet.state

        if state == PetState.IDLE:
            self.display_sys.show_idle_animation()
        elif state == PetState.HUNGRY:
            intensity = 2 if self.pet.hunger > 80 else (1 if self.pet.hunger > 50 else 0)
            self.display_sys.show_hungry_animation(intensity)
        elif state == PetState.HAPPY:
            self.display_sys.show_happy_animation()
        elif state == PetState.SICK:
            self.display_sys.show_sick_animation()

    def play_ambient_audio(self):
        if not self.pet.is_alive:
            return

        state = self.pet.state
        if state == PetState.IDLE:
            self.audio_sys.play_idle_breathing()
        elif state == PetState.HUNGRY:
            intensity = 2 if self.pet.hunger > 80 else (1 if self.pet.hunger > 50 else 0)
            self.audio_sys.play_hunger_alert(intensity)
        elif state == PetState.SICK:
            self.audio_sys.play_sickness_sound()

    def on_death(self):
        self.audio_sys.play_death_sequence()
        self.display_sys.show_death_sequence()
        display.scroll(f"AGE:{self.pet.age}s", delay=100)
        display.show(Image.SKULL)
        self.wait_for_reset()

    def wait_for_reset(self):
        while True:
            if button_a.is_pressed() and button_b.is_pressed():
                sleep(2000)
                if button_a.is_pressed() and button_b.is_pressed():
                    self.trigger_reset()
                    return
            sleep(100)

    def trigger_reset(self):
        display.scroll("RESET", delay=100)
        self.pet.reset()
        self.start()


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Entry point - Start the game!"""
    try:
        game = VirtualPetGame(audio_enabled=True)
        game.start()
    except Exception as e:
        display.clear()
        display.scroll(f"ERROR", delay=100)


# Start the game!
main()
