"""Data access connection boundary. Repository owner: wzy.

Legacy SQL is temporarily retained in services to preserve behavior. Move it into
domain repositories incrementally; do not change routers or API contracts.
"""
from database import get_connection as get_connection
