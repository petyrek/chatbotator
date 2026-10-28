"""TrailSupply support assistant API.

A chat request flows: routes/chat.py (HTTP) → assistant/reply.py (the model
call) → policies.py (the documents it answers from).
"""
