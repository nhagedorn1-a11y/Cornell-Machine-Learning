"""
Virtual Pet State Management System
Horror-themed Huggy Wuggy-inspired creature with FSM
"""
from microbit import sleep
import random


class PetState:
    """Enumeration of possible pet states"""
    IDLE = 0
    HUNGRY = 1
    SICK = 2
    HAPPY = 3
    DEATH = 4


class VirtualPet:
    """
    Core virtual pet logic with finite state machine.
    Manages creature state, needs, and behavioral patterns.
    """

    # State durations and thresholds (in milliseconds)
    HUNGER_THRESHOLD = 30000      # 30 seconds to get hungry (testing)
    CRITICAL_THRESHOLD = 60000     # 60 seconds to critical state
    HAPPY_DURATION = 5000          # 5 seconds of happiness after feeding
    DEATH_TIMER = 90000            # 90 seconds of neglect = death

    # Stat decay rates (per second)
    HUNGER_DECAY_RATE = 1.5
    HAPPINESS_DECAY_RATE = 0.8
    HEALTH_DECAY_RATE = 0.5

    def __init__(self):
        """Initialize the virtual pet with default stats"""
        self.state = PetState.IDLE
        self.previous_state = None

        # Core stats (0-100 scale)
        self.hunger = 50          # Higher = more hungry
        self.happiness = 70       # Higher = happier
        self.health = 100         # Higher = healthier
        self.age = 0              # Age in seconds

        # Timers
        self.last_feed_time = 0
        self.last_play_time = 0
        self.state_entry_time = 0
        self.death_timer = 0

        # Behavior flags
        self.is_alive = True
        self.is_critical = False
        self.interaction_count = 0

    def update(self, current_time: int) -> None:
        """
        Update pet state based on elapsed time.
        Call this every game loop iteration.

        Args:
            current_time: Current timestamp in milliseconds
        """
        if not self.is_alive:
            return

        # Calculate time deltas
        time_since_feed = current_time - self.last_feed_time
        time_since_play = current_time - self.last_play_time
        time_in_state = current_time - self.state_entry_time

        # Update age (convert ms to seconds)
        self.age = current_time // 1000

        # Decay stats over time
        self._decay_stats(time_since_feed, time_since_play)

        # Evaluate state transitions
        self._evaluate_state_change(time_since_feed, time_since_play, time_in_state)

    def _decay_stats(self, time_since_feed: int, time_since_play: int) -> None:
        """Apply exponential decay to pet stats"""
        # Hunger increases over time (capped at 100)
        hunger_increase = (time_since_feed / 1000) * self.HUNGER_DECAY_RATE
        self.hunger = min(100, self.hunger + hunger_increase * 0.01)

        # Happiness decreases over time
        happiness_decrease = (time_since_play / 1000) * self.HAPPINESS_DECAY_RATE
        self.happiness = max(0, self.happiness - happiness_decrease * 0.01)

        # Health decreases if hungry or unhappy
        if self.hunger > 70 or self.happiness < 30:
            health_decrease = self.HEALTH_DECAY_RATE * 0.1
            self.health = max(0, self.health - health_decrease)

    def _evaluate_state_change(self, time_since_feed: int,
                                time_since_play: int,
                                time_in_state: int) -> None:
        """Evaluate and transition between states"""

        # Death check - highest priority
        if self.health <= 0 or time_since_feed > self.DEATH_TIMER:
            self._transition_to_state(PetState.DEATH)
            self.is_alive = False
            return

        # Sickness check
        if self.health < 30 or (self.hunger > 80 and self.happiness < 20):
            self._transition_to_state(PetState.SICK)
            return

        # Happy state timeout
        if self.state == PetState.HAPPY and time_in_state > self.HAPPY_DURATION:
            self._transition_to_state(PetState.IDLE)
            return

        # Hunger escalation
        if self.hunger > 70:
            self._transition_to_state(PetState.HUNGRY)
            self.is_critical = self.hunger > 85
            return

        # Default to idle if stats are good
        if self.state != PetState.HAPPY and self.hunger < 50 and self.happiness > 40:
            self._transition_to_state(PetState.IDLE)

    def _transition_to_state(self, new_state: int) -> None:
        """Handle state transitions with cleanup"""
        if self.state != new_state:
            self.previous_state = self.state
            self.state = new_state
            self.state_entry_time = 0  # Will be set by main loop

    def feed(self, current_time: int) -> bool:
        """
        Feed the creature.

        Args:
            current_time: Current timestamp in milliseconds

        Returns:
            True if feeding was successful
        """
        if not self.is_alive or self.state == PetState.DEATH:
            return False

        # Reduce hunger
        self.hunger = max(0, self.hunger - 30)

        # Slight health boost if was hungry
        if self.hunger > 60:
            self.health = min(100, self.health + 10)

        # Update timers
        self.last_feed_time = current_time
        self.interaction_count += 1

        # Transition to happy state
        self._transition_to_state(PetState.HAPPY)

        return True

    def play(self, current_time: int) -> bool:
        """
        Play with the creature.

        Args:
            current_time: Current timestamp in milliseconds

        Returns:
            True if play was successful
        """
        if not self.is_alive or self.state == PetState.DEATH:
            return False

        # Increase happiness
        self.happiness = min(100, self.happiness + 25)

        # Slight health boost from exercise
        self.health = min(100, self.health + 5)

        # Slight hunger increase from activity
        self.hunger = min(100, self.hunger + 10)

        # Update timers
        self.last_play_time = current_time
        self.interaction_count += 1

        # Transition to happy state
        self._transition_to_state(PetState.HAPPY)

        return True

    def emergency_care(self, current_time: int) -> bool:
        """
        Emergency intervention for critical states.
        Triggered by A+B combo.

        Args:
            current_time: Current timestamp in milliseconds

        Returns:
            True if care was successful
        """
        if not self.is_alive or self.state == PetState.DEATH:
            return False

        # Major stat restoration
        self.hunger = max(0, self.hunger - 40)
        self.happiness = min(100, self.happiness + 30)
        self.health = min(100, self.health + 20)

        # Reset timers
        self.last_feed_time = current_time
        self.last_play_time = current_time
        self.interaction_count += 1

        # Clear critical flag
        self.is_critical = False

        # Transition to happy state
        self._transition_to_state(PetState.HAPPY)

        return True

    def get_state_name(self) -> str:
        """Get human-readable state name"""
        state_names = {
            PetState.IDLE: "IDLE",
            PetState.HUNGRY: "HUNGRY",
            PetState.SICK: "SICK",
            PetState.HAPPY: "HAPPY",
            PetState.DEATH: "DEATH"
        }
        return state_names.get(self.state, "UNKNOWN")

    def get_stats_summary(self) -> dict:
        """Get current pet stats as dictionary"""
        return {
            'state': self.get_state_name(),
            'hunger': int(self.hunger),
            'happiness': int(self.happiness),
            'health': int(self.health),
            'age': self.age,
            'alive': self.is_alive,
            'critical': self.is_critical,
            'interactions': self.interaction_count
        }

    def reset(self) -> None:
        """Factory reset the pet"""
        self.__init__()
