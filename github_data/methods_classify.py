from collections import defaultdict, Counter
import requests
from transformers import pipeline


TOPIC_KEYWORDS_PYTHON = {
    "dataset": ["dataset", "Dataset", "open_dataset", "write_dataset"],
    "compute": ["compute", "expression", "filter", "join", "hash"],
    "ipc": ["ipc", "streaming format", "file format"],
    "feather": ["feather", "read_feather", "write_feather"],
    "tables": [".Table", ".RecordBatch", ".Schema"],
    "filesystem": ["LocalFileSystem", "azure", "fs", "filesystem", "S3", "HDFS"],
    "pandas": ["pandas", "to_pandas", "from_pandas"],
    "parquet": ["parquet", "ParquetFile", "ParquetDataset"],
    "acero": ["acero", "Declaration"],
    "extension": ["extension types", "ExtensionType", "ExtensionArray"],
    "install": ["pip install", "build", "wheel", "conda", "mamba"]
}

# ------ METHODS ------

def fetch_issues(repo, state='open', per_page=100):
    issues = []
    url = "https://api.github.com/search/issues"
    headers = {"Accept": "application/vnd.github+json"}
    # Search query for issues created in given year and state
    query = f"repo:{repo} is:issue is:{state} created:2024-01-01..2025-12-31"
    params = {"q": query, "per_page": per_page, "page": 1}

    while True:
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        data = response.json()
        issues.extend(data.get("items", []))
        # Pagination logic: stop if no more pages
        if 'next' not in response.links:
            break
        params['page'] += 1
    return issues

def filter_issues_by_keywords(issues, keywords_dict):
    "Filter issues by the keywords included in the issue title and body"
    filtered_issues = {key: [] for key in keywords_dict}
    for issue in issues:
      for label in issue["labels"]:
        if label["name"] == "Component: Python":
          for topic, keywords in keywords_dict.items():
              if any(keyword.lower() in (issue['title'] + ' ' + (issue.get('body', '') or '')).lower() for keyword in keywords):
                  filtered_issues[topic].append(issue)
    return filtered_issues

def aggregate_pain_points(issues):
    "Aggregate issues that are classified by the model"
    keyword_counts = {key: len(issue_list) for key, issue_list in issues.items()}
    pain_point_counts = Counter()
    pain_point_by_topic = defaultdict(Counter)

    for topic, issue_list in issues.items():
        for issue in issue_list:
            pain_points = issue.get('pain_point', '')
            for point in [p.strip() for p in pain_points.split(',') if p.strip()]:
                pain_point_counts[point] += 1
                pain_point_by_topic[topic][point] += 1

    return keyword_counts, pain_point_counts, pain_point_by_topic

def get_issue_links_by_topic_and_pain_point(issues, component, pain_point):
    """
    Return a list of issue URLs for a specific component and pain point.
    """
    matching_links = []

    # Safety check: ensure the component exists
    if component not in issues:
        return []

    for issue in issues[component]:
        issue_url = issue.get('html_url', '')
        classified_points = issue.get('pain_point', '')

        # Check if the pain_point is one of the classifications
        if any(p.strip() == pain_point for p in classified_points.split(',')):
            matching_links.append(issue_url)

    return matching_links

# CLASSIFICATION MODEL

generator = pipeline(
    "text2text-generation",
    model="google/flan-t5-base",
    device=-1,
)

def classify_pain_point_flan(issue_title, issue_body):
    "Runs the classification model on the issue title and body to get the pain point"
    issue_title = issue_title[:100]
    issue_body = issue_body[:500]

    prompt = f"""
You are an expert in PyArrow. Classify the following GitHub issue into one or more of these categories:
- Bugs, 
- Documentation and usage questions, 
- Features,
- Interoperability.

Return only the category or categories, separated by commas.

Title: {issue_title}
Body: {issue_body}
"""
    result = generator(prompt, max_new_tokens=50)
    return result[0]["generated_text"].strip().split('\n')[0]

def classify_issues_flan(issues):
    "Run the classification model for all the issues to get the pain points"
    for _, issue_list in issues.items():
        for issue in issue_list:
            issue_title = issue.get('title') or ""
            issue_body = issue.get('body') or ""
            if issue_body == "":
                continue
            issue['pain_point'] = classify_pain_point_flan(issue_title, issue_body)
    return issues


# ------ USAGE ------
# Fetch open issues created in 2024 and 2025 together
issues_2025 = fetch_issues("apache/arrow")
print(f"Found {len(issues_2025)} open issues created in 2024&2025.")

# Filter issues by keywords
filtered_issues = filter_issues_by_keywords(issues_2025, TOPIC_KEYWORDS_PYTHON)
print(f"Filtered issues by {len(filtered_issues.keys())} keywords:")
for key in filtered_issues.keys():
   print(f"Keyword got {len(filtered_issues[key])} issues.")

# Assuming filtered_issues is your dict of issues by topic, run the classification model
classified_issues = classify_issues_flan(filtered_issues)

# Check results

# ---------------------------------

keyword_counts, pain_point_counts, pain_point_by_topic = aggregate_pain_points(classified_issues)
print("Keyword Counts:", keyword_counts)
print("Pain Point Counts:", pain_point_counts)
print("Pain Point Counts by topics:", pain_point_by_topic)

tables_pp = get_issue_links_by_topic_and_pain_point(classified_issues, component="tables", pain_point="Documentation and usage questions")
print(tables_pp)

# ---------------------------------

import matplotlib.pyplot as plt

component = keyword_counts.keys()
values_1 = keyword_counts.values()

keywords, counts = zip(*sorted(zip(component, values_1), key=lambda x: x[1], reverse=True))

plt.figure(figsize=(10, 6))
plt.barh(keywords, counts, color='lightgreen', edgecolor='black')
plt.xlabel('Issue count')
plt.title('Keyword Frequencies (Sorted)')
plt.gca().invert_yaxis()  # Most frequent at the top
plt.tight_layout()

plt.show()

# ---------------------------------

pains = pain_point_counts.keys()
values_2 = pain_point_counts.values()

keywords, counts = zip(*sorted(zip(pains, values_2), key=lambda x: x[1], reverse=True))

plt.figure(figsize=(10, 6))
plt.barh(keywords, counts, color='lightgreen', edgecolor='black')
plt.xlabel('Count')
plt.title('Pain Point Frequencies (Sorted)')
plt.gca().invert_yaxis()  # Most frequent at the top
plt.tight_layout()

plt.show()

# ---------------------------------

# Step 1: Sort components by total issue count
sorted_components = sorted(pain_point_by_topic.items(), key=lambda x: sum(x[1].values()), reverse=True)
top_5 = sorted_components[:5]

# Step 2: Extract components and reformat data
components = [comp for comp, _ in top_5]
top_data = {comp: pain_point_by_topic[comp] for comp in components}

# Step 3: Extract all issue types (from top 5 only)
all_issue_types = sorted({itype for counts in top_data.values() for itype in counts})
issue_values = {itype: [top_data[comp].get(itype, 0) for comp in components] for itype in all_issue_types}

# Step 4: Plot
plt.figure(figsize=(10, 6))
bottom = [0] * len(components)
colors = plt.cm.tab20.colors

for i, itype in enumerate(all_issue_types):
    plt.bar(components, issue_values[itype], bottom=bottom, label=itype, color=colors[i % len(colors)])
    bottom = [sum(x) for x in zip(bottom, issue_values[itype])]

# Style
plt.xticks(rotation=45, ha='right')
plt.ylabel("Issue Count")
plt.title("Top 5 Components by Issue Volume")
plt.legend(title="Issue Type", bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
plt.show()
