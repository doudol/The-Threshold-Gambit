# agent.py
import random
import logging

# Configure logging for this module if run standalone, or rely on root config
log = logging.getLogger(__name__)

class SimpleAgent:
    """
    Represents an agent that experiences punishments and rewards.
    It decides whether to continue or 'give up' based on its recent experience.
    """
    def __init__(self, give_up_threshold: int, name: str = "Agent"):
        """
        Initializes the agent.

        Args:
            give_up_threshold: The number of consecutive punishments before giving up.
            name: A name for the agent (optional).
        """
        if give_up_threshold <= 0:
            raise ValueError("give_up_threshold must be positive.")

        self.name = name
        self.give_up_threshold = give_up_threshold
        self.consecutive_punishments = 0
        self.total_punishments_received = 0
        self.total_rewards_received = 0
        self.steps_lived = 0
        self.decision_log = [] # Log agent decisions within a generation

    def reset(self):
        """Resets the agent's state for a new generation."""
        self.consecutive_punishments = 0
        self.total_punishments_received = 0
        self.total_rewards_received = 0
        self.steps_lived = 0
        self.decision_log = []

    def record_step(self, is_reward: bool):
        """
        Updates the agent's internal state based on the outcome of a step.

        Args:
            is_reward: True if a reward was received, False if a punishment.
        """
        self.steps_lived += 1
        if is_reward:
            self.total_rewards_received += 1
            self.consecutive_punishments = 0 # Reward resets punishment streak
            self.decision_log.append(f"Step {self.steps_lived}: REWARD received. Resetting consecutive punishments.")
            log.log(5, f"Agent {self.name}: Step {self.steps_lived} - REWARD. Consecutive punishments reset.") # TRACE level log
        else:
            self.total_punishments_received += 1
            self.consecutive_punishments += 1
            self.decision_log.append(f"Step {self.steps_lived}: PUNISHMENT received. Consecutive: {self.consecutive_punishments}.")
            log.log(5, f"Agent {self.name}: Step {self.steps_lived} - PUNISHMENT. Consecutive: {self.consecutive_punishments}.") # TRACE level log

    def decide_to_continue(self) -> bool:
        """
        Agent decides whether to continue to the next step or give up.
        Decision based on consecutive punishments vs. threshold.

        Returns:
            True to continue, False to give up.
        """
        if self.consecutive_punishments >= self.give_up_threshold:
            decision = False
            reason = f"Reached give_up_threshold ({self.give_up_threshold}) with {self.consecutive_punishments} consecutive punishments."
            self.decision_log.append(f"Step {self.steps_lived}: DECISION: Give Up. Reason: {reason}")
            log.log(5, f"Agent {self.name}: Step {self.steps_lived} - DECISION: Give Up ({reason}).") # TRACE level log
        else:
            decision = True
            # No explicit log for 'continue' to reduce verbosity, but decision_log implies it if no 'Give Up' entry follows.
            log.log(5, f"Agent {self.name}: Step {self.steps_lived} - DECISION: Continue (Consecutive: {self.consecutive_punishments} < Threshold: {self.give_up_threshold}).") # TRACE level log
        return decision

    def get_generation_summary(self):
        """Returns a summary of the agent's life in the current generation."""
        return {
            "lifespan": self.steps_lived,
            "total_rewards": self.total_rewards_received,
            "total_punishments": self.total_punishments_received,
            "final_consecutive_punishments": self.consecutive_punishments,
            "decision_log": self.decision_log # Include the detailed log for potential analysis
        }


class LearningAgent(SimpleAgent):
     """
     An agent that adjusts its give_up_threshold based on past experience
     (e.g., historical average lifespan). VERY basic heuristic learning.
     """
     def __init__(self, initial_threshold: int, learning_rate: float = 0.1, name: str = "LearningAgent"):
         """
         Initializes the learning agent.

         Args:
             initial_threshold: The starting threshold value.
             learning_rate: How strongly to adjust towards the historical average (0 to 1).
             name: A name for the agent.
         """
         super().__init__(initial_threshold, name)
         self.learning_rate = learning_rate
         # Initialize history; use initial threshold as a starting point for the average
         self.historical_lifespans = [initial_threshold]
         log.info(f"LearningAgent '{self.name}' initialized. Initial threshold: {self.give_up_threshold}, LR: {self.learning_rate}")

     def learn_from_history(self, current_lifespan: int):
         """ Updates threshold based on historical lifespans including the latest one. """
         self.historical_lifespans.append(current_lifespan)

         # Calculate historical average lifespan
         # Using simple average here; could use EWMA or windowed average for different dynamics
         if self.historical_lifespans:
             current_avg = sum(self.historical_lifespans) / len(self.historical_lifespans)
         else: # Should not happen if initialized correctly
             current_avg = self.give_up_threshold # Fallback

         # Target threshold is the historical average, but must be at least 1
         target_threshold = max(1, int(round(current_avg)))

         # Update rule: Interpolate between current threshold and target threshold
         new_threshold = int(round(
             self.give_up_threshold * (1 - self.learning_rate) + target_threshold * self.learning_rate
         ))

         # Ensure threshold is always at least 1
         self.give_up_threshold = max(1, new_threshold)

         log.info(f"Agent '{self.name}': Learning update. Avg lifespan (hist): {current_avg:.2f}. Target threshold: {target_threshold}. New threshold: {self.give_up_threshold}")


     def reset(self):
        """
        Resets per-generation counters but importantly KEEPS the learned threshold
        and the history used for learning.
        """
        # Keep the learned threshold and history across generations
        # Reset only the per-generation counters
        self.consecutive_punishments = 0
        self.total_punishments_received = 0
        self.total_rewards_received = 0
        self.steps_lived = 0
        self.decision_log = []
        # DO NOT reset self.give_up_threshold or self.historical_lifespans here
        log.debug(f"LearningAgent '{self.name}' reset for new generation. Current threshold: {self.give_up_threshold}")
