apiVersion: maestro/v1alpha1
kind: Tool
metadata:
  name: Wikipedia
  labels:
    app: tool-example
spec:
  description: Search factual and historical information, including biography, history, politics, geography, society, culture, science, technology, people, animal species, mathematics, and other subjects.
  inputSchema:
    type: jsonSchema
    schema: |
      {
        "title": "WikipediaToolInput",
        "type": "object",
        "properties": {
          "query": {
            "type": "string",
            "description": "Name of the Wikipedia page."
          },
          "full_text": {
            "type": "boolean",
            "description": "If set to true, it will return the full text of the page instead of its short summary.",
            "default": false
          }
        },
        "required": ["query"]
      }
  outputSchema:
    type: jsonSchema
    schema: |
      {
        "title": "SearchToolResult",
        "type": "object",
        "properties": {
          "title": {
            "type": "string"
          },
          "description": {
            "type": "string"
          },
          "url": {
            "type": "string"
          }
        },
        "required": ["title", "description", "url"]
      }


