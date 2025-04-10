# simulation.py
import logging
import time
import os
from agent import SimpleAgent, LearningAgent
from environment import HarshEnvironment

# Configure logging for simulation module
log = logging.getLogger(__name__)

def run_simulation(config):
    """
    Runs the main simulation loop based on the provided configuration.

    Args:
        config (dict): Dictionary containing simulation parameters like:
                       'num_generations', 'reward_probability', 'agent_type',
                       'agent_initial_threshold', 'learning_rate',
                       'max_steps_per_generation', 'simulation_name'.

    Returns:
        tuple: (list of generation data dictionaries, final environment stats dictionary)
               Returns ([], {}) if simulation fails to start or is interrupted very early.
    """
    sim_name = config.get('simulation_name', 'Unnamed Simulation')
    log.info("="*50)
    log.info(f"Starting Simulation: {sim_name}")
    log.info(f"Parameters: Gens={config['num_generations']}, RewardProb={config['reward_probability']:.5f}, Agent={config['agent_type']}, InitThresh={config['agent_initial_threshold']}, MaxSteps={config['max_steps_per_generation']}")
    if config.get('agent_type') == 'LearningAgent':
        log.info(f"              LearningRate={config.get('learning_rate', 'N/A')}")
    log.info("="*50)

    # --- Initialization ---
    try:
        environment = HarshEnvironment(reward_probability=config['reward_probability'])

        # Initialize Agent based on config type
        agent_type = config.get('agent_type', 'SimpleAgent')
        initial_threshold = config['agent_initial_threshold']

        if agent_type == 'LearningAgent':
            log.info("Initializing LearningAgent.")
            agent = LearningAgent(
                initial_threshold=initial_threshold,
                learning_rate=config.get('learning_rate', 0.05),
                name=f"Learner_Gen0" # Initial name
            )
        else: # Default to SimpleAgent
            log.info("Initializing SimpleAgent.")
            agent = SimpleAgent(
                give_up_threshold=initial_threshold,
                name=f"Simple_Gen0" # Initial name
            )
    except Exception as e:
        log.error(f"Failed to initialize simulation components: {e}", exc_info=True)
        return [], {} # Return empty results on initialization failure

    all_generation_data = []
    start_time = time.time()
    generations_completed = 0

    # --- Main Simulation Loop ---
    try:
        for gen_num in range(1, config['num_generations'] + 1):
            # Reset agent state for the new generation
            # Note: LearningAgent keeps its learned threshold during reset
            agent.reset()
            agent.name = f"{agent_type}_Gen{gen_num}" # Update agent name for logs
            current_threshold = agent.give_up_threshold # Capture threshold for this gen (esp. for LearningAgent)

            log.debug(f"--- Generation {gen_num}/{config['num_generations']} Start (Threshold: {current_threshold}) ---")
            gen_start_time = time.time()
            step_count_this_gen = 0
            generation_ended_normally = False

            # --- Inner Step Loop (Single Generation) ---
            while True:
                step_count_this_gen += 1

                # 1. Environment provides outcome
                is_reward = environment.step()
                # Logging at TRACE level handled by environment/agent methods

                # 2. Agent observes outcome and updates state
                agent.record_step(is_reward)

                # 3. Agent decides whether to continue
                should_continue = agent.decide_to_continue()

                # 4. Check termination conditions for the generation
                if not should_continue:
                    # Generation ends: Agent gave up
                    end_reason = "Agent Threshold Reached"
                    log.debug(f"Generation {gen_num} ended at step {step_count_this_gen}: {end_reason}.")
                    generation_ended_normally = True
                    break # Exit the inner while loop to start next generation

                # Safety break: Check max steps
                if step_count_this_gen >= config['max_steps_per_generation']:
                     end_reason = "Max Steps Reached"
                     log.warning(f"Generation {gen_num} terminated at step {step_count_this_gen}: {end_reason}.")
                     generation_ended_normally = True # Still count as ended for data collection
                     break # Exit the inner while loop

            # --- Post-Generation Processing ---
            gen_end_time = time.time()
            gen_duration = gen_end_time - gen_start_time
            gen_summary = agent.get_generation_summary()

            # Store generation results
            generation_data = {
                "generation": gen_num,
                "summary": gen_summary,
                "end_reason": end_reason,
                "duration_sec": gen_duration,
                "threshold_used": current_threshold # Store the threshold active during this gen
            }
            all_generation_data.append(generation_data)
            generations_completed += 1

            # Optional: Learning agent updates its strategy *after* the generation
            if isinstance(agent, LearningAgent):
                 agent.learn_from_history(gen_summary['lifespan']) # Learn based on the lifespan achieved

            # Progress Logging (controlled frequency)
            log_interval = max(1, config['num_generations'] // 20) # Log roughly 20 times
            if gen_num % log_interval == 0 or gen_num == config['num_generations']:
                log.info(f"Generation {gen_num}/{config['num_generations']} finished. Lifespan: {gen_summary['lifespan']}. Reason: {end_reason}. Time: {gen_duration:.3f}s")


    except KeyboardInterrupt:
        log.warning("Simulation interrupted by user (KeyboardInterrupt). Processing partial results.")
        print("\nSimulation interrupted. Data from completed generations will be saved.")
    except Exception as e:
        log.error(f"An unexpected error occurred during simulation loop: {e}", exc_info=True)
        print(f"\nERROR: Simulation halted due to an unexpected error: {e}")
        # Attempt to return partial data collected so far
    finally:
        # --- Simulation Cleanup & Summary ---
        end_time = time.time()
        total_duration = end_time - start_time
        log.info("="*50)
        log.info(f"Simulation Finished: {sim_name}")
        log.info(f"Total wall clock time: {total_duration:.2f} seconds.")
        log.info(f"Completed {generations_completed} out of {config['num_generations']} specified generations.")

        env_stats = environment.get_stats()
        log.info(f"Final Environment Stats: Total Steps={env_stats['total_steps']}, Actual Reward Rate={env_stats['actual_reward_rate']:.5f}")

        if generations_completed > 0:
             avg_gen_time = total_duration / generations_completed
             log.info(f"Average time per generation: {avg_gen_time:.3f} seconds.")
             lifespans = [g['summary']['lifespan'] for g in all_generation_data]
             log.info(f"Overall Average Lifespan: {sum(lifespans)/len(lifespans):.2f} steps.")
        log.info("="*50)

    return all_generation_data, environment.get_stats()
