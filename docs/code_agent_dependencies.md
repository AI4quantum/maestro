# Code Agent Dependencies

The Code Agent now supports automatic installation of Python dependencies before executing code. This feature allows you to specify dependencies in the agent's metadata, which will be installed using pip before the code is executed.

## Specifying Dependencies

To specify dependencies for a Code Agent, add a `dependencies` field to the agent's metadata section in the agent definition YAML:

```yaml
apiVersion: maestro/v1alpha1
kind: Agent
metadata:
  name: my-code-agent
  dependencies: |
    requests==2.31.0
    numpy>=1.20.0
    pandas
spec:
  framework: code
  description: A code agent that uses external dependencies
  code: |
    import requests
    import numpy as np
    import pandas as pd
    
    # Your code here
    output = {"result": "Success!"}
```

## Dependencies Format

The `dependencies` field follows the standard `requirements.txt` format:

- Each dependency should be on a separate line
- You can specify version constraints using the standard pip syntax:
  - `package==1.0.0`: Exact version
  - `package>=1.0.0`: Minimum version
  - `package<=1.0.0`: Maximum version
  - `package`: Latest version

## Considerations

- Dependencies are installed using pip in the current Python environment
- Installation occurs before each execution of the code agent
- If installation fails, the agent will raise an error and the code will not be executed
- Consider using virtual environments when working with code agents that have dependencies to avoid conflicts
- For security reasons, be cautious when running code agents with dependencies from untrusted sources

## Example

Here's an example of a code agent that uses external dependencies to fetch and parse a webpage:

```yaml
apiVersion: maestro/v1alpha1
kind: Agent
metadata:
  name: web-scraper-agent
  dependencies: |
    requests==2.31.0
    beautifulsoup4==4.12.2
spec:
  framework: code
  description: A code agent that fetches and parses web content
  code: |
    import requests
    from bs4 import BeautifulSoup
    
    # Simple function that uses the installed dependencies
    def fetch_webpage_title(url):
        try:
            response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.title.string if soup.title else "No title found"
            return title
        except Exception as e:
            return f"Error: {str(e)}"
    
    # Get a webpage title
    url = input[0] if input and len(input) > 0 else "https://www.example.com"
    title = fetch_webpage_title(url)
    output = f"Title of {url}: {title}"
```

This agent will automatically install the `requests` and `beautifulsoup4` packages before executing the code.
