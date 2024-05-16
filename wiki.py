import json
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
from pprint import pprint
from datetime import datetime

# Load config
with open("config.json", "r") as f:
    config = json.load(f)

_transport = RequestsHTTPTransport(
    url=config["wiki_url"],
    headers={"Authorization": f'Bearer {config["wiki_api"]}'},
    use_json=True,
)

client = Client(
    transport=_transport,
    fetch_schema_from_transport=True,
)


def write(content: str, id: int, timestamp=False, force=False):
    # Get the current content of the page
    query = gql(
        """
        query getPage($id: Int!) {
            pages {
                single(id: $id) {
                    path
                    title
                    createdAt
                    content
                }
            }
        }
        """
    )

    page = client.execute(query, variable_values={"id": id})

    old_content = page["pages"]["single"]["content"]

    # Remove generated timestamps if they're expected on this page
    if timestamp:
        old_content = old_content.split("\n")
        for line in old_content:
            if line.startswith("This page was automatically generated at: "):
                old_content.remove(line)
        old_content = "\n".join(old_content)

    # Compare the new content with the old content
    if old_content == content and not force:
        return

    else:
        if timestamp:
            content = f"{content}\nThis page was automatically generated at: {datetime.now().isoformat()}"

    # Update the page
    mutation = gql(
        """
        mutation update($id: Int!, $content: String!) {
            pages {
                update(
                    id: $id
                    content: $content
                    isPublished: true
                ) {
                    page {
                        id
                        content
                        title
                    }
                }
            }
        }
        """
    )

    render = gql(
        """
        mutation update($id: Int!) {
            pages {
                render(
                    id: $id
                ) {
                    responseResult {
                succeeded
                errorCode
                slug
                message
                }
                }
            }
        }
        """
    )

    client.execute(mutation, variable_values={"id": id, "content": content})
    client.execute(render, variable_values={"id": id})


write(content="Testing\na b c", id=961, timestamp=True, force=True)
