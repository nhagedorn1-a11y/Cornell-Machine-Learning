"""
Freddy Fazbear Virtual Pet - FNAF Edition
Animatronic horror-themed Tamagotchi for BBC micro:bit V2

You're the night guard at Freddy Fazbear's Pizza...
Keep the animatronic bear satisfied or face the consequences!

Controls:
- Button A: Feed power (pizza)
- Button B: Play music box
- Shake: Distract with flashlight
- A+B (hold 2s): System reboot

Copy this ENTIRE file and paste it into https://python.microbit.org/
Then click "Download" to flash it to your micro:bit!

Inspired by Five Nights at Freddy's
Version: 1.0.0
"""
from microbit import *
import random
import music


# ============================================================================
# ANIMATRONIC STATE MANAGEMENT
# ============================================================================

class AnimatronicState:
    """Animatronic behavior states"""
    IDLE = 0          # Dormant in show stage
    AGGRESSIVE = 1    # Moving toward office
    ATTACKING = 2     # Malfunctioning/hostile
    ENTERTAINED = 3   # Satisfied with music/pizza
    SHUTDOWN = 4      # Power failure/jumpscare


class FreddyFazbear:
    """Freddy Fazbear animatronic logic - FNAF virtual pet"""

    POWER_DRAIN_RATE = 1.8      # Power drains faster
    MUSIC_DECAY_RATE = 1.2      # Music box winds down
    AGGRESSION_DECAY = 0.6      # Becomes more aggressive

    POWER_THRESHOLD = 30000     # 30s until power critical
    SHUTDOWN_TIMER = 90000      # 90s without power = jumpscare
    ENTERTAINED_DURATION = 6000 # 6s of entertainment

    def __init__(self):
        self.state = AnimatronicState.IDLE
        self.previous_state = None

        # Core stats (0-100 scale)
        self.power = 60           # Building power level
        self.music_box = 70       # Music box wind level
        self.aggression = 20      # How hostile Freddy is
        self.night = 0            # Survival time in "nights" (seconds)

        # Timers
        self.last_power_time = 0
        self.last_music_time = 0
        self.state_entry_time = 0

        # Status flags
        self.is_active = True
        self.is_critical = False
        self.interaction_count = 0
        self.jumpscares = 0

    def update(self, current_time):
        if not self.is_active:
            return

        time_since_power = current_time - self.last_power_time
        time_since_music = current_time - self.last_music_time
        time_in_state = current_time - self.state_entry_time
        self.night = current_time // 1000

        # Power drains over time
        power_drain = (time_since_power / 1000) * self.POWER_DRAIN_RATE
        self.power = max(0, self.power - power_drain * 0.01)

        # Music box winds down
        music_drain = (time_since_music / 1000) * self.MUSIC_DECAY_RATE
        self.music_box = max(0, self.music_box - music_drain * 0.01)

        # Aggression increases when neglected
        if self.power < 40 or self.music_box < 30:
            self.aggression = min(100, self.aggression + self.AGGRESSION_DECAY * 0.1)
        else:
            self.aggression = max(0, self.aggression - 0.05)

        # State transitions
        self._evaluate_state(time_since_power, time_since_music, time_in_state)

    def _evaluate_state(self, time_since_power, time_since_music, time_in_state):
        # SHUTDOWN (Jumpscare) - highest priority
        if self.power <= 0 or time_since_power > self.SHUTDOWN_TIMER:
            self._transition_to_state(AnimatronicState.SHUTDOWN)
            self.is_active = False
            return

        # ATTACKING - critical aggression or failures
        if self.aggression > 80 or (self.power < 20 and self.music_box < 20):
            self._transition_to_state(AnimatronicState.ATTACKING)
            self.is_critical = True
            return

        # ENTERTAINED timeout
        if self.state == AnimatronicState.ENTERTAINED and time_in_state > self.ENTERTAINED_DURATION:
            self._transition_to_state(AnimatronicState.IDLE)
            return

        # AGGRESSIVE when power/music low
        if self.power < 40 or self.music_box < 40:
            self._transition_to_state(AnimatronicState.AGGRESSIVE)
            self.is_critical = self.aggression > 60
            return

        # IDLE when systems are good
        if self.state != AnimatronicState.ENTERTAINED and self.power > 50 and self.music_box > 50:
            self._transition_to_state(AnimatronicState.IDLE)
            self.is_critical = False

    def _transition_to_state(self, new_state):
        if self.state != new_state:
            self.previous_state = self.state
            self.state = new_state
            self.state_entry_time = 0

    def feed_power(self, current_time):
        """Give pizza to restore power"""
        if not self.is_active or self.state == AnimatronicState.SHUTDOWN:
            return False

        self.power = min(100, self.power + 35)
        self.aggression = max(0, self.aggression - 15)
        self.last_power_time = current_time
        self.interaction_count += 1
        self._transition_to_state(AnimatronicState.ENTERTAINED)
        return True

    def play_music(self, current_time):
        """Wind music box to calm Freddy"""
        if not self.is_active or self.state == AnimatronicState.SHUTDOWN:
            return False

        self.music_box = min(100, self.music_box + 30)
        self.aggression = max(0, self.aggression - 10)
        self.power = max(0, self.power - 5)  # Using music drains power
        self.last_music_time = current_time
        self.interaction_count += 1
        self._transition_to_state(AnimatronicState.ENTERTAINED)
        return True

    def use_flashlight(self, current_time):
        """Distract with flashlight (shake action)"""
        if not self.is_active or self.state == AnimatronicState.SHUTDOWN:
            return False

        self.aggression = max(0, self.aggression - 20)
        self.power = max(0, self.power - 10)  # Flashlight drains power
        self.music_box = min(100, self.music_box + 10)
        self.last_music_time = current_time
        self.interaction_count += 1
        self._transition_to_state(AnimatronicState.ENTERTAINED)
        return True

    def emergency_reboot(self, current_time):
        """Emergency system reboot (A+B combo)"""
        if not self.is_active or self.state == AnimatronicState.SHUTDOWN:
            return False

        self.power = min(100, self.power + 40)
        self.music_box = min(100, self.music_box + 35)
        self.aggression = max(0, self.aggression - 30)
        self.last_power_time = current_time
        self.last_music_time = current_time
        self.interaction_count += 1
        self.is_critical = False
        self._transition_to_state(AnimatronicState.ENTERTAINED)
        return True

    def reset(self):
        self.__init__()


# ============================================================================
# AUDIO SYSTEM - FNAF THEMED
# ============================================================================

class FNAFAudioSystem:
    """Five Nights at Freddy's themed audio"""

    NOTES = {
        'C2': 65, 'D2': 73, 'E2': 82, 'F2': 87, 'G2': 98, 'A2': 110,
        'C3': 131, 'D3': 147, 'E3': 165, 'F3': 175, 'G3': 196, 'A3': 220,
        'C4': 262, 'D4': 294, 'E4': 330, 'F4': 349, 'G4': 392, 'A4': 440, 'B4': 494,
        'C5': 523, 'D5': 587, 'E5': 659, 'F5': 698, 'G5': 784,
    }

    def __init__(self, enabled=True):
        self.enabled = enabled

    def play_idle_mechanical(self):
        """Mechanical servo sounds - idle state"""
        if not self.enabled:
            return

        # Mechanical whirring
        for _ in range(3):
            music.pitch(self.NOTES['C2'] + random.randint(-10, 10), duration=150, wait=True)
            sleep(random.randint(100, 200))

    def play_aggression_alert(self, intensity):
        """Footsteps and movement sounds"""
        if not self.enabled:
            return

        if intensity == 0:
            # Mild - distant footsteps
            for _ in range(3):
                music.pitch(self.NOTES['G2'], duration=80, wait=True)
                sleep(400)

        elif intensity == 1:
            # Moderate - closer footsteps, faster
            for _ in range(4):
                music.pitch(self.NOTES['G2'], duration=60, wait=True)
                sleep(250)

        else:
            # Critical - rapid metallic clanging
            for _ in range(6):
                freq = random.choice([self.NOTES['E3'], self.NOTES['G3'], self.NOTES['C4']])
                music.pitch(freq, duration=100, wait=True)
                sleep(100)

    def play_music_box(self):
        """Classic FNAF music box melody"""
        if not self.enabled:
            return

        # Simplified music box tune
        melody = [
            (self.NOTES['E5'], 200),
            (self.NOTES['D5'], 200),
            (self.NOTES['C5'], 200),
            (self.NOTES['A4'], 300),
            (self.NOTES['E5'], 200),
        ]

        for freq, dur in melody:
            music.pitch(freq, duration=dur, wait=True)
            sleep(50)

    def play_satisfaction_chime(self):
        """Freddy is satisfied - arcade-like chime"""
        if not self.enabled:
            return

        melody = [
            (self.NOTES['C5'], 100),
            (self.NOTES['E5'], 100),
            (self.NOTES['G5'], 150),
        ]

        for freq, dur in melody:
            music.pitch(freq, duration=dur, wait=True)

    def play_malfunction_sound(self):
        """Glitchy animatronic malfunction"""
        if not self.enabled:
            return

        for _ in range(10):
            freq = random.randint(80, 600)
            music.pitch(freq, duration=random.randint(40, 120), wait=True)
            sleep(random.randint(10, 60))

    def play_jumpscare_scream(self):
        """FNAF jumpscare audio sequence"""
        if not self.enabled:
            return

        # Rapid metallic screeching
        for _ in range(15):
            freq = random.randint(400, 1200)
            music.pitch(freq, duration=random.randint(40, 100), wait=True)

        sleep(200)

        # Deep mechanical roar (pitch drop)
        self._play_pitch_drop(800, 60, 2000)

    def _play_pitch_drop(self, start_freq, end_freq, duration):
        steps = 25
        step_duration = duration // steps
        freq_step = (start_freq - end_freq) / steps

        for i in range(steps):
            freq = int(start_freq - (freq_step * i))
            music.pitch(freq, duration=step_duration, wait=True)

    def play_power_out_alert(self):
        """Power running out warning"""
        if not self.enabled:
            return

        for _ in range(3):
            music.pitch(self.NOTES['A4'], duration=150, wait=True)
            music.pitch(self.NOTES['E4'], duration=150, wait=True)

    def play_startup_jingle(self):
        """Freddy Fazbear's Pizza startup"""
        if not self.enabled:
            return

        # Cheerful but slightly off-key jingle
        melody = [
            (self.NOTES['C4'], 150),
            (self.NOTES['E4'], 150),
            (self.NOTES['G4'], 150),
            (self.NOTES['C5'], 300),
        ]

        for freq, dur in melody:
            music.pitch(freq, duration=dur, wait=True)
            sleep(30)


# ============================================================================
# DISPLAY SYSTEM - ANIMATRONIC BEAR
# ============================================================================

class FreddyDisplaySystem:
    """Freddy Fazbear LED animations"""

    # Freddy's face - idle (bear head with bow tie)
    IDLE_FRAME_1 = Image("09090:99999:09990:99999:09990")
    IDLE_FRAME_2 = Image("09090:99999:09990:99999:99099")

    # Aggressive - eyes glowing
    AGGRESSIVE_FRAME_1 = Image("09090:09990:99999:99999:09990")
    AGGRESSIVE_FRAME_2 = Image("99099:09990:99999:09990:09090")
    AGGRESSIVE_FRAME_3 = Image("99999:99999:09990:99999:99999")

    # Entertained - happy bear
    ENTERTAINED_FRAME = Image("09090:09090:09990:90009:09990")

    # Malfunctioning - corrupted
    ATTACKING_FRAME_1 = Image("90909:09090:99999:09090:90909")
    ATTACKING_FRAME_2 = Image("09090:90909:09090:90909:09090")

    # Warning
    WARNING_FRAME = Image("99999:00000:99999:00000:99999")

    def __init__(self):
        self.current_frame = 0
        self.flash_state = False

    def show_idle_animation(self):
        """Freddy waiting on stage"""
        frames = [self.IDLE_FRAME_1, self.IDLE_FRAME_2]
        display.show(frames[self.current_frame % 2])
        self.current_frame += 1

    def show_aggressive_animation(self, intensity):
        """Freddy moving toward you"""
        if intensity == 2:
            # Critical - rapid flashing eyes
            if self.flash_state:
                display.show(self.AGGRESSIVE_FRAME_3)
            else:
                display.show(self.WARNING_FRAME)
            self.flash_state = not self.flash_state

        elif intensity == 1:
            # Moderate - approaching
            frames = [self.AGGRESSIVE_FRAME_1, self.AGGRESSIVE_FRAME_2, self.AGGRESSIVE_FRAME_3]
            display.show(frames[self.current_frame % 3])
            self.current_frame += 1

        else:
            # Mild - slow movement
            frames = [self.IDLE_FRAME_1, self.AGGRESSIVE_FRAME_1]
            display.show(frames[self.current_frame % 2])
            self.current_frame += 1

    def show_entertained_animation(self):
        """Freddy is satisfied"""
        display.show(self.ENTERTAINED_FRAME)

    def show_attacking_animation(self):
        """Freddy malfunctioning"""
        frames = [self.ATTACKING_FRAME_1, self.ATTACKING_FRAME_2]
        display.show(frames[self.current_frame % 2])
        self.current_frame += 1

    def show_jumpscare_sequence(self):
        """FNAF-style jumpscare"""
        # Rapid approach
        for _ in range(8):
            if random.randint(0, 1):
                display.show(self.AGGRESSIVE_FRAME_3)
            else:
                display.clear()
            sleep(80)

        # Full screen flash
        for _ in range(5):
            display.show(Image("99999:99999:99999:99999:99999"))
            sleep(100)
            display.clear()
            sleep(100)

        # Freddy's face close-up
        display.show(Image("99999:09990:99999:09990:09990"))
        sleep(500)

    def show_startup_sequence(self):
        """Animatronic powering on"""
        # Eyes light up one by one
        display.show(Image("00000:09000:00000:00000:00000"))
        sleep(200)
        display.show(Image("00000:09090:00000:00000:00000"))
        sleep(200)
        display.show(self.IDLE_FRAME_1)

    def show_power_feedback(self):
        """Pizza given - power restored"""
        # Pizza slice animation
        display.show(Image("00000:00990:09900:99000:00000"))
        sleep(200)
        self.show_entertained_animation()

    def show_music_feedback(self):
        """Music box wound"""
        # Musical note animation
        display.show(Image("00900:00990:00900:09000:99000"))
        sleep(200)
        self.show_entertained_animation()

    def show_flashlight_feedback(self):
        """Flashlight used"""
        # Flash of light
        for brightness in [9, 6, 3, 6, 9]:
            img_str = str(brightness) * 25
            formatted = ":".join([img_str[i:i+5] for i in range(0, 25, 5)])
            display.show(Image(formatted))
            sleep(40)


# ============================================================================
# INPUT HANDLER
# ============================================================================

class InputHandler:
    """Input handling with debouncing"""

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

class FreddyFazbearGame:
    """Five Nights at Freddy's virtual pet game"""

    UPDATE_INTERVAL = 100
    ANIMATION_INTERVAL = 400
    AUDIO_INTERVAL = 4000

    def __init__(self, audio_enabled=True):
        self.freddy = FreddyFazbear()
        self.display_sys = FreddyDisplaySystem()
        self.audio_sys = FNAFAudioSystem(enabled=audio_enabled)
        self.input_handler = InputHandler()
        self.last_update_time = 0
        self.last_animation_time = 0
        self.last_audio_time = 0
        self.running = True

    def start(self):
        """Start the night shift"""
        self.display_sys.show_startup_sequence()
        self.audio_sys.play_startup_jingle()
        sleep(500)

        display.scroll("FREDDY", delay=120)
        sleep(200)
        display.scroll("NIGHT 1", delay=120)

        self.last_update_time = running_time()
        self.last_animation_time = running_time()
        self.last_audio_time = running_time()

        self.run_game_loop()

    def run_game_loop(self):
        """Main game loop"""
        while self.running:
            current_time = running_time()

            if current_time - self.last_update_time >= self.UPDATE_INTERVAL:
                previous_state = self.freddy.state
                self.freddy.update(current_time)

                if previous_state != self.freddy.state:
                    self.freddy.state_entry_time = current_time
                    if self.freddy.state == AnimatronicState.SHUTDOWN:
                        self.on_jumpscare()

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
        """Process player inputs"""
        inputs = self.input_handler.update()

        if inputs['long_press']:
            self.trigger_reboot()
            return

        if inputs['combo']:
            if self.freddy.emergency_reboot(current_time):
                self.audio_sys.play_power_out_alert()
                self.audio_sys.play_satisfaction_chime()
                self.display_sys.show_power_feedback()

        elif inputs['button_a']:
            if self.freddy.feed_power(current_time):
                self.audio_sys.play_satisfaction_chime()
                self.display_sys.show_power_feedback()

        elif inputs['button_b']:
            if self.freddy.play_music(current_time):
                self.audio_sys.play_music_box()
                self.display_sys.show_music_feedback()

        elif inputs['shake']:
            if self.freddy.use_flashlight(current_time):
                self.display_sys.show_flashlight_feedback()

    def update_display(self):
        """Update LED display"""
        state = self.freddy.state

        if state == AnimatronicState.IDLE:
            self.display_sys.show_idle_animation()

        elif state == AnimatronicState.AGGRESSIVE:
            intensity = 2 if self.freddy.aggression > 70 else (1 if self.freddy.aggression > 40 else 0)
            self.display_sys.show_aggressive_animation(intensity)

        elif state == AnimatronicState.ENTERTAINED:
            self.display_sys.show_entertained_animation()

        elif state == AnimatronicState.ATTACKING:
            self.display_sys.show_attacking_animation()

    def play_ambient_audio(self):
        """Play ambient sounds"""
        if not self.freddy.is_active:
            return

        state = self.freddy.state

        if state == AnimatronicState.IDLE:
            self.audio_sys.play_idle_mechanical()

        elif state == AnimatronicState.AGGRESSIVE:
            intensity = 2 if self.freddy.aggression > 70 else (1 if self.freddy.aggression > 40 else 0)
            self.audio_sys.play_aggression_alert(intensity)

        elif state == AnimatronicState.ATTACKING:
            self.audio_sys.play_malfunction_sound()

    def on_jumpscare(self):
        """Freddy jumpscares you - game over"""
        self.freddy.jumpscares += 1
        self.audio_sys.play_jumpscare_scream()
        self.display_sys.show_jumpscare_sequence()

        sleep(500)
        display.scroll(f"NIGHT {self.freddy.night}s", delay=100)
        sleep(300)
        display.show(Image.SKULL)

        self.wait_for_reboot()

    def wait_for_reboot(self):
        """Wait for system reboot"""
        while True:
            if button_a.is_pressed() and button_b.is_pressed():
                sleep(2000)
                if button_a.is_pressed() and button_b.is_pressed():
                    self.trigger_reboot()
                    return
            sleep(100)

    def trigger_reboot(self):
        """Reboot the system"""
        display.scroll("REBOOT", delay=100)
        self.freddy.reset()
        self.start()


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def main():
    """Welcome to Freddy Fazbear's Pizza!"""
    try:
        game = FreddyFazbearGame(audio_enabled=True)
        game.start()
    except Exception as e:
        display.clear()
        display.scroll("ERROR", delay=100)


# Start your night shift!
main()
