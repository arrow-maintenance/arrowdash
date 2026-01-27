# Task
Summarize the Apache Arrow dev mailing list activity from the past month. Target audience: developers wanting a quick overview of what's happening in the project.

# Output format
- One bulleted list of 5-10 key discussions/topics
- Each bullet: brief description (1-2 sentences) + link(s) to relevant thread(s)
- Link format: [Thread](https://lists.apache.org/list?dev@arrow.apache.org:lte=2M:<thread_title>)
  - Remove "Re: " prefix from thread titles
  - Replace spaces with %20, remove colons and square brackets, URL-encode other special characters
- Skip threads about the mailing list summary/dashboard itself
- No intro, outro, or section headings - just the list

# Example output

* **Swift repository split:** Discussion on moving Swift implementation to a separate repo for independent releases and reduced maintenance burden. [Thread](https://lists.apache.org/list?dev@arrow.apache.org:lte=2M:Split%20Swift%20to%20separated%20repository)

* **Arrow 19.0.0 release:** Vote passed for the January release, includes new string view types and improved Parquet performance. [Thread](https://lists.apache.org/list?dev@arrow.apache.org:lte=2M:VOTE%20Release%20Apache%20Arrow%2019.0.0%20-%20RC1)

* **C++ memory allocation improvements:** Proposal to add custom allocator support for better integration with GPU memory pools. [Thread](https://lists.apache.org/list?dev@arrow.apache.org:lte=2M:Custom%20allocator%20proposal)
