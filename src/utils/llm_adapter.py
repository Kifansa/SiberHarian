from collections import deque
import os
import re
import threading
import time
from typing import List, Optional

import google.generativeai as genai
from src.utils.logger import setup_logger
from src.utils.settings_manager import SettingsManager

logger = setup_logger(__name__)

DEFAULT_MODEL_CHAIN = [
    "gemini-3.5-flash-lite",
    "gemini-3.5-flash",
    "gemini-3.6-flash",
    "gemini-3.7-flash",
]

DEFAULT_TIMEOUT_DETIK = 10.0


class APIKeyPool:
    """Manages multi-API key rotation and temporary cooldowns on 429 quota exhaustion."""

    def __init__(self):
        self._lock = threading.Lock()
        self._keys: List[str] = []
        self._current_index = 0
        self._cooldowns: dict[str, float] = {}

    def set_keys(self, raw_keys: any) -> None:
        with self._lock:
            parsed = []
            if isinstance(raw_keys, list):
                for k in raw_keys:
                    if isinstance(k, str) and k.strip():
                        parsed.append(k.strip())
            elif isinstance(raw_keys, str):
                for k in raw_keys.replace("\n", ",").split(","):
                    if k.strip():
                        parsed.append(k.strip())

            self._keys = parsed
            self._current_index = 0
            self._cooldowns.clear()

    def get_active_key(self) -> Optional[str]:
        with self._lock:
            if not self._keys:
                return None
            now = time.time()
            for i in range(len(self._keys)):
                idx = (self._current_index + i) % len(self._keys)
                k = self._keys[idx]
                if self._cooldowns.get(k, 0) <= now:
                    self._current_index = idx
                    return k
            # Fallback to key with earliest cooldown expiration
            earliest_key = min(self._keys, key=lambda k: self._cooldowns.get(k, 0))
            return earliest_key

    def mark_rate_limited(self, key: str, cooldown_seconds: float = 60.0) -> Optional[str]:
        """Put current key into cooldown and advance index to next available key."""
        with self._lock:
            now = time.time()
            self._cooldowns[key] = now + cooldown_seconds
            logger.warning(
                f"API Key ...{key[-6:] if len(key) >= 6 else key} terkena batas kuota, "
                f"masuk cooldown {cooldown_seconds:.0f}s."
            )
            for i in range(1, len(self._keys)):
                idx = (self._current_index + i) % len(self._keys)
                k = self._keys[idx]
                if self._cooldowns.get(k, 0) <= now:
                    self._current_index = idx
                    logger.info(f"Beralih ke API Key cadangan ...{k[-6:] if len(k) >= 6 else k}.")
                    return k
            return None

    def total_keys(self) -> int:
        with self._lock:
            return len(self._keys)


class GeminiRateLimiter:
    """Enforces sliding-window request-per-minute limits to avoid HTTP 429."""

    def __init__(self):
        self._lock = threading.Lock()
        self._history: dict[str, deque] = {}
        self._last_call: dict[str, float] = {}

    def _get_model_rpm_limit(self, model_name: str) -> float:
        name = model_name.lower()
        if "embedding" in name:
            return 80.0
        if "lite" in name:
            return 12.0
        return 4.0

    def wait_if_needed(self, model_name: str) -> None:
        """Paces API calls to stay strictly under the model's RPM limit."""
        clean_model = model_name.replace("models/", "").strip()
        safe_rpm = self._get_model_rpm_limit(clean_model)
        min_interval = 60.0 / safe_rpm

        with self._lock:
            if clean_model not in self._history:
                self._history[clean_model] = deque()
            history = self._history[clean_model]

            now = time.time()
            while history and now - history[0] > 60.0:
                history.popleft()

            sleep_time = 0.0
            if len(history) >= safe_rpm:
                oldest = history[0]
                sleep_time = max(sleep_time, (oldest + 60.0) - now + 0.2)

            last_call = self._last_call.get(clean_model, 0.0)
            elapsed = now - last_call
            if elapsed < min_interval:
                sleep_time = max(sleep_time, min_interval - elapsed)

        if sleep_time > 0.0:
            logger.debug(f"Pacing {clean_model}: menunggu {sleep_time:.2f} detik sesuai batas safe RPM ({safe_rpm:.0f} RPM).")
            time.sleep(sleep_time)

        with self._lock:
            post_now = time.time()
            self._history[clean_model].append(post_now)
            self._last_call[clean_model] = post_now


_key_pool = APIKeyPool()
_rate_limiter = GeminiRateLimiter()


class GeminiLLMAdapter:
    _configured_key: Optional[str] = None
    _configured = False

    @classmethod
    def _ensure_configured(cls) -> None:
        if not cls._configured:
            cfg = SettingsManager.get_gemini_config()
            raw_key = cfg.get("api_key", "")
            if not raw_key:
                raw_key = os.environ.get("GEMINI_API_KEY", "")

            _key_pool.set_keys(raw_key)
            active_key = _key_pool.get_active_key()
            if active_key:
                genai.configure(api_key=active_key)
                cls._configured_key = active_key
            cls._configured = True

    @classmethod
    def _switch_key_if_available(cls, failed_key: str, cooldown: float = 60.0) -> bool:
        new_key = _key_pool.mark_rate_limited(failed_key, cooldown)
        if new_key and new_key != cls._configured_key:
            genai.configure(api_key=new_key)
            cls._configured_key = new_key
            return True
        return False

    @classmethod
    def chat(
        cls,
        system_prompt: str,
        user_prompt: str,
        temperature: float = None,
        max_tokens: int = None,
        timeout: float = None,
    ) -> str:
        cls._ensure_configured()
        cfg = SettingsManager.get_gemini_config()

        if temperature is None:
            temperature = cfg.get("temperature", 0.1)
        if max_tokens is None:
            max_tokens = cfg.get("max_output_tokens", 500)
        if timeout is None:
            timeout = cfg.get("timeout_detik", DEFAULT_TIMEOUT_DETIK)

        model_chain = cfg.get("model_chain", DEFAULT_MODEL_CHAIN)

        for model_name in model_chain:
            # 2 percobaan per model sebelum beralih ke fallback model berikutnya
            for percobaan in range(2):
                _rate_limiter.wait_if_needed(model_name)
                try:
                    model = genai.GenerativeModel(
                        model_name=model_name,
                        system_instruction=system_prompt,
                        generation_config=genai.GenerationConfig(
                            temperature=temperature,
                            max_output_tokens=max_tokens,
                        ),
                    )
                    response = model.generate_content(
                        user_prompt,
                        request_options={"timeout": timeout},
                    )
                    if response and response.text:
                        logger.info(f"LLM OK via {model_name}")
                        return response.text.strip()
                except Exception as e:
                    err_str = str(e)
                    is_rate_limit = (
                        "429" in err_str
                        or "quota" in err_str.lower()
                        or "resourceexhausted" in err_str.lower()
                    )

                    if is_rate_limit:
                        # Prioritaskan rotasi API Key jika tersedia key cadangan
                        current_key = cls._configured_key or ""
                        if _key_pool.total_keys() > 1 and cls._switch_key_if_available(current_key):
                            logger.info(f"Mencoba ulang {model_name} dengan API key baru...")
                            continue

                        if percobaan == 0:
                            delay = 10.0
                            match = re.search(r"retry in (\d+(?:\.\d+)?)s", err_str, re.IGNORECASE)
                            if match:
                                delay = float(match.group(1))
                            else:
                                match_sec = re.search(r"seconds:\s*(\d+)", err_str)
                                if match_sec:
                                    delay = float(match_sec.group(1))
                            wait_time = min(max(delay + 1.0, 3.0), 20.0)
                            logger.warning(
                                f"{model_name} terkena batas laju (429), menunggu {wait_time:.1f} detik..."
                            )
                            time.sleep(wait_time)
                            continue

                    logger.warning(f"{model_name} gagal: {e}, mencoba fallback...")
                    break

        logger.error("Semua model Gemini gagal atau kuota API key habis.")
        return ""

    @classmethod
    def reload_config(cls) -> None:
        cls._configured = False
        cls._configured_key = None

    @classmethod
    def embed_text(cls, text: str, model_name: str = None) -> list:
        cls._ensure_configured()
        if not text or not str(text).strip():
            return []

        cfg = SettingsManager.get_gemini_config()
        model_name = model_name or cfg.get("embedding_model", "gemini-embedding-001")
        model_target = f"models/{model_name}" if not model_name.startswith("models/") else model_name

        for _ in range(2):
            _rate_limiter.wait_if_needed(model_target)
            try:
                res = genai.embed_content(
                    model=model_target,
                    content=str(text).strip(),
                    task_type="retrieval_query",
                )
                if res and "embedding" in res:
                    return res["embedding"]
            except Exception as e:
                err_str = str(e)
                if ("429" in err_str or "quota" in err_str.lower()) and cls._switch_key_if_available(cls._configured_key or ""):
                    continue
                logger.warning(f"Gagal generate vector embedding: {e}")
                break
        return []

    @classmethod
    def embed_documents(cls, texts: list, model_name: str = None, batch_size: int = 50) -> list:
        """Menghasilkan vector embeddings untuk kumpulan dokumen dalam potongan batch."""
        cls._ensure_configured()
        if not texts:
            return []

        clean_texts = [str(t).strip() for t in texts if t and str(t).strip()]
        if not clean_texts:
            return []

        cfg = SettingsManager.get_gemini_config()
        model_name = model_name or cfg.get("embedding_model", "gemini-embedding-001")
        model_target = f"models/{model_name}" if not model_name.startswith("models/") else model_name

        all_embeddings = []
        for i in range(0, len(clean_texts), batch_size):
            chunk = clean_texts[i:i + batch_size]
            success = False

            for attempt in range(2):
                _rate_limiter.wait_if_needed(model_target)
                try:
                    res = genai.embed_content(
                        model=model_target,
                        content=chunk,
                        task_type="retrieval_document",
                    )
                    if res and "embedding" in res:
                        emb = res["embedding"]
                        if emb and isinstance(emb[0], list):
                            all_embeddings.extend(emb)
                        elif emb and isinstance(emb[0], (int, float)):
                            all_embeddings.append(emb)
                        success = True
                        break
                except Exception as e:
                    err_str = str(e)
                    is_rate = "429" in err_str or "quota" in err_str.lower()
                    if is_rate and cls._switch_key_if_available(cls._configured_key or ""):
                        continue
                    if is_rate and attempt == 0:
                        time.sleep(5.0)
                        continue
                    logger.warning(f"Gagal batch embedding chunk {i//batch_size + 1}: {e}")
                    break

            if not success:
                # Fallback per-item jika panggilan batch gagal
                for item in chunk:
                    single_emb = cls.embed_text(item, model_name)
                    all_embeddings.append(single_emb if single_emb else None)

        return all_embeddings
