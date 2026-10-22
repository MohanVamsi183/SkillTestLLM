import time

from skilltest.cache import Cache
from skilltest.models import call_model

cache = Cache()  # saves into .skilltest_cache\ in your project

for attempt in (1, 2):
    start = time.perf_counter()
    reply = call_model("Name one planet.", "groq/openai/gpt-oss-20b", cache=cache)
    seconds = time.perf_counter() - start
    print(f"Attempt {attempt}: {reply!r} in {seconds:.2f}s")