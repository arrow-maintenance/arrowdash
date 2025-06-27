import os

from chatlas import ChatGoogle


def summarisation_input(content):
    """
    Prepares input for summarization by formatting issues into a single string.

    Args:
        issues (list[dict]): A list of issue titles and bodies.

    Returns:
        str: Formatted string representation of issues in content.
    """
    return "\n" + "\n\n" + "-" * 80 + "\n\n".join(
        f"{item["body"]}" for item in content
    )

TOPIC_KEYWORDS_PYTHON = {
    "dataset": ["dataset", "open_dataset", "write_dataset"],
    "compute": ["compute", "expression", "filter", "execute_scalar"],
    "ipc": ["ipc", "stream", "file format"],
    "feather": ["feather", "read_feather", "write_feather"],
    "table": ["table", "table.", "Table", "RecordBatch", "Schema"],
    "filesystem": ["azure", "fs", "filesystem", "S3", "HDFS"],
    "pandas": ["pandas", "to_pandas", "from_pandas"],
    "parquet": ["parquet", "ParquetFile", "ParquetDataset"],
    "acero": ["acero"],
    "extension": ["extension types", "ExtensionType", "ExtensionArray"],
    "install": ["pip install", "build", "wheel", "conda", "mamba"]
}

TOPIC_KEYWORDS_R = {
    "dataset": ["dataset", "open_dataset", "write_dataset"],
    "compute": ["compute", "expression", "filter"],
    "ipc": ["ipc", "stream", "file format"],
    "table": ["arrow_table", "Table", "RecordBatch", "Schema"],
    "filesystem": ["azure", "fs", "filesystem", "S3"],
    "parquet": ["parquet", "ParquetFile", "read_parquet"],
    "dplyr": ["acero", "dplyr"],
    "install": ["download", "install", "install.packages", "CRAN"]
}

TOPICS_PYTHON = [
    "Documentation and user guidance (combine documentation issues and user questions)",
    "Bugs",
    "Interoperability in Python Ecosystem",
    "Feature requests",
]

TOPICS_R = [
    "Documentation and user guidance (combine documentation issues and user questions)",
    "Bugs",
    "Feature requests",
]

def generate_summary_prompt_txt(
    output_file, component_mapping, topics, num_bullets=3
):
    """
    Generates a markdown-formatted prompt file for summarizing GitHub issue trends
    in Apache Arrow.

    The output includes:
    - Detailed instructions for summarizing issue tracker content
    - Structured content guidelines
    - Output style expectations and formatting rules
    - An example section illustrating the desired format

    Parameters:
    ----------
    output_file : str
        Name of the output markdown file.
    topics : list of str
        List of topic section headings.
    num_bullets : int, optional
        The number of bullet points required under each output section (default is 3).

    Returns:
    -------
    None
        Writes formatted markdown instructions to the specified output file.
    """
    with open(output_file, "w") as f:
        f.write(f"""
# Task
Create a concise, high-level summary (max 300 words) of current trends in the Apache Arrow GitHub
issue tracker. The summary is intended for developers who want an overview of user needs and technical
challenges.

Follow these detailed requirements:

# Content Guidelines
- Focus on trends across the issue tracker, not individual issues.
- Highlight:
""")
        for topic in topics:
            f.write(f"  - ## {topic}\n")
        f.write(f"""
# Output Style & Structure
- Use **Markdown format** with ## headings for each of the following topics:
""")
        for topic in topics:
            f.write(f"  - ## {topic}\n")
        f.write(f"""
- For each topic, include maximum {num_bullets} bullet points, each summarizing the most common themes.
- For the "Documentation and user guidance" section:
  - Combine issues including documentation and user questions, since both often highlight
  gaps in usage clarity.
  - The goal is to surface which components most need improved documentation, tutorials,
  or code examples.
  - Treat common user confusion as actionable input for improving docs.
- Each bullet should include:
  - A short summary of the trend or need for that component
- Do **NOT** include any introduction or conclusion. Begin directly with the first heading.

# Do Not
-  Exceed 300 words.
-  List or summarize individual issues unless grouped by theme.
-  Add fluff or general commentary.

# Example of a good output

Here's a partial example of good output:

'## Documentation and user guidance

*   Users are confused about how to access summary statistics from a Parquet file. There would
    be a need to update the documentation with examples including Statistics object.
*   The community is asking for User Guide improvement, specially for the dataset module.
'
""")

def summarise_github_issues(content, component):
    """
    Summarizes the GitHub issues from the past year using a pre-defined prompt and Google Chat API.

    Returns:
        str: The summarized output.
    """
    content_string = summarisation_input(content)
    chat = ChatGoogle(api_key=os.getenv("GOOGLE_API_KEY"))

    if component.lower() == "python":
        prompt_file = "./github_data/prompt_issues_summary_py.txt"
        component_mapping = TOPIC_KEYWORDS_PYTHON
        topics = TOPICS_PYTHON
        num_bullets = 3
    elif component.lower() == "r":
        prompt_file = "./github_data/prompt_issues_summary_r.txt"
        component_mapping = TOPIC_KEYWORDS_R
        topics = TOPICS_R
        num_bullets = 2
    
    generate_summary_prompt_txt(
        prompt_file, component_mapping, topics, num_bullets=num_bullets,
    )

    with open(prompt_file, "r", encoding="utf-8") as f:
        chat_prompt = f.read()

    summary = chat.chat(chat_prompt, content_string)
    return str(summary)
