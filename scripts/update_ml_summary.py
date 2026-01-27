"""
Generate dev mailing list summary using LLM.

Output file:
  - data/dev_ml_summary.txt
"""

import logging
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ml_data.summarise_ml as llm_ml

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


def main():
    logging.info("=== Generating dev mailing list summary ===")
    os.makedirs("data", exist_ok=True)

    try:
        summary = llm_ml.summarise_dev_ml()
        with open("data/dev_ml_summary.txt", "w", encoding="utf-8") as f:
            f.write(summary)
        logging.info("Wrote dev_ml_summary.txt")
    except Exception as e:
        logging.warning(f"Failed to generate ML summary: {e}")
        with open("data/dev_ml_summary.txt", "w", encoding="utf-8") as f:
            f.write("Summary generation failed. Please check the mailing list directly.")


if __name__ == "__main__":
    main()
