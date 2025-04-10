# environment.py
import random
import logging

log = logging.getLogger(__name__)

class HarshEnvironment:
    """
    Simulates an environment that delivers punishments frequently
    and rewards rarely based on a defined probability.
    """
    def __init__(self, reward_probability: float):
        """
        Initializes the environment.

        Args:
            reward_probability: The probability (0.0 to 1.0) of getting a reward
                                in any given step.
        """
        if not 0.0 <= reward_probability <= 1.0:
            raise ValueError("reward_probability must be between 0.0 and 1.0")
        self.reward_probability = reward_probability
        self.steps_taken = 0
        self.total_rewards_given = 0
        self.total_punishments_given = 0
        log.info(f"HarshEnvironment initialized with reward probability: {self.reward_probability:.5f}")

    def step(self) -> bool:
        """
        Simulates one step in the environment, returning whether a reward was given.

        Returns:
            True if a reward is given, False if a punishment is given.
        """
        self.steps_taken += 1
        is_reward = random.random() < self.reward_probability
        if is_reward:
            self.total_rewards_given += 1
            log.log(5, f"Environment Step {self.steps_taken}: Outcome = REWARD") # TRACE
        else:
            self.total_punishments_given += 1
            log.log(5, f"Environment Step {self.steps_taken}: Outcome = PUNISHMENT") # TRACE
        return is_reward

    def get_stats(self):
        """Returns statistics about the environment's history."""
        actual_rate = (self.total_rewards_given / self.steps_taken) if self.steps_taken > 0 else 0
        stats = {
            "total_steps": self.steps_taken,
            "total_rewards": self.total_rewards_given,
            "total_punishments": self.total_punishments_given,
            "configured_reward_prob": self.reward_probability,
            "actual_reward_rate": actual_rate
        }
        log.debug(f"Environment stats requested: {stats}")
        return stats

    def reset_stats(self):
        """Resets the environment's internal statistics counters."""
        self.steps_taken = 0
        self.total_rewards_given = 0
        self.total_punishments_given = 0
        log.info("Environment statistics reset.")
