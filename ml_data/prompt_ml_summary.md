# Task
Summarize the Apache Arrow dev mailing list activity from the past month. Target audience: developers wanting a quick overview of what's happening in the project.

# Output format
The summary is shown in a small card on a dashboard, so it has to be quick to scan. Aim for about 2,500 characters in total.

- One flat bulleted list of 5-10 key discussions/topics. No nested bullets
- Each bullet: a bold topic name, then one or two sentences saying what happened or what was decided, then the link(s). Two sentences is the limit; if a topic needs more, keep the outcome and drop the detail
- Describe the discussion, not who took part. Name a person only when the topic makes no sense without them, at most one name per bullet. Do not list who voted, replied or agreed
- Refer to people by name. Never use gendered pronouns (he/she/his/her) for anyone; repeat the name, use "they", or rephrase, since a name does not tell you someone's gender
- At most two links per bullet, and only links to mailing list threads in the format below. No links to PRs, reports or other sites
- Link format: [Thread](https://lists.apache.org/list?dev@arrow.apache.org:lte=2M:<thread_title>)
  - The link text is always the word Thread, and links are separated by a single space
  - Remove "Re: " prefix from thread titles
  - Replace spaces with %20, remove colons, and URL-encode other special characters
  - Replace square-bracket tags with the word inside them followed by a space, so "[VOTE][Format] Add X" becomes VOTE%20Format%20Add%20X
- Combine closely related threads (for example several releases of one subproject) into one bullet
- Skip threads about the mailing list summary/dashboard itself
- No intro, outro, or section headings - just the list

# Example output

* **Swift repository split:** Discussion on moving Swift implementation to a separate repo for independent releases and reduced maintenance burden. [Thread](https://lists.apache.org/list?dev@arrow.apache.org:lte=2M:Split%20Swift%20to%20separated%20repository)

* **Arrow 19.0.0 release:** Vote passed for the January release, includes new string view types and improved Parquet performance. [Thread](https://lists.apache.org/list?dev@arrow.apache.org:lte=2M:VOTE%20Release%20Apache%20Arrow%2019.0.0%20-%20RC1)

* **C++ memory allocation improvements:** Proposal to add custom allocator support for better integration with GPU memory pools. [Thread](https://lists.apache.org/list?dev@arrow.apache.org:lte=2M:Custom%20allocator%20proposal)
