import re

# 1. Update src/utils/llm_adapter.py
adapter_path = "src/utils/llm_adapter.py"
with open(adapter_path, "r", encoding="utf-8") as f:
    adapter_code = f.read()

# Add saturate_model method after is_model_near_limit
saturate_def = '''    def saturate_model(self, model_name: str, api_key: str = "") -> None:
        """Menandai model pada api_key telah mencapai limit kuota (429/quota)."""
        h_key = self._get_history_key(model_name, api_key)
        thresh = self.get_proactive_threshold(model_name)
        now = time.time()
        with self._lock:
            if h_key not in self._history:
                self._history[h_key] = deque()
            while len(self._history[h_key]) < int(thresh + 1):
                self._history[h_key].append(now)
            self._last_call[h_key] = now
'''

if "def saturate_model" not in adapter_code:
    adapter_code = adapter_code.replace(
        "    def is_model_near_limit(self, model_name: str, api_key: str = \"\") -> bool:\n"
        "        threshold = self.get_proactive_threshold(model_name)\n"
        "        count = self.get_recent_call_count(model_name, api_key)\n"
        "        return count >= threshold\n",
        "    def is_model_near_limit(self, model_name: str, api_key: str = \"\") -> bool:\n"
        "        threshold = self.get_proactive_threshold(model_name)\n"
        "        count = self.get_recent_call_count(model_name, api_key)\n"
        "        return count >= threshold\n\n" + saturate_def
    )

# In chat(): replace the rate limit handling
old_chat_block = '''                if is_rate_limit:
                    logger.warning(f"Model {selected_model} terkena limit kuota (429), mencatat penggunaan kuota.")
                    for _ in range(5):
                        _rate_limiter.record_call(selected_model, selected_key or "")
                    if _key_pool.total_keys() > 1 and selected_key:
                        _key_pool.mark_rate_limited(selected_key, cooldown_seconds=60.0)
                    continue'''

new_chat_block = '''                if is_rate_limit:
                    logger.warning(f"Model {selected_model} terkena limit kuota (429), menandai model jenuh untuk beralih model/key.")
                    _rate_limiter.saturate_model(selected_model, selected_key or "")
                    continue'''

if old_chat_block in adapter_code:
    adapter_code = adapter_code.replace(old_chat_block, new_chat_block)
    print("Replaced chat() 429 block.")

# In embed_text(): replace the rate limit handling
old_embed_block = '''                is_rate = "429" in err_str or "quota" in err_str.lower() or "resourceexhausted" in err_str.lower()
                if is_rate:
                    for _ in range(10):
                        _rate_limiter.record_call(selected_model, selected_key or "")
                    if _key_pool.total_keys() > 1 and selected_key:
                        _key_pool.mark_rate_limited(selected_key, cooldown_seconds=60.0)
                    continue'''

new_embed_block = '''                is_rate = "429" in err_str or "quota" in err_str.lower() or "resourceexhausted" in err_str.lower()
                if is_rate:
                    logger.warning(f"Model embedding {selected_model} terkena limit kuota (429), menandai model jenuh untuk beralih model/key.")
                    _rate_limiter.saturate_model(selected_model, selected_key or "")
                    continue'''

if old_embed_block in adapter_code:
    adapter_code = adapter_code.replace(old_embed_block, new_embed_block)
    print("Replaced embed_text() 429 block.")

with open(adapter_path, "w", encoding="utf-8", newline="") as f:
    f.write(adapter_code)
print("Updated src/utils/llm_adapter.py successfully.")


# 2. Update tests/test_embedding_and_rag.py with setUp and tearDown
test_path = "tests/test_embedding_and_rag.py"
with open(test_path, "r", encoding="utf-8") as f:
    test_code = f.read()

setup_teardown = '''    def setUp(self):
        from src.utils.llm_adapter import _rate_limiter, _key_pool
        with _rate_limiter._lock:
            _rate_limiter._history.clear()
            _rate_limiter._last_call.clear()
        with _key_pool._lock:
            _key_pool._cooldowns.clear()

    def tearDown(self):
        from src.utils.llm_adapter import _rate_limiter, _key_pool
        with _rate_limiter._lock:
            _rate_limiter._history.clear()
            _rate_limiter._last_call.clear()
        with _key_pool._lock:
            _key_pool._cooldowns.clear()
'''

if "def setUp(self):" not in test_code:
    test_code = test_code.replace(
        "class TestEmbeddingFallbackAndRAG(unittest.TestCase):\n",
        "class TestEmbeddingFallbackAndRAG(unittest.TestCase):\n" + setup_teardown + "\n"
    )
    with open(test_path, "w", encoding="utf-8", newline="") as f:
        f.write(test_code)
    print("Updated tests/test_embedding_and_rag.py successfully.")
