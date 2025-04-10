# main.py
import logging
import os
import datetime
import sys
import argparse
from simulation import run_simulation
from reporting import generate_report

# --- Configuration Defaults ---
DEFAULT_CONFIG = {
    "simulation_name": "The_Threshold_Gambit_v1",
    "num_generations": 100,
    "reward_probability": 1.0 / 28.0, # Approx 1 reward every 28 steps
    "agent_initial_threshold": 50,    # Initial consecutive punishments tolerance
    "agent_type": "SimpleAgent",      # Options: "SimpleAgent", "LearningAgent"
    "learning_rate": 0.05,            # Only used if agent_type is "LearningAgent"
    "max_steps_per_generation": 10000,# Safety break
    "output_dir_base": "simulation_results", # Base directory for output folders
    "log_level": "INFO",              # Logging level (TRACE, DEBUG, INFO, WARNING, ERROR)
    "log_to_console": True,
    "log_to_file": True,
    "add_detailed_log_to_pdf": False, # Add verbose generation logs to PDF?
    "max_detailed_logs_in_pdf": 10    # Limit verbose logs in PDF if enabled
}

# --- Logging Setup ---
# Define custom TRACE logging level (lower than DEBUG)
TRACE_LEVEL_NUM = 5
logging.addLevelName(TRACE_LEVEL_NUM, "TRACE")

def trace(self, message, *args, **kws):
    # Add the TRACE level method to the logger class
    if self.isEnabledFor(TRACE_LEVEL_NUM):
        self._log(TRACE_LEVEL_NUM, message, args, **kws)
logging.Logger.trace = trace

def setup_logging(level_str="INFO", log_file="simulation.log", log_to_console=True, log_to_file=True):
    """Sets up root logger configuration for console and file."""
    numeric_level = getattr(logging, level_str.upper(), logging.INFO)
    if level_str.upper() == "TRACE":
        numeric_level = TRACE_LEVEL_NUM

    # Create formatter
    # Example format: 2023-10-27 15:30:00,123 - simulation - INFO - Simulation started.
    log_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Get the root logger
    logger = logging.getLogger()
    logger.setLevel(numeric_level) # Set minimum level for the root logger

    # Remove existing handlers to prevent duplicate messages in interactive environments
    while logger.hasHandlers():
        logger.removeHandler(logger.handlers[0])

    # Console Handler (outputs to stderr by default, use sys.stdout for explicit control)
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout) # Use stdout
        console_handler.setFormatter(log_formatter)
        # Optional: Set a different level for console output if desired
        # console_handler.setLevel(logging.INFO)
        logger.addHandler(console_handler)

    # File Handler
    if log_to_file:
        try:
            # Ensure directory exists before creating file handler
            log_dir = os.path.dirname(log_file)
            if log_dir and not os.path.exists(log_dir):
                 os.makedirs(log_dir, exist_ok=True)
                 print(f"Created log directory: {log_dir}") # User feedback

            # Use 'w' mode to overwrite the log file for each new run
            file_handler = logging.FileHandler(log_file, mode='w', encoding='utf-8')
            file_handler.setFormatter(log_formatter)
            logger.addHandler(file_handler)
            print(f"Logging detailed output to file: {log_file}") # User feedback
        except Exception as e:
             # Fallback: Log error to console if file logging setup fails
             print(f"[ERROR] Could not set up file logging to '{log_file}': {e}", file=sys.stderr)
             logging.error(f"Failed to set up file handler for {log_file}: {e}", exc_info=True)

    # Log initialization confirmation
    log_dest = []
    if log_to_console: log_dest.append("Console")
    if log_to_file: log_dest.append(f"File ({log_file})")
    logger.info(f"Logging initialized. Level: {level_str.upper()}. Output: {', '.join(log_dest)}")


# --- Main Execution ---
if __name__ == "__main__":
    # --- Argument Parsing ---
    parser = argparse.ArgumentParser(description='Run The Threshold Gambit simulation.')
    parser.add_argument('--generations', type=int, help=f"Number of generations (default: {DEFAULT_CONFIG['num_generations']}).")
    parser.add_argument('--reward_prob', type=float, help=f"Probability of reward per step (default: {DEFAULT_CONFIG['reward_probability']:.4f}).")
    parser.add_argument('--threshold', type=int, help=f"Agent's initial give-up threshold (default: {DEFAULT_CONFIG['agent_initial_threshold']}).")
    parser.add_argument('--agent', type=str, choices=['SimpleAgent', 'LearningAgent'], help=f"Type of agent (default: {DEFAULT_CONFIG['agent_type']}).")
    parser.add_argument('--lr', type=float, help=f"Learning rate for LearningAgent (default: {DEFAULT_CONFIG['learning_rate']}).")
    parser.add_argument('--log_level', type=str, choices=['TRACE', 'DEBUG', 'INFO', 'WARNING', 'ERROR'], help=f"Logging level (default: {DEFAULT_CONFIG['log_level']}).")
    parser.add_argument('--max_steps', type=int, help=f"Max steps per generation safety break (default: {DEFAULT_CONFIG['max_steps_per_generation']}).")
    parser.add_argument('--name', type=str, help=f"Custom simulation name (default: {DEFAULT_CONFIG['simulation_name']}).")
    parser.add_argument('--output_base', type=str, help=f"Base directory for results (default: {DEFAULT_CONFIG['output_dir_base']}).")
    # Add more arguments if needed for other config options

    args = parser.parse_args()

    # --- Build Configuration ---
    # Start with defaults, override with any command-line arguments provided
    config = DEFAULT_CONFIG.copy()
    if args.generations is not None: config['num_generations'] = args.generations
    if args.reward_prob is not None: config['reward_probability'] = args.reward_prob
    if args.threshold is not None: config['agent_initial_threshold'] = args.threshold
    if args.agent is not None: config['agent_type'] = args.agent
    if args.lr is not None: config['learning_rate'] = args.lr
    if args.log_level is not None: config['log_level'] = args.log_level
    if args.max_steps is not None: config['max_steps_per_generation'] = args.max_steps
    if args.name is not None: config['simulation_name'] = args.name
    if args.output_base is not None: config['output_dir_base'] = args.output_base
    # Add checks for invalid combinations if necessary (e.g., learning_rate without LearningAgent)

    # --- Create Unique Output Directory ---
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    # Sanitize parts of the name for filesystem compatibility
    safe_sim_name = "".join(c if c.isalnum() else "_" for c in config['simulation_name'])
    safe_agent_type = config['agent_type']
    run_folder_name = f"{safe_sim_name}_{safe_agent_type}_Thresh{config['agent_initial_threshold']}_{timestamp}"
    config['output_dir'] = os.path.join(config['output_dir_base'], run_folder_name)

    # Create the directory *before* setting up file logging
    try:
        os.makedirs(config['output_dir'], exist_ok=True)
        print(f"Results will be saved in: {config['output_dir']}") # Early user feedback
    except OSError as e:
        print(f"[CRITICAL ERROR] Failed to create output directory '{config['output_dir']}': {e}. Exiting.", file=sys.stderr)
        sys.exit(1) # Exit if we can't create the output directory

    # --- Setup Logging ---
    log_file_path = os.path.join(config['output_dir'], "simulation.log")
    setup_logging(
        level_str=config['log_level'],
        log_file=log_file_path,
        log_to_console=config['log_to_console'],
        log_to_file=config['log_to_file']
    )

    # --- Run Simulation ---
    # Wrap in try...except block to catch potential top-level errors in the run
    try:
        logging.info("Starting simulation run...")
        generation_data, final_env_stats = run_simulation(config)
        logging.info("Simulation run completed.")
    except Exception as e:
        logging.critical(f"A critical error occurred during run_simulation: {e}", exc_info=True)
        print(f"\n[CRITICAL ERROR] Simulation failed unexpectedly: {e}. Check simulation.log for details.", file=sys.stderr)
        # Ensure partial data is not processed if the run failed catastrophically
        generation_data = []
        final_env_stats = {} # Or provide default/empty stats

    # --- Generate Report ---
    if generation_data: # Only generate report if simulation produced valid data
        logging.info("Starting report generation...")
        try:
            generate_report(generation_data, final_env_stats, config, config['output_dir'])
            logging.info("Report generation finished successfully.")
        except Exception as e:
            logging.error(f"Failed to generate report: {e}", exc_info=True)
            print(f"\n[ERROR] Could not generate the final report: {e}. Check simulation.log.", file=sys.stderr)
    else:
        logging.warning("No generation data was produced or simulation failed; skipping report generation.")
        print("\nNo valid simulation data generated, skipping report creation.")

    # --- Final Output ---
    logging.info(f"Script finished. Output located in: {config['output_dir']}")
    print("\n" + "="*60)
    print(f"Simulation finished. Results are in directory:")
    print(f"{config['output_dir']}")
    print("Check the .log file for detailed execution trace and the .pdf for summary and plots.")
    print("="*60)
    sys.exit(0) # Explicitly exit with success code
