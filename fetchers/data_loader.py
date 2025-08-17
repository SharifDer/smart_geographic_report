# fetchers/data_loader.py
from typing import List, Dict
from fetchers.utils import getting_data_category
from concurrent.futures import ThreadPoolExecutor, as_completed

def preload_categories(conf, user_id: str, token: str, categories: List[str], parallel: bool = True) -> Dict[str, dict]:
    """
    Load each category once (from cache file or remote). Returns dict: category -> data (json/dict).
    Use parallel=True to load categories concurrently (useful if requests are remote & latency dominated).
    """
    if not parallel:
        return {c: getting_data_category(user_id, token, conf.raw_data, category=c) for c in categories}

    results = {}
    with ThreadPoolExecutor(max_workers=min(8, max(2, len(categories)))) as ex:
        futures = {ex.submit(getting_data_category, user_id, token, conf.raw_data, c): c for c in categories}
        for fut in as_completed(futures):
            c = futures[fut]
            results[c] = fut.result()
    return results
