# reporting.py
import matplotlib.pyplot as plt
from fpdf import FPDF
import os
import datetime
import numpy as np
import logging

# Configure logging for reporting module
log = logging.getLogger(__name__)

def plot_lifespan_trend(generation_data, output_dir, filename="lifespan_trend.png"):
    """Plots lifespan per generation and a moving average."""
    if not generation_data:
        log.warning("No generation data provided for lifespan trend plot.")
        return None

    generations = list(range(1, len(generation_data) + 1))
    lifespans = [gen['summary']['lifespan'] for gen in generation_data]

    if not lifespans:
        log.warning("Lifespan data is empty, cannot generate trend plot.")
        return None

    plt.figure(figsize=(12, 6))
    plt.plot(generations, lifespans, marker='.', linestyle='-', alpha=0.6, label='Lifespan per Generation')

    # Calculate moving average (e.g., window of 10% of total generations, capped)
    window_size = max(1, min(len(generations) // 10, 50))
    if len(lifespans) >= window_size:
        # Use 'valid' mode: output length is N - window_size + 1
        moving_avg = np.convolve(lifespans, np.ones(window_size)/window_size, mode='valid')
        # Adjust x-axis for moving average alignment (starts after window_size-1 points)
        moving_avg_x = generations[window_size-1:]
        plt.plot(moving_avg_x, moving_avg, linestyle='--', color='red', linewidth=2, label=f'{window_size}-Gen Moving Avg')

    plt.title('Agent Lifespan Across Generations')
    plt.xlabel('Generation Number')
    plt.ylabel('Lifespan (Steps)')
    if len(generations) > 50: # Add finer grid lines for many generations
        plt.grid(True, which='both', linestyle='--', linewidth=0.5, alpha=0.7)
    else:
         plt.grid(True, alpha=0.7)
    plt.legend()
    plt.tight_layout() # Adjust layout to prevent labels overlapping

    plot_path = os.path.join(output_dir, filename)
    try:
        plt.savefig(plot_path)
        log.info(f"Saved lifespan trend plot to {plot_path}")
    except Exception as e:
        log.error(f"Failed to save lifespan trend plot '{plot_path}': {e}")
        plot_path = None # Indicate failure
    plt.close() # Close the plot to free memory
    return plot_path

def plot_lifespan_histogram(generation_data, output_dir, filename="lifespan_histogram.png"):
    """Plots a histogram of agent lifespans."""
    if not generation_data:
        log.warning("No generation data provided for histogram plot.")
        return None

    lifespans = [gen['summary']['lifespan'] for gen in generation_data]

    if not lifespans:
        log.warning("Lifespan data is empty, cannot generate histogram.")
        return None

    plt.figure(figsize=(10, 6))
    # Determine number of bins using Freedman-Diaconis rule or a simpler heuristic
    if len(lifespans) > 1:
        iqr = np.subtract(*np.percentile(lifespans, [75, 25]))
        bin_width = 2 * iqr * len(lifespans)**(-1/3) if iqr > 0 else 1
        num_bins = int(np.ceil((max(lifespans) - min(lifespans)) / bin_width)) if bin_width > 0 else max(10, int(np.sqrt(len(lifespans))))
        num_bins = max(5, min(num_bins, 100)) # Clamp bin count
    else:
        num_bins = 1 # Handle single data point case

    plt.hist(lifespans, bins=num_bins, edgecolor='black', alpha=0.75)
    plt.title('Distribution of Agent Lifespans')
    plt.xlabel('Lifespan (Steps)')
    plt.ylabel('Frequency (Number of Generations)')
    plt.grid(axis='y', alpha=0.75)
    plt.tight_layout()

    plot_path = os.path.join(output_dir, filename)
    try:
        plt.savefig(plot_path)
        log.info(f"Saved lifespan histogram plot to {plot_path}")
    except Exception as e:
        log.error(f"Failed to save lifespan histogram plot '{plot_path}': {e}")
        plot_path = None
    plt.close()
    return plot_path


class PDFReport(FPDF):
    def __init__(self, sim_config, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sim_config = sim_config
        self.set_auto_page_break(auto=True, margin=15)
        self.add_page()
        # Standard fonts usually available: Times, Helvetica, Courier
        self.set_font('Helvetica', '', 10)

    def header(self):
        self.set_font('Helvetica', 'B', 12)
        self.cell(0, 10, f"Simulation Report: {self.sim_config.get('simulation_name', 'Agent Persistence Study')}", 0, 1, 'C')
        self.set_font('Helvetica', '', 8)
        self.cell(0, 5, f"Report Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", 0, 1, 'C')
        self.ln(5) # Line break

    def footer(self):
        self.set_y(-15) # Position 1.5 cm from bottom
        self.set_font('Helvetica', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}/{{nb}}', 0, 0, 'C') # Add total page number

    def chapter_title(self, title):
        self.set_font('Helvetica', 'B', 12)
        self.set_fill_color(230, 230, 230) # Light grey background for titles
        self.cell(0, 8, title, 0, 1, 'L', fill=True)
        self.ln(4)

    def chapter_body(self, body):
        self.set_font('Helvetica', '', 10)
        # Use multi_cell for automatic line breaks and text wrapping
        self.multi_cell(0, 5, body)
        self.ln() # Add a line break after the body text

    def add_config_summary(self):
        self.chapter_title('1. Simulation Configuration')
        reward_prob = self.sim_config.get('reward_probability', 0)
        reward_interval = 1.0 / reward_prob if reward_prob > 0 else float('inf')
        config_text = f"""
        Simulation Name: {self.sim_config.get('simulation_name', 'N/A')}
        Total Generations Specified: {self.sim_config.get('num_generations', 'N/A')}
        Reward Probability (per step): {reward_prob:.5f}
          (Expected steps per reward: {reward_interval:.1f})
        Agent Type: {self.sim_config.get('agent_type', 'N/A')}
        Agent Initial Threshold: {self.sim_config.get('agent_initial_threshold', 'N/A')}
        Max Steps Per Generation: {self.sim_config.get('max_steps_per_generation', 'N/A')}
        Output Directory: {self.sim_config.get('output_dir', 'N/A')}
        Log Level: {self.sim_config.get('log_level', 'N/A')}
        """
        if self.sim_config.get('agent_type') == 'LearningAgent':
            config_text += f"\nLearning Rate: {self.sim_config.get('learning_rate', 'N/A')}"

        self.chapter_body(config_text.strip())

    def add_overall_results(self, generation_data, env_stats):
        self.chapter_title('2. Overall Results')
        if not generation_data:
            self.chapter_body("No generation data available to summarize.")
            log.warning("PDFReport: No generation data for overall results.")
            return

        lifespans = np.array([gen['summary']['lifespan'] for gen in generation_data])
        total_rewards_agent = sum(gen['summary']['total_rewards'] for gen in generation_data)
        total_punishments_agent = sum(gen['summary']['total_punishments'] for gen in generation_data)
        num_gens_run = len(generation_data)

        results_text = f"""
        Total Generations Simulated: {num_gens_run}
        Total Environment Steps Across All Generations: {env_stats.get('total_steps', 'N/A')}

        Agent Lifespan Statistics (over {num_gens_run} generations):
          - Average: {np.mean(lifespans):.2f} steps
          - Median: {np.median(lifespans):.2f} steps
          - Minimum: {np.min(lifespans)} steps
          - Maximum: {np.max(lifespans)} steps
          - Standard Deviation: {np.std(lifespans):.2f} steps
          - 25th Percentile: {np.percentile(lifespans, 25):.2f} steps
          - 75th Percentile: {np.percentile(lifespans, 75):.2f} steps

        Aggregate Event Counts (Agent Perspective):
          - Total Rewards Received: {total_rewards_agent}
          - Total Punishments Received: {total_punishments_agent}
          - Average Rewards per Generation: {total_rewards_agent / num_gens_run:.3f}

        Environment Statistics (Overall):
          - Total Rewards Issued: {env_stats.get('total_rewards', 'N/A')}
          - Total Punishments Issued: {env_stats.get('total_punishments', 'N/A')}
          - Actual Reward Rate (Rewards Issued / Total Steps): {env_stats.get('actual_reward_rate', 0):.5f}
            (Compare to configured rate: {env_stats.get('configured_reward_prob', 0):.5f})
        """
        self.chapter_body(results_text.strip())

        # Add Learning Agent threshold info if applicable
        if self.sim_config.get('agent_type') == 'LearningAgent' and generation_data:
             thresholds = [gen.get('threshold_used', np.nan) for gen in generation_data] # Handle potential missing key
             thresholds = [t for t in thresholds if not np.isnan(t)] # Filter out NaNs if any
             if thresholds:
                 self.set_font('Helvetica', 'B', 10)
                 self.cell(0, 6, "Learning Agent Threshold Dynamics:")
                 self.ln()
                 self.set_font('Helvetica', '', 10)
                 threshold_text = f"""
          - Initial Threshold: {self.sim_config.get('agent_initial_threshold', 'N/A')}
          - Final Threshold (end of last gen): {thresholds[-1]}
          - Minimum Threshold Observed: {min(thresholds)}
          - Maximum Threshold Observed: {max(thresholds)}
          - Average Threshold Across Generations: {np.mean(thresholds):.2f}
                 """
                 self.chapter_body(threshold_text.strip())


    def add_plot(self, plot_path, title="Plot"):
        """Adds a plot image to the PDF, scaling it to fit the page width."""
        if plot_path and os.path.exists(plot_path):
            self.chapter_title(title)
            try:
                # Get available width on page
                page_width = self.w - self.l_margin - self.r_margin
                # Open image to get its dimensions (optional, but good for aspect ratio)
                # from PIL import Image # Requires Pillow: pip install Pillow
                # with Image.open(plot_path) as img:
                #     img_width, img_height = img.size
                # aspect_ratio = img_height / img_width
                # img_render_height = page_width * aspect_ratio

                # Simplified: just use the width and let fpdf handle height scaling
                self.image(plot_path, x=self.l_margin, w=page_width)
                self.ln(5) # Space after image
                log.info(f"Added plot '{os.path.basename(plot_path)}' to PDF.")
            except Exception as e:
                log.error(f"Failed to add plot '{plot_path}' to PDF: {e}")
                self.set_font('Helvetica', 'I', 9)
                self.set_text_color(255, 0, 0) # Red color for error
                self.multi_cell(0, 5, f"[Error embedding plot: {os.path.basename(plot_path)} - Check logs and ensure image file is valid]")
                self.set_text_color(0, 0, 0) # Reset text color
                self.set_font('Helvetica', '', 10) # Reset font
        elif plot_path:
             log.warning(f"Plot file not found or invalid path provided: {plot_path}")
             self.set_font('Helvetica', 'I', 9)
             self.chapter_body(f"[Plot file not found or invalid: {os.path.basename(plot_path)}]")
        else:
             log.warning("Attempted to add a non-existent plot (plot_path was None).")
             self.set_font('Helvetica', 'I', 9)
             self.chapter_body("[Plot generation failed or was skipped]")


def generate_report(generation_data, env_stats, config, output_dir, filename="simulation_report.pdf"):
    """Generates plots and a PDF summary report."""
    log.info("Starting report generation...")
    if not os.path.exists(output_dir):
        log.warning(f"Output directory '{output_dir}' does not exist. Attempting to create.")
        try:
            os.makedirs(output_dir, exist_ok=True)
        except OSError as e:
            log.error(f"Failed to create output directory '{output_dir}': {e}. Cannot save report.")
            return

    # 1. Generate Plots
    lifespan_plot_path = plot_lifespan_trend(generation_data, output_dir)
    histogram_plot_path = plot_lifespan_histogram(generation_data, output_dir)

    # 2. Generate PDF
    pdf_path = os.path.join(output_dir, filename)
    pdf = PDFReport(config)
    pdf.alias_nb_pages() # Enable total page count feature '{nb}'

    # Add content sections
    pdf.add_config_summary()
    pdf.add_overall_results(generation_data, env_stats)
    pdf.add_plot(lifespan_plot_path, title="3. Lifespan Trend Analysis")
    pdf.add_plot(histogram_plot_path, title="4. Lifespan Distribution")

    # Optional: Add detailed generation summaries (consider performance for large reports)
    add_detailed_log = config.get("add_detailed_log_to_pdf", False)
    max_detailed_logs = config.get("max_detailed_logs_in_pdf", 10)

    if add_detailed_log and generation_data:
        log.info(f"Adding detailed log snippets for first {max_detailed_logs} generations to PDF.")
        pdf.add_page()
        pdf.chapter_title(f"5. Detailed Generation Log Snippets (First {max_detailed_logs})")
        pdf.set_font('Courier', '', 7) # Use monospace and small font for logs
        for i, gen_data in enumerate(generation_data[:max_detailed_logs]):
            summary = gen_data['summary']
            pdf.multi_cell(0, 3, f"--- Gen {gen_data['generation']} (End: {gen_data['end_reason']}) Thresh: {gen_data.get('threshold_used', 'N/A')} ---")
            pdf.multi_cell(0, 3, f"  Lifespan: {summary['lifespan']}, Rewards: {summary['total_rewards']}, Punish: {summary['total_punishments']}")
            pdf.multi_cell(0, 3, "  Decision Log (Last 5):")
            # Ensure decision log isn't excessively long in the PDF
            log_snippet = summary['decision_log'][-5:]
            for log_entry in log_snippet:
                 # Truncate very long log lines if necessary
                 display_entry = (log_entry[:120] + '...') if len(log_entry) > 120 else log_entry
                 pdf.multi_cell(0, 3, f"    {display_entry}")
            pdf.ln(1)
        if len(generation_data) > max_detailed_logs:
             pdf.set_font('Helvetica', 'I', 8)
             pdf.multi_cell(0, 4, f"... (details for {len(generation_data) - max_detailed_logs} more generations omitted for brevity)")
        pdf.set_font('Helvetica', '', 10) # Reset font
    else:
        log.info("Skipping detailed log snippets in PDF based on configuration.")

    try:
        pdf.output(pdf_path)
        log.info(f"Successfully generated PDF report: {pdf_path}")
    except Exception as e:
        log.error(f"Failed to write PDF report '{pdf_path}': {e}")

    log.info("Report generation finished.")
