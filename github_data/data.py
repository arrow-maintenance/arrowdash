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

from datetime import date, timedelta
import os
import requests

GH_API_TOKEN = os.environ["GH_API_TOKEN"]
HTTP_HEADERS = {
    "Accept": "application/vnd.github.v3+json",
    "Authorization": f"token {GH_API_TOKEN}",
}


def get_data():
    """
    Get issues and PRs updated in last three months with the GitHub API call.

    Returns
    -------
    data : list
        list of issues and PRs updated in the last 3 months
    """
    data = []

    last_3_months = date.today() - timedelta(days=90)
    last_3_months = last_3_months.strftime("%Y-%m-%dT%H:%M:%SZ")

    page_number = 1
    while True:
        resp = requests.get(
            "https://api.github.com/repos/apache/arrow/issues",
            params={
                "state": "all",
                "since": last_3_months,
                "per_page": 100,
                "page": page_number,
            },
            headers=HTTP_HEADERS,
        )

        for item in resp.json():
            data.append(item)

        # search through all pages from the REST API
        if "Link" in resp.headers and 'rel="next"' in resp.headers["Link"]:
            page_number += 1
        else:
            break

    return data
