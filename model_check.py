import cohere

import os

co = cohere.Client(os.getenv("COHERE_API_KEY"))

# now list models
models = co.models.list()

for m in models.models:
    print(m.name)