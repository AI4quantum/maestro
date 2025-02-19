# Summary.ai Example

A multi-agent workflow using Maestro: Allows an user to specify a topic from Arxiv they want to look at, choose a number of potential papers to summarize.

## Getting Started

* Run a local instance of the [bee-stack](https://github.com/i-am-bee/bee-stack/blob/main/README.md)

* Verify a valid llm is available to bee-stack

* Install [maestro](https://github.com/i-am-bee/beeai-labs) dependencies: `cd ../../../maestro && poetry shell && poetry install && cd -`

* Configure environmental variables: `cp example.env .env`

* Copy `.env` to common directory: `cp .env ./../common/src`

### Allowing maestro to be run from anywhere

Modify wrapper script: `nano ~/.local/bin/maestro`
Set the script path to run relative to your location, whereever in the terminal:

```bash
#!/bin/bash
export PYTHONPATH="/Users/REPLACEwUser/Desktop/work/bee-hive:$PYTHONPATH"
python3 -m maestro.cli.maestro "$@"
```

Make sure the script is executable: `chmod +x ~/.local/bin/maestro`
Verify maestro is running properly: `maestro --help`

* Set up the demo and create the agents: `./setup.sh`

* Run the workflow: `./run.sh` (to run for a different topic, change the `prompt` field in `workflow.yaml`)

Assuming you are in maestro top level:

* Creating the agents(with the ability to manually add tools): `maestro create ./demos/workflows/summary.ai/test_yaml/agents.yaml`

* Running the workflow: (to run for a different topic, change the `prompt` field in `workflow.yaml`):

- If you already created the agents and enabled the tool: `maestro run None ./demos/workflows/summary.ai/test_yaml/workflow.yaml`

OR

- Directly run the workflow: `maestro run ./demos/workflows/summary.ai/test_yaml/agents.yaml ./demos/workflows/summary.ai/test_yaml/workflow.yaml`

### NOTE: Custom Tools Required for this Demo

Go into the UI and make 2 tools for this demo:

1) Fetch tool:

Name: Fetch

Code:

```Python
import urllib.request

def fetch_arxiv_titles(topic: str, k: int = 10):
  """Fetches the k most recent article titles from arXiv on a given topic."""
  url = f"http://export.arxiv.org/api/query?search_query=all:{topic}&sortBy=submittedDate&sortOrder=descending&max_results={k}"

  with urllib.request.urlopen(url) as response:
      data = response.read().decode()

  titles = [line.split("<title>")[1].split("</title>")[0] for line in data.split("\n") if "<title>" in line][1:k+1]
  return titles
```

2) Filtering tool:

Name: Filter

Code:

```Python
import urllib.request
import urllib.parse
import re

def fetch_valid_arxiv_titles(titles: list):
    """
    Fetches titles that have an available abstract on ArXiv.

    Args:
        titles (list): List of paper titles.

    Returns:
        list: Titles that have an abstract.
    """
    base_url = "http://export.arxiv.org/api/query?search_query="
    valid_titles = []

    for title in titles:
        search_query = f'all:"{urllib.parse.quote(title)}"'
        url = f"{base_url}{search_query}&max_results=1"
        try:
            with urllib.request.urlopen(url) as response:
                data = response.read().decode()
        except Exception as e:
            continue

        abstract_match = re.search(r"<summary>(.*?)</summary>", data, re.DOTALL)

        if abstract_match:
            valid_titles.append(title)
        else:
            print(f"❌ No abstract found: {title}")
    return valid_titles
```
