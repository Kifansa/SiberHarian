"""Sesi HMAC, token CSRF, dan otorisasi admin panel web."""

import hashlib
import hmac
import os
from typing import Optional

from fastapi import Request, Response
from fastapi.responses import JSONResponse

from src.utils.logger import setup_logger

logger = setup_logger(__name__)

SESSION_COOKIE = "cti_session"
CSRF_COOKIE = "cti_csrf"
CSRF_HEADER = "X-CSRF-Token"
SESSION_MAX_AGE = 86400 * 7


def session_secret() -> str:
    """Mengembalikan SESSION_SECRET; gagal keras bila tidak dikonfigurasi."""
    secret = os.getenv("SESSION_SECRET", "")
    if not secret.strip():
        raise RuntimeError(
            "SESSION_SECRET wajib diisi di environment sebelum aplikasi web dijalankan."
        )
    return secret


def validasi_keamanan_startup() -> None:
    """Memvalidasi konfigurasi keamanan wajib saat aplikasi mulai."""
    secret = session_secret()
    if len(secret) < 32:
        logger.warning(
            "SESSION_SECRET kurang dari 32 karakter; gunakan nilai acak yang lebih panjang."
        )


def buat_token_sesi(username: str) -> str:
    """Membuat cookie sesi bertanda tangan HMAC untuk username."""
    sig = hmac.new(
        session_secret().encode(), username.encode(), hashlib.sha256
    ).hexdigest()
    return f"{username}:{sig}"


def ambil_user_dari_sesi(request: Request) -> Optional[dict]:
    """Memvalidasi cookie sesi dan mengembalikan data admin aktif."""
    cookie = request.cookies.get(SESSION_COOKIE)
    if not cookie or ":" not in cookie:
        return None
    username, sig = cookie.split(":", 1)
    expected_sig = hmac.new(
        session_secret().encode(), username.encode(), hashlib.sha256
    ).hexdigest()
    if not hmac.compare_digest(sig, expected_sig):
        return None

    from src.utils.admin_auth import get_admin_user

    return get_admin_user(username)


def cek_admin_autentikasi(request: Request) -> bool:
    """True bila request memiliki sesi admin yang valid."""
    return ambil_user_dari_sesi(request) is not None


def cek_superadmin_autentikasi(request: Request) -> bool:
    """True bila request memiliki sesi superadmin yang valid."""
    user = ambil_user_dari_sesi(request)
    return user is not None and user.get("role") == "superadmin"


def buat_token_csrf(token_sesi: str) -> str:
    """Menurunkan token CSRF dari cookie sesi sehingga terikat pada sesi."""
    return hmac.new(
        session_secret().encode(),
        f"csrf:{token_sesi}".encode(),
        hashlib.sha256,
    ).hexdigest()


def token_csrf_request(request: Request) -> str:
    """Mengembalikan token CSRF yang berlaku untuk sesi request ini."""
    cookie = request.cookies.get(SESSION_COOKIE, "")
    return buat_token_csrf(cookie) if cookie else ""


def verifikasi_csrf(request: Request) -> bool:
    """Memeriksa header X-CSRF-Token terhadap token turunan sesi."""
    cookie = request.cookies.get(SESSION_COOKIE, "")
    header = request.headers.get(CSRF_HEADER, "")
    if not cookie or not header:
        return False
    return hmac.compare_digest(header, buat_token_csrf(cookie))


def pasang_cookie_sesi(response: Response, username: str) -> str:
    """Memasang cookie sesi HttpOnly dan cookie CSRF yang dapat dibaca UI."""
    token = buat_token_sesi(username)
    response.set_cookie(
        key=SESSION_COOKIE,
        value=token,
        httponly=True,
        max_age=SESSION_MAX_AGE,
        samesite="lax",
    )
    response.set_cookie(
        key=CSRF_COOKIE,
        value=buat_token_csrf(token),
        httponly=False,
        max_age=SESSION_MAX_AGE,
        samesite="lax",
    )
    return token


def hapus_cookie_sesi(response: Response) -> None:
    """Menghapus cookie sesi dan CSRF."""
    response.delete_cookie(key=SESSION_COOKIE)
    response.delete_cookie(key=CSRF_COOKIE)


def tolak_autentikasi() -> JSONResponse:
    """Respons standar untuk request tanpa sesi admin."""
    return JSONResponse(
        {"status": "error", "message": "Akses ditolak: Autentikasi diperlukan."},
        status_code=401,
    )


def tolak_superadmin() -> JSONResponse:
    """Respons standar untuk sesi admin yang bukan superadmin."""
    return JSONResponse(
        {"status": "error", "message": "Akses ditolak: Hanya superadmin yang dapat mengakses pengaturan."},
        status_code=403,
    )


def tolak_csrf() -> JSONResponse:
    """Respons standar untuk token CSRF yang hilang atau tidak cocok."""
    return JSONResponse(
        {"status": "error", "message": "Akses ditolak: Token CSRF tidak valid."},
        status_code=403,
    )


def wajib_superadmin(request: Request) -> Optional[JSONResponse]:
    """Mengembalikan respons error bila sesi bukan superadmin atau CSRF gagal."""
    if not cek_admin_autentikasi(request):
        return tolak_autentikasi()
    if not cek_superadmin_autentikasi(request):
        return tolak_superadmin()
    if not verifikasi_csrf(request):
        return tolak_csrf()
    return None
