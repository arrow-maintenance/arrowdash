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

import mailbox
import pandas as pd
import requests


def get_data():
    """
    Download and save mbox file from Apache Arrow mailing list archive.
    """
    url = "https://lists.apache.org/api/mbox.lua?list=user&domain=arrow.apache.org"
    resp = requests.get(url)

    with open("emails.mbox", mode="wb") as file:
        file.write(resp.content)


def get_all(component):
    """
    Get user mailing list threads and email subject from the last
    month that are labelled with a particular component.

    This method needs mbox file to be saved to ./'emails.mbox'.

    Parameters
    ----------
    component : string
        Python or R.

    Returns
    -------
    issues : pd.DataFrame
        Pandas data frame with mailing list information.
    """
    if component == "R":
        component = "[R]"
    list = [(message['Date'],
             message['Subject'],
             message['Thread-Topic'])
             for message in mailbox.mbox('emails.mbox') 
             if component.lower() in message['Subject'].lower()]
    
    df = pd.DataFrame(list, columns =['date', 'subject', 'thread'])

    # Add url_title column with href link to the search result of the email
    # thread or subject in the Apache Arrow mailing list Pony Mail
    # https://lists.apache.org/list?user@arrow.apache.org

    df["url_title"] = df.subject.str.replace(' ', '%20', regex=False)
    df["url_title"] = (
        '<a target="_blank" href="https://lists.apache.org/list?user@arrow.apache.org:lte=1M' +
        df["url_title"] + '">' +
        df["subject"] + "</a>"
    )
    return df[["date", "url_title"]]
