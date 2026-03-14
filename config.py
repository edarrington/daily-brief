import os

GRAPH_CLIENT_ID = os.environ["GRAPH_CLIENT_ID"]
GRAPH_CLIENT_SECRET = os.environ["GRAPH_CLIENT_SECRET"]
GRAPH_TENANT_ID = os.environ["GRAPH_TENANT_ID"]
FROM_EMAIL = os.environ.get("FROM_EMAIL", "erick@singularityai.tech")
TO_EMAIL = os.environ.get("TO_EMAIL", "erickdarrington@gmail.com")
