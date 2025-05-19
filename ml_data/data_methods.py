# MIT license

# Copyright (c) 2024 ???

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import logging
import mailbox
import pandas as pd
import requests

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

def get_messages(list_name):
    """
    Download and save mbox file from Apache Arrow mailing list archive.
    """
    url = f"https://lists.apache.org/api/mbox.lua?list={list_name}&domain=arrow.apache.org"
    logging.info(f"Starting download of mbox file from Apache Arrow {list_name} mailing list.")

    try:
        resp = requests.get(url)
        resp.raise_for_status()
        with open(f"{list_name}_ml.mbox", mode="wb") as file:
            file.write(resp.content)
        logging.info(f"Successfully downloaded and saved {list_name} mbox file.")
    except requests.exceptions.RequestException as e:
        logging.error(f"Failed to download {list_name} mbox file: {e}")
        raise

def get_all(component):
    """
    Get user mailing list threads and email subject from the last
    month that are labelled with a particular component.

    This method needs mbox file to be saved to ./'user_ml.mbox'.

    Parameters
    ----------
    component : string
        Python or R.

    Returns
    -------
    issues : pd.DataFrame
        Pandas data frame with mailing list information.
    """
    logging.info(f"Processing mbox file for component: {component}")

    if component == "R":
        component = "[R]"

    try:
        email_list = [
            (message["Date"], message["Subject"], message["Thread-Topic"])
            for message in mailbox.mbox("user_ml.mbox")
            if component.lower() in (message["Subject"] or "").lower()
        ]

        logging.info(f"Found {len(email_list)} messages related to component: {component}")

        df = pd.DataFrame(email_list, columns=["date", "subject", "thread"])

        # Add url_title column with href link to the search result of the email
        df["url_title"] = df.subject.str.replace(" ", "%20", regex=False)
        df["url_title"] = (
            '<a target="_blank" href="https://lists.apache.org/list?user@arrow.apache.org:lte=1M'
            + df["url_title"]
            + '">'
            + df["subject"]
            + "</a>"
        )

        logging.info("Successfully created DataFrame with mailing list information.")
        return df[["date", "url_title"]]

    except Exception as e:
        logging.error(f"Error while processing mbox file: {e}")
        raise
