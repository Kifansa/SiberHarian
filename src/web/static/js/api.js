/**
 * Semua pemanggilan ke backend FastAPI dikumpulkan di sini - satu tempat,
 * supaya kalau ada perubahan endpoint nanti, tidak perlu cari-cari ke
 * banyak file berbeda.
 */
export async function ambilBeranda() {
  const resp = await fetch('/api/beranda');
  return resp.json();
}

export async function ambilArsip() {
  const resp = await fetch('/api/arsip');
  return resp.json();
}

export async function ambilTren() {
  const resp = await fetch('/api/tren');
  return resp.json();
}

export async function mulaiPipelineRequest() {
  const resp = await fetch('/api/run', { method: 'POST' });
  return resp.json();
}

export async function batalkanPipelineRequest() {
  return fetch('/api/cancel', { method: 'POST' });
}

export function bukaStreamLog(onPesan, onError) {
  const sumber = new EventSource('/api/stream');
  sumber.onmessage = (event) => onPesan(JSON.parse(event.data));
  sumber.onerror = () => onError();
  return sumber;
}