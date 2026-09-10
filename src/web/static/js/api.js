/**
 * Pemanggilan ke backend FastAPI dengan proteksi error & timeout.
 */
export async function ambilBeranda() {
  try {
    const resp = await fetch('/api/beranda');
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return await resp.json();
  } catch (err) {
    console.error('Fetch ambilBeranda error:', err);
    return { status: 'error', message: err.message };
  }
}

export async function ambilArsip() {
  try {
    const resp = await fetch('/api/arsip');
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return await resp.json();
  } catch (err) {
    console.error('Fetch ambilArsip error:', err);
    return { status: 'error', message: err.message, hari: [] };
  }
}

export async function ambilTren() {
  try {
    const resp = await fetch('/api/tren');
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return await resp.json();
  } catch (err) {
    console.error('Fetch ambilTren error:', err);
    return { status: 'error', message: err.message };
  }
}

export async function mulaiPipelineRequest() {
  try {
    const resp = await fetch('/api/run', { method: 'POST' });
    if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
    return await resp.json();
  } catch (err) {
    console.error('Fetch mulaiPipelineRequest error:', err);
    return { status: 'error', message: err.message };
  }
}

export async function batalkanPipelineRequest() {
  try {
    return await fetch('/api/cancel', { method: 'POST' });
  } catch (err) {
    console.error('Fetch batalkanPipelineRequest error:', err);
  }
}

export function bukaStreamLog(onPesan, onError) {
  const sumber = new EventSource('/api/stream');
  sumber.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      if (typeof onPesan === 'function') onPesan(data);
    } catch (e) {
      console.error('Error parsing SSE JSON:', e);
    }
  };
  sumber.onerror = (err) => {
    if (typeof onError === 'function') onError(err);
  };
  return sumber;
}