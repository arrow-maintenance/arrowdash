"""
Update language-specific mailing list data.

Output files:
  - data/{lang}_mailing_list.csv
"""

import logging
import os
import sys

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import ml_data.data_methods as ml

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)


def process_language_data(lang):
    """Process mailing list data for a language and save CSV."""
    logging.info(f"Processing {lang} mailing list")
    lang_lower = lang.lower()

    try:
        ml_df = ml.get_all(lang)
        ml_df.to_csv(f"data/{lang_lower}_mailing_list.csv", index=False)
        logging.info(f"  Wrote {lang_lower}_mailing_list.csv ({len(ml_df)} rows)")
    except Exception as e:
        logging.warning(f"  Failed to get mailing list for {lang}: {e}")
        pd.DataFrame(columns=["date", "url_title"]).to_csv(f"data/{lang_lower}_mailing_list.csv", index=False)


def main():
    logging.info("=== Updating language-specific data ===")
    os.makedirs("data", exist_ok=True)

    # Download user mailing list
    logging.info("Downloading user mailing list")
    ml.get_messages("user")

    # Process each language
    for lang in ["Python", "R"]:
        process_language_data(lang)

    logging.info("=== Language data update complete ===")


if __name__ == "__main__":
    main()
