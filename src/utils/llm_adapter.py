from collections import deque
import os
import threading
import time
from typing import List, Optional, Set, Tuple

import google.generativeai as genai
from src.utils.logger import setup_logger
from src.utils.settings_manager import SettingsManager

logger = setup_logger(__name__)

DEFAULT_MODEL_CHAIN = [
    "gemini-2.5-flash",
    "gemini-2.5-flash-lite",
    "gemini-3-flash",
    "gemini-3.1-flash-lite",
    "gemini-3.6-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.8-flash",
]

DEFAULT_TIMEOUT_DETIK = 10.0

DEFAULT_EMBEDDING_MODEL = "gemini-embedding-001"
DEFAULT_EMBEDDING_FALLBACK_MODELS = [
    "gemini-embedding-exp-03-07",
    "text-embedding-004",
]

# Quota limit (RPM) resmi dari Google AI Studio sesuai konfigurasi kuota pengguna
QUOTA_RPM_MAP: dict[str, float] = {
    # 2 Model Embedding Google Gemini Resmi (100 RPM)
    "gemini-embedding-001": 100.0,
    "gemini-embedding-exp-03-07": 100.0,
    "text-embedding-004": 100.0,
    # 7 Model Narasi resmi Google Gemini
    "gemini-2.5-flash": 5.0,
    "gemini-2.5-flash-lite": 10.0,
    "gemini-3-flash": 5.0,
    "gemini-3.1-flash-lite": 15.0,
    "gemini-3.6-flash": 5.0,
    "gemini-3.5-flash-lite": 15.0,
    "gemini-3.8-flash": 5.0,
}

# Ambang batas pergantian proaktif (90% - 95% dari kuota RPM)
PROACTIVE_THRESHOLD_MAP: dict[str, int] = {
    # Embedding 100 RPM: proaktif switch pada 90-95 calls/min (threshold 90)
    "gemini-embedding-001": 90,
    "gemini-embedding-exp-03-07": 90,
    "text-embedding-004": 90,
    # 7 Model Narasi:
    "gemini-2.5-flash": 4,          # 4 / 5 RPM
    "gemini-2.5-flash-lite": 9,     # 9 / 10 RPM (90%)
    "gemini-3-flash": 4,            # 4 / 5 RPM
    "gemini-3.1-flash-lite": 14,    # 14 / 15 RPM (93.3%)
    "gemini-3.6-flash": 4,          # 4 / 5 RPM
    "gemini-3.5-flash-lite": 14,    # 14 / 15 RPM (93.3%)
    "gemini-3.8-flash": 4,          # 4 / 5 RPM
}


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

    def get_all_keys(self) -> List[str]:
        with self._lock:
            return list(self._keys)

    def set_active_key(self, key: str) -> None:
        with self._lock:
            if key in self._keys:
                self._current_index = self._keys.index(key)

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

    def _get_history_key(self, model_name: str, api_key: str = "") -> str:
        clean_model = model_name.replace("models/", "").strip().lower()
        key_id = api_key[-8:] if api_key and len(api_key) >= 8 else (api_key or "default")
        return f"{key_id}:{clean_model}"

    def get_quota_rpm(self, model_name: str) -> float:
        clean_model = model_name.replace("models/", "").strip().lower()
        try:
            from src.utils.settings_manager import SettingsManager
            cfg = SettingsManager.get_gemini_config()
            rate_limits = cfg.get("rate_limits") or {}
            if clean_model in rate_limits:
                return float(rate_limits[clean_model])
            for k in sorted(rate_limits.keys(), key=len, reverse=True):
                if k.lower() in clean_model:
                    return float(rate_limits[k])
        except Exception:
            pass

        if clean_model in QUOTA_RPM_MAP:
            return QUOTA_RPM_MAP[clean_model]
        # Urutkan berdasarkan panjang kunci terpanjang agar nama spesifik seperti 'flash-lite' mendahului 'flash'
        for k in sorted(QUOTA_RPM_MAP.keys(), key=len, reverse=True):
            if k in clean_model:
                return QUOTA_RPM_MAP[k]
        if "embedding" in clean_model:
            return 100.0
        if "lite" in clean_model:
            return 10.0
        return 5.0

    def get_proactive_threshold(self, model_name: str) -> int:
        clean_model = model_name.replace("models/", "").strip().lower()
        try:
            from src.utils.settings_manager import SettingsManager
            cfg = SettingsManager.get_gemini_config()
            thresholds = cfg.get("proactive_thresholds") or {}
            if clean_model in thresholds:
                return int(thresholds[clean_model])
            for k in sorted(thresholds.keys(), key=len, reverse=True):
                if k.lower() in clean_model:
                    return int(thresholds[k])
        except Exception:
            pass

        if clean_model in PROACTIVE_THRESHOLD_MAP:
            return PROACTIVE_THRESHOLD_MAP[clean_model]
        for k in sorted(PROACTIVE_THRESHOLD_MAP.keys(), key=len, reverse=True):
            if k in clean_model:
                return PROACTIVE_THRESHOLD_MAP[k]
        quota = self.get_quota_rpm(model_name)
        return max(1, int(quota * 0.9))

    def _get_model_rpm_limit(self, model_name: str) -> float:
        name = model_name.lower()
        if "embedding" in name:
            return 80.0
        if "3.5-flash-lite" in name or "lite" in name:
            return 12.0
        return 4.0

    def record_call(self, model_name: str, api_key: str = "") -> None:
        h_key = self._get_history_key(model_name, api_key)
        now = time.time()
        with self._lock:
            if h_key not in self._history:
                self._history[h_key] = deque()
            self._history[h_key].append(now)
            self._last_call[h_key] = now

    def get_recent_call_count(self, model_name: str, api_key: str = "") -> int:
        h_key = self._get_history_key(model_name, api_key)
        now = time.time()
        with self._lock:
            if h_key not in self._history:
                return 0
            dq = self._history[h_key]
            while dq and now - dq[0] > 60.0:
                dq.popleft()
            return len(dq)

    def is_model_near_limit(self, model_name: str, api_key: str = "") -> bool:
        threshold = self.get_proactive_threshold(model_name)
        count = self.get_recent_call_count(model_name, api_key)
        return count >= threshold

    def saturate_model(self, model_name: str, api_key: str = "") -> None:
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

    def get_wait_time_seconds(self, model_name: str, api_key: str = "") -> float:
        h_key = self._get_history_key(model_name, api_key)
        now = time.time()
        with self._lock:
            if h_key not in self._history:
                return 0.0
            dq = self._history[h_key]
            while dq and now - dq[0] > 60.0:
                dq.popleft()
            threshold = self.get_proactive_threshold(model_name)
            if len(dq) >= threshold and dq:
                oldest = dq[0]
                wait = (oldest + 60.0) - now + 0.2
                return max(0.0, wait)
            return 0.0

    def select_available_slot(
        self,
        candidate_models: List[str],
        key_pool: APIKeyPool,
        unavailable_models: Optional[Set[str]] = None,
    ) -> Tuple[Optional[str], Optional[str], float]:
        """
        Memilih pasangan (api_key, model) yang belum mencapai batas ambang 90%-95% RPM.
        Urutan prioritas:
        1. Model pertama yang aman pada API Key saat ini.
        2. Jika semua model pada API Key saat ini mendekati batas, ganti ke API Key cadangan.
        3. Jika seluruh model pada semua API Key mendekati batas, hitung waktu tunggu minimum (graceful waiting).
        """
        if unavailable_models is None:
            unavailable_models = set()

        all_keys = key_pool.get_all_keys()
        active_k = key_pool.get_active_key()
        if not all_keys:
            all_keys = [active_k] if active_k else [""]

        # Pastikan active_key dicoba lebih dulu
        ordered_keys = []
        if active_k and active_k in all_keys:
            ordered_keys.append(active_k)
        for k in all_keys:
            if k not in ordered_keys:
                ordered_keys.append(k)

        now = time.time()
        # 1 & 2: Cek ketersediaan model per key
        for k in ordered_keys:
            with key_pool._lock:
                if key_pool._cooldowns.get(k, 0) > now:
                    continue

            for model_name in candidate_models:
                clean_m = model_name.replace("models/", "").strip()
                if clean_m in unavailable_models or model_name in unavailable_models:
                    continue

                if not self.is_model_near_limit(clean_m, k):
                    return k, model_name, 0.0

        # 3: Jika seluruh model pada seluruh key mendekati limit, hitung waktu tunggu minimum
        min_wait = 60.0
        found_wait = False
        for k in ordered_keys:
            for model_name in candidate_models:
                clean_m = model_name.replace("models/", "").strip()
                if clean_m in unavailable_models or model_name in unavailable_models:
                    continue
                w = self.get_wait_time_seconds(clean_m, k)
                if w > 0:
                    found_wait = True
                    if w < min_wait:
                        min_wait = w

        if not found_wait or min_wait <= 0:
            min_wait = 1.0

        return None, None, min_wait

    def wait_if_needed(self, model_name: str, api_key: str = "") -> None:
        """Paces API calls to stay strictly under the model's RPM limit."""
        clean_model = model_name.replace("models/", "").strip()
        safe_rpm = self._get_model_rpm_limit(clean_model)
        min_interval = 60.0 / safe_rpm
        h_key = self._get_history_key(clean_model, api_key)

        with self._lock:
            if h_key not in self._history:
                self._history[h_key] = deque()
            history = self._history[h_key]

            now = time.time()
            while history and now - history[0] > 60.0:
                history.popleft()

            sleep_time = 0.0
            if len(history) >= safe_rpm:
                oldest = history[0]
                sleep_time = max(sleep_time, (oldest + 60.0) - now + 0.2)

            last_call = self._last_call.get(h_key, 0.0)
            elapsed = now - last_call
            if elapsed < min_interval:
                sleep_time = max(sleep_time, min_interval - elapsed)

        if sleep_time > 0.0:
            logger.debug(f"Pacing {clean_model}: menunggu {sleep_time:.2f} detik sesuai batas safe RPM ({safe_rpm:.0f} RPM).")
            time.sleep(sleep_time)

        with self._lock:
            post_now = time.time()
            self._history[h_key].append(post_now)
            self._last_call[h_key] = post_now


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

        raw_chain = cfg.get("model_chain") or DEFAULT_MODEL_CHAIN
        model_chain = [m.strip() for m in raw_chain if m and str(m).strip()]
        # Pastikan model produksi resmi Google Gemini selalu ada sebagai cadangan failover
        for fallback_m in DEFAULT_MODEL_CHAIN:
            if fallback_m not in model_chain:
                model_chain.append(fallback_m)

        unavailable_models = set()
        max_attempts = len(model_chain) * max(1, _key_pool.total_keys()) + 3

        for attempt in range(max_attempts):
            selected_key, selected_model, wait_sec = _rate_limiter.select_available_slot(
                candidate_models=model_chain,
                key_pool=_key_pool,
                unavailable_models=unavailable_models,
            )

            if not selected_key or not selected_model:
                # Seluruh model narasi pada seluruh API Key mendekati batas kuota (90%-95% RPM)
                logger.warning(
                    f"Seluruh model narasi pada semua API Key mendekati limit kuota (90%-95% RPM). "
                    f"Sistem menunggu secara anggun (graceful waiting) selama {wait_sec:.1f} detik..."
                )
                time.sleep(min(wait_sec, 60.0))
                continue

            if selected_key and selected_key != cls._configured_key:
                _key_pool.set_active_key(selected_key)
                genai.configure(api_key=selected_key)
                cls._configured_key = selected_key

            _rate_limiter.wait_if_needed(selected_model, selected_key)
            try:
                model = genai.GenerativeModel(
                    model_name=selected_model,
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
                _rate_limiter.record_call(selected_model, selected_key)
                if response and response.text:
                    logger.info(f"LLM OK via {selected_model}")
                    return response.text.strip()
            except Exception as e:
                err_str = str(e)
                if "404" in err_str or "not found" in err_str.lower():
                    logger.warning(f"Model {selected_model} tidak ditemukan di Google API (404), langsung beralih ke model berikutnya.")
                    unavailable_models.add(selected_model)
                    continue

                is_rate_limit = (
                    "429" in err_str
                    or "quota" in err_str.lower()
                    or "resourceexhausted" in err_str.lower()
                )

                if is_rate_limit:
                    logger.warning(f"Model {selected_model} terkena limit kuota (429), menandai model jenuh untuk beralih model/key.")
                    _rate_limiter.saturate_model(selected_model, selected_key or "")
                    continue

                logger.warning(f"Model {selected_model} gagal: {e}, mencoba alternatif berikutnya...")
                unavailable_models.add(selected_model)

        logger.error("Semua model Gemini gagal atau kuota API key habis.")
        return ""

    @classmethod
    def reload_config(cls) -> None:
        cls._configured = False
        cls._configured_key = None

    @classmethod
    def get_key_status(cls) -> dict:
        """Mengembalikan jumlah key dan indeks key yang sedang aktif tanpa menulis log."""
        cfg = SettingsManager.get_gemini_config()
        raw_key = cfg.get("api_key", "")
        if isinstance(raw_key, list):
            keys = [str(k).strip() for k in raw_key if str(k).strip()]
        elif isinstance(raw_key, str) and raw_key.strip():
            keys = [
                k.strip()
                for k in raw_key.replace("\r\n", "\n").replace("\n", ",").split(",")
                if k.strip()
            ]
        else:
            keys = []

        pool_keys = _key_pool.get_all_keys()
        active_key = _key_pool.get_active_key() if pool_keys else (keys[0] if keys else None)
        if active_key in keys:
            active_index = keys.index(active_key)
        else:
            active_index = 0 if keys else -1

        return {
            "total_keys": len(keys),
            "active_api_key_index": active_index,
            "active_api_key": active_key,
        }

    @classmethod
    def _get_embedding_chain(cls, requested_model: Optional[str] = None) -> List[str]:
        cfg = SettingsManager.get_gemini_config()
        configured_primary = cfg.get("embedding_model", DEFAULT_EMBEDDING_MODEL)
        fallback = cfg.get("embedding_model_fallback", DEFAULT_EMBEDDING_FALLBACK_MODELS)

        chain = []
        if requested_model and str(requested_model).strip():
            chain.append(str(requested_model).strip())
        if configured_primary and configured_primary not in chain:
            chain.append(configured_primary)

        fallback_list = []
        if isinstance(fallback, str):
            fallback_list = [f.strip() for f in fallback.replace("\n", ",").split(",") if f.strip()]
        elif isinstance(fallback, (list, tuple)):
            fallback_list = [str(f).strip() for f in fallback if str(f).strip()]

        for m in fallback_list:
            if m and m not in chain:
                chain.append(m)

        return chain

    @classmethod
    def embed_text(cls, text: str, model_name: str = None) -> list:
        cls._ensure_configured()
        if not text or not str(text).strip():
            return []

        models_to_try = cls._get_embedding_chain(model_name)
        unavailable_models = set()
        max_attempts = len(models_to_try) * max(1, _key_pool.total_keys()) + 3

        for attempt in range(max_attempts):
            selected_key, selected_model, wait_sec = _rate_limiter.select_available_slot(
                candidate_models=models_to_try,
                key_pool=_key_pool,
                unavailable_models=unavailable_models,
            )

            if not selected_key or not selected_model:
                logger.warning(
                    f"Seluruh model embedding pada semua API Key mendekati ambang 90%-95% (kuota 100 RPM). "
                    f"Sistem menunggu secara anggun selama {wait_sec:.1f} detik..."
                )
                time.sleep(min(wait_sec, 60.0))
                continue

            if selected_key and selected_key != cls._configured_key:
                _key_pool.set_active_key(selected_key)
                genai.configure(api_key=selected_key)
                cls._configured_key = selected_key

            model_target = f"models/{selected_model}" if not selected_model.startswith("models/") else selected_model
            _rate_limiter.wait_if_needed(model_target, selected_key)
            try:
                res = genai.embed_content(
                    model=model_target,
                    content=str(text).strip(),
                    task_type="retrieval_query",
                )
                _rate_limiter.record_call(selected_model, selected_key)
                if res and "embedding" in res:
                    return res["embedding"]
            except Exception as e:
                err_str = str(e)
                if "404" in err_str or "not found" in err_str.lower():
                    logger.warning(f"Model embedding {selected_model} tidak ditemukan di Google API (404), langsung beralih ke model fallback...")
                    unavailable_models.add(selected_model)
                    continue
                is_rate = "429" in err_str or "quota" in err_str.lower() or "resourceexhausted" in err_str.lower()
                if is_rate:
                    logger.warning(f"Model embedding {selected_model} terkena limit kuota (429), menandai model jenuh untuk beralih model/key.")
                    _rate_limiter.saturate_model(selected_model, selected_key or "")
                    continue
                logger.warning(f"Gagal generate vector embedding dengan {selected_model}: {e}")
                unavailable_models.add(selected_model)

        logger.error("Semua model embedding Gemini gagal.")
        return []

    @classmethod
    def embed_documents(cls, texts: list, model_name: str = None, batch_size: int = 50) -> list:
        """Menghasilkan vector embeddings untuk kumpulan dokumen dalam potongan batch dengan fallback otomatis."""
        cls._ensure_configured()
        if not texts:
            return []

        clean_texts = [str(t).strip() for t in texts if t and str(t).strip()]
        if not clean_texts:
            return []

        models_to_try = cls._get_embedding_chain(model_name)

        for model_cand in models_to_try:
            model_target = f"models/{model_cand}" if not model_cand.startswith("models/") else model_cand
            all_embeddings = []
            model_failed = False

            for i in range(0, len(clean_texts), batch_size):
                chunk = clean_texts[i:i + batch_size]
                chunk_success = False

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
                            chunk_success = True
                            break
                    except Exception as e:
                        err_str = str(e)
                        is_rate = "429" in err_str or "quota" in err_str.lower() or "resourceexhausted" in err_str.lower()
                        if is_rate and cls._switch_key_if_available(cls._configured_key or ""):
                            continue
                        if is_rate and attempt == 0:
                            time.sleep(5.0)
                            continue
                        logger.warning(f"Gagal batch embedding chunk {i//batch_size + 1} dengan {model_cand}: {e}")
                        break

                if not chunk_success:
                    model_failed = True
                    break

            if not model_failed and len(all_embeddings) == len(clean_texts):
                return all_embeddings

            logger.warning(f"Batch embedding dengan {model_cand} gagal, mencoba model fallback berikutnya...")

        # Fallback per-item jika seluruh pemanggilan batch gagal
        logger.warning("Batch embedding semua model gagal, mencoba per-item fallback...")
        item_embeddings = []
        for item in clean_texts:
            single_emb = cls.embed_text(item, model_name)
            item_embeddings.append(single_emb if single_emb else None)

        return item_embeddings
