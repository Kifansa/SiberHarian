/**
 * Helper utilitas bersama untuk modul analitik tren SiberHarian
 */

/**
 * Melakukan sanitasi teks untuk mencegah XSS saat disisipkan ke HTML
 * @param {string} str 
 * @returns {string}
 */
export function escapeHtml(str) {
  if (!str) return '';
  return String(str).replace(/[&<>"']/g, match => {
    const map = { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#039;' };
    return map[match];
  });
}
