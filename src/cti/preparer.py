"""
Modul CTI Data Preparation & Relational/Document Storage.

Melakukan transformasi dan persiapan data dari berkas mentah staging:
1. Perataan MITRE ATT&CK STIX 2.1: Memfilter hanya attack-pattern aktif (membuang revoked/deprecated).
2. Pembangkitan Dokumen Taksonomi Insiden: 11 kategori tertutup berpemetaan ke induk eCSIRT.
3. Ingesti D3FEND Relasional: Menyimpan teknik & relasi pemetaan ke SQLite data/state.db (strictly non-vector).
4. Perataan Katalog NIST OSCAL: Mengekstraksi kontrol SP 800-53 Rev 5 dan subkategori CSF 2.0.
"""

import os
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple, Set

from src.storage.db import (
    DEFAULT_DB_PATH,
    simpan_d3fend_techniques,
    simpan_d3fend_attack_mappings,
    ambil_d3fend_mitigasi_by_attack_id,
)
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

DEFAULT_RAW_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
DEFAULT_PREPARED_DIR = Path(__file__).resolve().parents[2] / "data" / "prepared"

# Definisi 11 Kategori Tertutup Taksonomi Insiden Siber
CLOSED_11_TAXONOMY_CATEGORIES = [
    "ransomware",
    "data_breach",
    "ddos",
    "defacement",
    "phishing_penipuan",
    "malware",
    "eksploitasi_kerentanan",
    "akses_tidak_sah",
    "pelecehan_konten",
    "lainnya",
    "tidak_dapat_ditentukan",
]

TAXONOMY_DISPLAY_NAMES = {
    "ransomware": "Ransomware",
    "data_breach": "Data Breach / Kebocoran Data",
    "ddos": "DDoS / Gangguan Ketersediaan",
    "defacement": "Web Defacement",
    "phishing_penipuan": "Phishing / Penipuan Siber",
    "malware": "Malware / Infostealer",
    "eksploitasi_kerentanan": "Eksploitasi Kerentanan (Exploit / Zero-Day)",
    "akses_tidak_sah": "Akses Tidak Sah / Pembobolan Akun",
    "pelecehan_konten": "Pelecehan / Konten Berbahaya",
    "lainnya": "Lainnya",
    "tidak_dapat_ditentukan": "Tidak Dapat Ditentukan",
}

ECSIRT_PARENT_MAPPINGS = {
    "ransomware": "malicious-code:ransomware",
    "data_breach": "information-content-security:unauthorized-information-access",
    "ddos": "availability:ddos",
    "defacement": "intrusions:defacement",
    "phishing_penipuan": "fraud:phishing",
    "malware": "malicious-code:malware",
    "eksploitasi_kerentanan": "intrusion-attempts:ids-alert",
    "akses_tidak_sah": "intrusions:account-compromise",
    "pelecehan_konten": "abusive-content:spam",
    "lainnya": "other:other",
    "tidak_dapat_ditentukan": "other:unspecified",
}

TAXONOMY_DEFINITIONS = {
    "ransomware": (
        "Serangan perangkat lunak jahat (ransomware) yang menyandera, mengeksekusi enkripsi data, "
        "basis data, atau sistem server, disertai tuntutan uang tebusan (ransom) untuk kunci pemulihan."
    ),
    "data_breach": (
        "Akses ilegal, eksfiltrasi, penjualan, pembocoran, atau distribusi tanpa hak atas data sensitif, "
        "rahasia instansi, data pribadi kependudukan (PII), atau catatan basis data internal ke publik/forum gelap."
    ),
    "ddos": (
        "Serangan penolakan layanan (Distributed Denial of Service / DoS) yang membanjiri kapasitas trafik jaringan, "
        "banderol bandwidth, atau sumber daya pemrosesan server sehingga layanan publik atau portal web tidak dapat diakses."
    ),
    "defacement": (
        "Tindakan peretasan tanpa hak yang mengubah tampilan visual, indeks halaman muka, atau menyisipkan berkas/konten "
        "terlarang (seperti tautan promosi judi online/slot gacor, konten politik, atau pesan kelompok peretas) pada situs web resmi."
    ),
    "phishing_penipuan": (
        "Rekayasa sosial berbasis komunikasi digital (email phishing, tautan login palsu, file APK manipulatif via WhatsApp, "
        "spoofing domain instansi) untuk mengelabui korban agar membocorkan kredensial, OTP, atau mentransfer aset keuangan."
    ),
    "malware": (
        "Penyusupan dan infeksi perangkat/server oleh perangkat lunak berbahaya selain ransomware, mencakup trojan, "
        "infostealer, botnet drone, spyware, keylogger, worm, atau backdoor untuk spionase siber dan pencurian data."
    ),
    "eksploitasi_kerentanan": (
        "Pemanfaatan celah keamanan sistem perangkat lunak, sistem operasi, pustaka dependensi, atau perangkat keras "
        "(termasuk CVE terpublikasi, kelemahan Remote Code Execution / RCE, SQL Injection, Zero-Day exploit) untuk menembus perimeter."
    ),
    "akses_tidak_sah": (
        "Pengambilalihan akun berwenang, pembajakan kredensial (credential stuffing/brute force), eskalasi hak akses "
        "(privilege escalation), atau penyusupan internal ke dalam sistem/jaringan tertutup tanpa izin sah."
    ),
    "pelecehan_konten": (
        "Penyalahgunaan infrastruktur komunikasi digital untuk transmisi pesan spam berskala masif, penyebaran disinformasi "
        "terkoordinasi, intimidasi/doxing siber, atau penyebaran materi berbahaya/terlarang."
    ),
    "lainnya": (
        "Insiden keamanan siber faktual lainnya yang secara jelas merupakan insiden keamanan informasi namun tidak dapat "
        "dikelompokkan ke dalam 9 kategori spesifik di atas (misal anomali konfigurasi keamanan, sabotase fisik TI)."
    ),
    "tidak_dapat_ditentukan": (
        "Berita atau artikel tidak memuat bukti faktual yang memadai mengenai jenis serangan siber, atau hanya membahas "
        "regulasi umum, seremonial, opini, maupun informasi non-insiden sehingga klasifikasi teknis tidak dapat ditentukan."
    ),
}

TAXONOMY_REPRESENTATIVE_EXAMPLES = {
    "ransomware": [
        "Pusat Data Nasional Sementara (PDNS) mengalami kelumpuhan akibat serangan ransomware Brain Cipher / LockBit 3.0.",
        "Sistem informasi rumah sakit daerah disandera ransomware dan pelaku menuntut tebusan mata uang kripto.",
    ],
    "data_breach": [
        "Jutaan data registrasi SIM card dan data kependudukan diduga bocor dan dijual di forum BreachForums.",
        "Aktor ancaman mengklaim membobol basis data kepegawaian dan merilis sampel data NIK ke publik.",
    ],
    "ddos": [
        "Situs pendaftaran seleksi calon aparatur sipil negara tumbang akibat lonjakan trafik anomali serangan SYN flood DDoS.",
        "Layanan perbankan digital tidak dapat diakses nasabah selama beberapa jam akibat serangan saturasi DNS amplification.",
    ],
    "defacement": [
        "Subdomain resmi pemerintah daerah diubah tampilannya menjadi situs promosi judi slot gacor online.",
        "Halaman beranda portal dinas pendidikan diretas menampilkan pesan protes terhadap kebijakan daerah.",
    ],
    "phishing_penipuan": [
        "Penyebaran undangan pernikahan digital atau tagihan palsu berformat file APK yang menguras rekening korban.",
        "Email mengatasnamakan pimpinan dinas beredar meminta staf melakukan login pada tautan webmail palsu.",
    ],
    "malware": [
        "Perangkat komputer pegawai terinfeksi malware infostealer RedLine yang mencuri sesi cookies browser dan password tersimpan.",
        "Penyusupan malware Mirai memanfaatkan botnet router untuk kampanye serangan siber lanjutan.",
    ],
    "eksploitasi_kerentanan": [
        "Peretas menembus portal SIMPEG Pemprov melalui eksploitasi kerentanan kritis Apache Log4j (Log4Shell / CVE-2021-44228).",
        "Eksploitasi zero-day pada modul upload aplikasi layanan publik memungkinkan injeksi arbitrary file upload.",
    ],
    "akses_tidak_sah": [
        "Akun administrator portal kepegawaian dibobol pihak luar menggunakan teknik credential stuffing.",
        "Pelaku menyusup ke active directory instansi menggunakan kredensial default yang belum diganti.",
    ],
    "pelecehan_konten": [
        "Kampanye spam email massal membanjiri mail server pemda dengan ribuan pesan promosi gelap.",
        "Operasi disinformasi siber terkoordinasi memanfaatkan bot media sosial mencemarkan institusi layanan publik.",
    ],
    "lainnya": [
        "Kesalahan miskonfigurasi bucket penyimpanan cloud internal yang sempat terbuka tanpa autentikasi.",
        "Kerusakan perangkat keras firewall akibat gangguan pasokan daya cadangan data center.",
    ],
    "tidak_dapat_ditentukan": [
        "Dinas Kominfo menggelar bimbingan teknis literasi keamanan informasi bagi ASN di lingkungan pemprov.",
        "Kunjungan kerja Komisi I DPRD membahas kesiapan infrastruktur Smart City Jawa Timur.",
    ],
}


class InvalidTaxonomyError(ValueError):
    """Exception dilempar saat kategori taksonomi di luar 11 daftar tertutup."""
    pass


# =============================================================================
# Definisi 10 Sektor Infrastruktur Informasi Vital (IIV) Perpres 82/2022 Pasal 4
# =============================================================================
CLOSED_10_IIV_SECTORS = [
    "Administrasi Pemerintahan",
    "Energi & Sumber Daya Mineral",
    "Transportasi",
    "Keuangan & Perbankan",
    "Kesehatan",
    "Teknologi Informasi & Komunikasi (TIK)",
    "Pertahanan & Keamanan",
    "Pangan",
    "Pendidikan",
    "Layanan Publik & Pengguna Digital",
    "Tidak dapat ditentukan",
]

IIV_SECTOR_DISPLAY_NAMES = {
    "Administrasi Pemerintahan": "Administrasi Pemerintahan",
    "Energi & Sumber Daya Mineral": "Energi & Sumber Daya Mineral",
    "Transportasi": "Transportasi",
    "Keuangan & Perbankan": "Keuangan & Perbankan",
    "Kesehatan": "Kesehatan",
    "Teknologi Informasi & Komunikasi (TIK)": "Teknologi Informasi & Komunikasi (TIK)",
    "Pertahanan & Keamanan": "Pertahanan & Keamanan",
    "Pangan": "Pangan",
    "Pendidikan": "Pendidikan",
    "Layanan Publik & Pengguna Digital": "Layanan Publik & Pengguna Digital",
    "Tidak dapat ditentukan": "Tidak Dapat Ditentukan",
}


class InvalidSectorError(ValueError):
    """Exception dilempar saat sektor sasaran di luar 10 IIV Perpres 82/2022 + fallback."""
    pass


class CTIPreparer:
    """
    Engine persiapan data CTI untuk meratakan dan menstrukturkan payload sumber resmi.
    """

    def __init__(
        self,
        raw_base_dir: Path = DEFAULT_RAW_DIR,
        prepared_base_dir: Path = DEFAULT_PREPARED_DIR,
        db_path: Path = DEFAULT_DB_PATH,
    ):
        self.raw_base_dir = Path(raw_base_dir)
        self.prepared_base_dir = Path(prepared_base_dir)
        self.db_path = Path(db_path)

    # -------------------------------------------------------------------------
    # 1. MITRE ATT&CK STIX 2.1 Flattener
    # -------------------------------------------------------------------------
    @staticmethod
    def flatten_attack_stix(
        stix_input: Any, source_version: str = "v20.0"
    ) -> List[Dict[str, Any]]:
        """
        Meratakan STIX 2.1 bundle ATT&CK Enterprise menjadi dokumen teks terstruktur per teknik.
        Menyaring ketat:
        - Hanya objek type == 'attack-pattern'
        - Membuang yang revoked == True
        - Membuang yang x_mitre_deprecated == True
        """
        if isinstance(stix_input, (str, Path)):
            stix_path = Path(stix_input)
            if not stix_path.exists():
                raise FileNotFoundError(f"Berkas bundle STIX tidak ditemukan: {stix_path}")
            with open(stix_path, "r", encoding="utf-8") as f:
                bundle = json.load(f)
        elif isinstance(stix_input, dict):
            bundle = stix_input
        else:
            raise TypeError("stix_input harus berupa Path berkas atau dict bundle JSON")

        if bundle.get("type") != "bundle":
            raise ValueError("Payload STIX tidak valid: root type bukan 'bundle'")

        # Deteksi versi bundle jika ada
        objects = bundle.get("objects", [])
        for obj in objects:
            if obj.get("type") == "x-mitre-collection" and "x_mitre_version" in obj:
                source_version = f"v{obj['x_mitre_version']}"
                break

        ingest_date = datetime.now(timezone.utc).isoformat()
        flattened_techniques: List[Dict[str, Any]] = []

        for obj in objects:
            if obj.get("type") != "attack-pattern":
                continue

            # Buang revoked & deprecated
            if obj.get("revoked", False):
                continue
            if obj.get("x_mitre_deprecated", False):
                continue

            # Ekstrak Technique ID (T-number) dari external_references
            technique_id = None
            for ref in obj.get("external_references", []):
                if ref.get("source_name") == "mitre-attack":
                    technique_id = ref.get("external_id")
                    break

            if not technique_id:
                continue

            # Ekstrak Taktik dari kill_chain_phases
            tactics = []
            for kc in obj.get("kill_chain_phases", []):
                if kc.get("kill_chain_name") == "mitre-attack":
                    tactics.append(kc.get("phase_name"))

            name = obj.get("name", "").strip()
            description = obj.get("description", "").strip()
            platforms = obj.get("x_mitre_platforms", [])
            is_subtechnique = bool(obj.get("x_mitre_is_subtechnique", False))
            original_id = obj.get("id", "")

            flattened_techniques.append({
                "technique_id": technique_id,
                "name": name,
                "tactics": tactics,
                "description": description,
                "platforms": platforms,
                "is_subtechnique": is_subtechnique,
                "revoked": False,
                "deprecated": False,
                "metadata": {
                    "source": "mitre-attack",
                    "source_version": source_version,
                    "original_id": original_id,
                    "ingest_date": ingest_date,
                },
            })

        logger.info(
            f"STIX Flattener selesai: Berhasil memproses {len(flattened_techniques)} teknik ATT&CK Enterprise aktif (versi {source_version})."
        )
        return flattened_techniques

    @staticmethod
    def format_attack_document_text(technique: Dict[str, Any]) -> str:
        """Membuat representasi teks dokumen teknik ATT&CK untuk indeks RAG."""
        tactics_str = ", ".join(technique.get("tactics", [])) or "Umum"
        platforms_str = ", ".join(technique.get("platforms", [])) or "Semua Platform"
        return (
            f"[TEKNIK MITRE ATT&CK]\n"
            f"ID: {technique.get('technique_id')}\n"
            f"Nama: {technique.get('name')}\n"
            f"Taktik: {tactics_str}\n"
            f"Platform: {platforms_str}\n"
            f"Deskripsi: {technique.get('description')}"
        )

    # -------------------------------------------------------------------------
    # 2. Incident Taxonomy Document Generator
    # -------------------------------------------------------------------------
    @staticmethod
    def generate_taxonomy_documents(
        machinetag_input: Optional[Any] = None, source_version: str = "2"
    ) -> List[Dict[str, Any]]:
        """
        Membangkitkan korpus dokumen taksonomi 11 kategori tertutup yang dipetakan
        ke induk taksonomi eCSIRT/MISP.
        """
        # Jika file machinetag tersedia, baca versinya
        if machinetag_input:
            try:
                if isinstance(machinetag_input, (str, Path)) and Path(machinetag_input).exists():
                    with open(machinetag_input, "r", encoding="utf-8") as f:
                        m_data = json.load(f)
                        source_version = str(m_data.get("version", source_version))
                elif isinstance(machinetag_input, dict):
                    source_version = str(machinetag_input.get("version", source_version))
            except Exception as e:
                logger.warning(f"Gagal membaca machinetag JSON: {e}")

        ingest_date = datetime.now(timezone.utc).isoformat()
        docs: List[Dict[str, Any]] = []

        for cat_id in CLOSED_11_TAXONOMY_CATEGORIES:
            name = TAXONOMY_DISPLAY_NAMES[cat_id]
            ecsirt_parent = ECSIRT_PARENT_MAPPINGS[cat_id]
            definition = TAXONOMY_DEFINITIONS[cat_id]
            examples = TAXONOMY_REPRESENTATIVE_EXAMPLES[cat_id]

            doc = {
                "category_id": cat_id,
                "name": name,
                "ecsirt_parent": ecsirt_parent,
                "definition": definition,
                "representative_examples": examples,
                "metadata": {
                    "source": "misp-taxonomies/ecsirt",
                    "source_version": source_version,
                    "original_id": str(uuid.uuid5(uuid.NAMESPACE_DNS, f"ecsirt.{cat_id}")),
                    "ingest_date": ingest_date,
                },
            }
            docs.append(doc)

        logger.info(f"Taxonomy Generator selesai: {len(docs)} dokumen kategori taksonomi resmi dibangkitkan.")
        return docs

    @staticmethod
    def format_taxonomy_document_text(doc: Dict[str, Any]) -> str:
        """Membuat representasi teks dokumen taksonomi insiden untuk indeks RAG."""
        contoh_str = " | ".join(doc.get("representative_examples", []))
        return (
            f"[TAKSONOMI INSIDEN SIBER]\n"
            f"Kategori: {doc.get('name')}\n"
            f"ID Kategori: {doc.get('category_id')}\n"
            f"Induk eCSIRT: {doc.get('ecsirt_parent')}\n"
            f"Definisi: {doc.get('definition')}\n"
            f"Contoh Kasus Nyata: {contoh_str}"
        )

    # -------------------------------------------------------------------------
    # 3. D3FEND Relational Storage (SQLite)
    # -------------------------------------------------------------------------
    @staticmethod
    def prepare_d3fend_storage(
        mappings_input: Any,
        techniques_input: Any,
        db_path: Path = DEFAULT_DB_PATH,
        prepared_dir: Optional[Path] = None,
        source_version: str = "1.6.0",
    ) -> Dict[str, Any]:
        """
        Memproses ontologi teknik D3FEND dan relasi pemetaan ATT&CK -> D3FEND,
        lalu menyimpannya ke tabel relasional SQLite (strictly non-vector).
        """
        # 1. Load techniques data
        if isinstance(techniques_input, (str, Path)):
            with open(techniques_input, "r", encoding="utf-8") as f:
                tech_json = json.load(f)
        elif isinstance(techniques_input, dict):
            tech_json = techniques_input
        else:
            raise TypeError("techniques_input harus berupa Path atau dict")

        # 2. Load mappings data
        if isinstance(mappings_input, (str, Path)):
            with open(mappings_input, "r", encoding="utf-8") as f:
                map_json = json.load(f)
        elif isinstance(mappings_input, dict):
            map_json = mappings_input
        else:
            raise TypeError("mappings_input harus berupa Path atau dict")

        sekarang = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")

        # Ekstrak seluruh teknik D3FEND dari @graph
        techniques_to_store: Dict[str, Dict[str, Any]] = {}
        uri_to_id: Dict[str, str] = {}
        label_to_id: Dict[str, str] = {}

        for item in tech_json.get("@graph", []):
            d3_id = item.get("d3f:d3fend-id")
            label = item.get("rdfs:label")
            at_id = item.get("@id", "")
            synonym = item.get("d3f:synonym")
            synonym_str = synonym if isinstance(synonym, str) else (", ".join(synonym) if isinstance(synonym, list) else "")

            if not d3_id or not label:
                continue

            definition = synonym_str or f"Teknik pertahanan {label} (D3FEND)."
            tactic = "Harden"  # default tactic jika tidak terspesifikasi langsung di technique all

            techniques_to_store[d3_id] = {
                "technique_id": d3_id,
                "name": label,
                "tactic": tactic,
                "definition": definition,
                "source_version": source_version,
                "updated_at": sekarang,
            }

            label_to_id[label.lower()] = d3_id
            if at_id:
                clean_at_id = at_id.split(":")[-1]
                uri_to_id[clean_at_id.lower()] = d3_id

        # Ekstrak pemetaan dari bindings SPARQL
        bindings = map_json.get("results", {}).get("bindings", [])
        mappings_to_store: List[Dict[str, Any]] = []

        for b in bindings:
            off_tech_id_obj = b.get("off_tech_id", {})
            off_tech_id = off_tech_id_obj.get("value")
            if not off_tech_id:
                continue

            def_tech_label = b.get("def_tech_label", {}).get("value", "")
            query_def_tech_label = b.get("query_def_tech_label", {}).get("value", "")
            def_tactic_label = b.get("def_tactic_label", {}).get("value", "Defend")
            def_tech_uri = b.get("def_tech", {}).get("value", "")

            # Resolusi D3FEND technique ID
            d3_tech_id = None
            if def_tech_label and def_tech_label.lower() in label_to_id:
                d3_tech_id = label_to_id[def_tech_label.lower()]
            elif query_def_tech_label and query_def_tech_label.lower() in label_to_id:
                d3_tech_id = label_to_id[query_def_tech_label.lower()]
            elif def_tech_uri:
                cls_name = def_tech_uri.split("#")[-1].lower()
                if cls_name in uri_to_id:
                    d3_tech_id = uri_to_id[cls_name]

            # Jika teknik belum terdaftar di techniques_to_store, tambahkan sebagai entri valid
            target_label = query_def_tech_label or def_tech_label or "Defensive Technique"
            if not d3_tech_id:
                # Bentuk synthetic / canonical ID dari label jika tidak terdaftar di all.json
                # Contoh: "D3-TokenBinding"
                clean_name = "".join(c for c in target_label.title() if c.isalnum())
                d3_tech_id = f"D3-{clean_name[:8].upper()}"

            if d3_tech_id not in techniques_to_store:
                techniques_to_store[d3_tech_id] = {
                    "technique_id": d3_tech_id,
                    "name": target_label,
                    "tactic": def_tactic_label,
                    "definition": f"Tindakan pertahanan D3FEND untuk taktik {def_tactic_label}.",
                    "source_version": source_version,
                    "updated_at": sekarang,
                }
            else:
                # Perbarui taktik jika lebih spesifik dari mappings
                if def_tactic_label and techniques_to_store[d3_tech_id]["tactic"] == "Harden":
                    techniques_to_store[d3_tech_id]["tactic"] = def_tactic_label

            tech_info = techniques_to_store.get(d3_tech_id, {})
            mappings_to_store.append({
                "attack_technique_id": off_tech_id,
                "d3fend_technique_id": d3_tech_id,
                "technique_id": d3_tech_id,
                "name": tech_info.get("name", target_label),
                "tactic": tech_info.get("tactic", def_tactic_label),
                "definition": tech_info.get("definition", f"Tindakan pertahanan D3FEND untuk taktik {def_tactic_label}."),
                "relationship_type": "mitigates",
                "source_version": source_version,
            })

        # Simpan ke berkas JSON data/prepared/ dan SQLite jika custom db
        tech_list = sorted(list(techniques_to_store.values()), key=lambda x: x["technique_id"])
        mappings_to_store = sorted(mappings_to_store, key=lambda x: (x["attack_technique_id"], x["technique_id"]))
        stored_tech = simpan_d3fend_techniques(tech_list, db_path=db_path, prepared_dir=prepared_dir)
        stored_maps = simpan_d3fend_attack_mappings(mappings_to_store, db_path=db_path, prepared_dir=prepared_dir)

        logger.info(
            f"D3FEND Storage siap: {stored_tech} teknik disimpan, {stored_maps} baris relasi ATT&CK dipetakan."
        )

        return {
            "techniques_stored": stored_tech,
            "mappings_stored": stored_maps,
            "total_raw_bindings": len(bindings),
            "db_path": str(db_path),
        }

    # -------------------------------------------------------------------------
    # 4. NIST OSCAL Control Flattener
    # -------------------------------------------------------------------------
    @staticmethod
    def _extract_prose(parts: List[Dict[str, Any]]) -> str:
        """Ekstraksi teks pernyataan secara rekursif dari struktur parts OSCAL."""
        texts = []
        for p in parts:
            name = p.get("name", "")
            if name in ("statement", "item", "overview", "guidance"):
                prose = p.get("prose", "").strip()
                if prose:
                    texts.append(prose)
            if "parts" in p and isinstance(p["parts"], list):
                nested = CTIPreparer._extract_prose(p["parts"])
                if nested:
                    texts.append(nested)
        return " ".join(texts).strip()

    @staticmethod
    def flatten_nist_oscal(
        sp800_input: Optional[Any] = None,
        csf_input: Optional[Any] = None,
        source_version: str = "SP800-53-Rev5 / CSF-2.0",
    ) -> List[Dict[str, Any]]:
        """
        Meratakan katalog kontrol NIST SP 800-53 Rev 5 dan subkategori CSF 2.0
        menjadi dokumen kontrol terstruktur.
        """
        ingest_date = datetime.now(timezone.utc).isoformat()
        flattened_controls: List[Dict[str, Any]] = []

        # 1. Proses SP 800-53 Rev 5
        if sp800_input:
            if isinstance(sp800_input, (str, Path)) and Path(sp800_input).exists():
                with open(sp800_input, "r", encoding="utf-8") as f:
                    sp_data = json.load(f)
            elif isinstance(sp800_input, dict):
                sp_data = sp800_input
            else:
                sp_data = None

            if sp_data:
                catalog = sp_data.get("catalog", {})
                groups = catalog.get("groups", [])
                for grp in groups:
                    family_title = grp.get("title", grp.get("id", "Security Control"))
                    for ctrl in grp.get("controls", []):
                        raw_id = ctrl.get("id", "")
                        ctrl_id = raw_id.upper()
                        title = ctrl.get("title", "")
                        statement = CTIPreparer._extract_prose(ctrl.get("parts", []))

                        doc = {
                            "control_id": ctrl_id,
                            "title": title,
                            "statement": statement,
                            "family_or_function": family_title,
                            "framework": "NIST SP 800-53 Rev 5",
                            "metadata": {
                                "source": "nist-oscal",
                                "source_version": "SP800-53-Rev5",
                                "original_id": raw_id,
                                "ingest_date": ingest_date,
                            },
                        }
                        flattened_controls.append(doc)

                        # Proses enhancement kontrol jika ada
                        for enh in ctrl.get("controls", []):
                            enh_raw_id = enh.get("id", "")
                            enh_id = enh_raw_id.upper()
                            enh_title = enh.get("title", title)
                            enh_stmt = CTIPreparer._extract_prose(enh.get("parts", []))
                            doc_enh = {
                                "control_id": enh_id,
                                "title": f"{title} - {enh_title}",
                                "statement": enh_stmt or statement,
                                "family_or_function": family_title,
                                "framework": "NIST SP 800-53 Rev 5",
                                "metadata": {
                                    "source": "nist-oscal",
                                    "source_version": "SP800-53-Rev5",
                                    "original_id": enh_raw_id,
                                    "ingest_date": ingest_date,
                                },
                            }
                            flattened_controls.append(doc_enh)

        # 2. Proses CSF 2.0
        if csf_input:
            if isinstance(csf_input, (str, Path)) and Path(csf_input).exists():
                with open(csf_input, "r", encoding="utf-8") as f:
                    csf_data = json.load(f)
            elif isinstance(csf_input, dict):
                csf_data = csf_input
            else:
                csf_data = None

            if csf_data:
                catalog = csf_data.get("catalog", {})
                groups = catalog.get("groups", [])
                for grp in groups:
                    fn_title = grp.get("title", grp.get("id", "Cybersecurity Function"))
                    for cat in grp.get("controls", []):
                        cat_title = cat.get("title", "")
                        for subcat in cat.get("controls", []):
                            subcat_id = subcat.get("id", "").upper()
                            title = subcat.get("title", cat_title)
                            statement = CTIPreparer._extract_prose(subcat.get("parts", []))

                            doc = {
                                "control_id": subcat_id,
                                "title": f"{cat_title}: {title}",
                                "statement": statement,
                                "family_or_function": fn_title,
                                "framework": "NIST CSF 2.0",
                                "metadata": {
                                    "source": "nist-oscal",
                                    "source_version": "CSF-2.0",
                                    "original_id": subcat.get("id", ""),
                                    "ingest_date": ingest_date,
                                },
                            }
                            flattened_controls.append(doc)

        logger.info(f"NIST Flattener selesai: {len(flattened_controls)} kontrol keamanan diratakan.")
        return flattened_controls

    @staticmethod
    def format_nist_document_text(control: Dict[str, Any]) -> str:
        """Membuat representasi teks kontrol NIST untuk indeks RAG."""
        return (
            f"[KONTROL KEAMANAN SISTEM NIST]\n"
            f"Framework: {control.get('framework')}\n"
            f"ID Kontrol: {control.get('control_id')}\n"
            f"Judul: {control.get('title')}\n"
            f"Keluarga/Fungsi: {control.get('family_or_function')}\n"
            f"Pernyataan: {control.get('statement')}"
        )

    # -------------------------------------------------------------------------
    # 5. Pipeline Runner: Siapkan Seluruh Data Staging
    # -------------------------------------------------------------------------
    def prepare_all_staged(self, specific_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Menemukan berkas unduhan staging terbaru dari data/raw/<sumber>/,
        menjalankan seluruh preparer, dan menyimpan berkas JSON siap pakai ke data/prepared/.
        """
        self.prepared_base_dir.mkdir(parents=True, exist_ok=True)
        summary = {}

        def get_latest_folder(source: str) -> Optional[Path]:
            src_dir = self.raw_base_dir / source
            if not src_dir.exists():
                return None
            if specific_date:
                candidate = src_dir / specific_date
                return candidate if candidate.exists() else None
            folders = sorted([d for d in src_dir.iterdir() if d.is_dir()], reverse=True)
            return folders[0] if folders else None

        # 1. Taksonomi MISP
        misp_folder = get_latest_folder("misp_taxonomies")
        misp_file = (misp_folder / "machinetag.json") if misp_folder else None
        tax_docs = self.generate_taxonomy_documents(misp_file)
        tax_out = self.prepared_base_dir / "taxonomy_categories.json"
        with open(tax_out, "w", encoding="utf-8") as f:
            json.dump(tax_docs, f, indent=2, ensure_ascii=False)
        summary["taxonomy"] = {"count": len(tax_docs), "output": str(tax_out)}

        # 2. MITRE ATT&CK
        attack_folder = get_latest_folder("mitre_attack")
        if attack_folder and (attack_folder / "enterprise-attack.json").exists():
            attack_file = attack_folder / "enterprise-attack.json"
            attack_docs = self.flatten_attack_stix(attack_file)
            attack_out = self.prepared_base_dir / "attack_techniques.json"
            with open(attack_out, "w", encoding="utf-8") as f:
                json.dump(attack_docs, f, indent=2, ensure_ascii=False)
            summary["mitre_attack"] = {"count": len(attack_docs), "output": str(attack_out)}
        else:
            summary["mitre_attack"] = {"count": 0, "status": "RAW_FILE_NOT_FOUND"}

        # 3. MITRE D3FEND
        d3fend_folder = get_latest_folder("mitre_d3fend")
        if d3fend_folder and (d3fend_folder / "d3fend-full-mappings.json").exists():
            map_file = d3fend_folder / "d3fend-full-mappings.json"
            tech_file = d3fend_folder / "technique-all.json"
            ver_file = d3fend_folder / "version.json"
            ver_str = "1.6.0"
            if ver_file.exists():
                try:
                    with open(ver_file, "r", encoding="utf-8") as f:
                        ver_str = json.load(f).get("version", "1.6.0")
                except Exception:
                    pass

            d3_res = self.prepare_d3fend_storage(
                mappings_input=map_file,
                techniques_input=tech_file,
                db_path=self.db_path,
                prepared_dir=self.prepared_base_dir,
                source_version=ver_str,
            )
            summary["d3fend"] = d3_res
        else:
            summary["d3fend"] = {"status": "RAW_FILE_NOT_FOUND"}

        # 4. NIST OSCAL
        nist_folder = get_latest_folder("nist_oscal")
        sp800_file = (nist_folder / "NIST_SP-800-53_rev5_catalog.json") if nist_folder else None
        csf_file = (nist_folder / "CSF_2.0_catalog.json") if nist_folder else None
        nist_docs = self.flatten_nist_oscal(sp800_file, csf_file)
        nist_out = self.prepared_base_dir / "nist_controls.json"
        with open(nist_out, "w", encoding="utf-8") as f:
            json.dump(nist_docs, f, indent=2, ensure_ascii=False)
        summary["nist_oscal"] = {"count": len(nist_docs), "output": str(nist_out)}

        return summary


# Convenience functions
def flatten_attack_stix(stix_input: Any, source_version: str = "v20.0") -> List[Dict[str, Any]]:
    return CTIPreparer.flatten_attack_stix(stix_input, source_version)


def generate_taxonomy_documents(machinetag_input: Optional[Any] = None, source_version: str = "2") -> List[Dict[str, Any]]:
    return CTIPreparer.generate_taxonomy_documents(machinetag_input, source_version)


def prepare_d3fend_storage(
    mappings_input: Any,
    techniques_input: Any,
    db_path: Path = DEFAULT_DB_PATH,
    prepared_dir: Optional[Path] = None,
    source_version: str = "1.6.0",
) -> Dict[str, Any]:
    return CTIPreparer.prepare_d3fend_storage(mappings_input, techniques_input, db_path, prepared_dir, source_version)


def flatten_nist_oscal(
    sp800_input: Optional[Any] = None, csf_input: Optional[Any] = None, source_version: str = "SP800-53-Rev5 / CSF-2.0"
) -> List[Dict[str, Any]]:
    return CTIPreparer.flatten_nist_oscal(sp800_input, csf_input, source_version)


def prepare_all_staged(
    raw_dir: Path = DEFAULT_RAW_DIR,
    prepared_dir: Path = DEFAULT_PREPARED_DIR,
    db_path: Path = DEFAULT_DB_PATH,
    specific_date: Optional[str] = None,
) -> Dict[str, Any]:
    preparer = CTIPreparer(raw_base_dir=raw_dir, prepared_base_dir=prepared_dir, db_path=db_path)
    return preparer.prepare_all_staged(specific_date=specific_date)


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="CTI Data Preparation CLI")
    parser.add_argument("--date", help="Tanggal staging tertentu (YYYY-MM-DD)")
    args = parser.parse_args()

    res = prepare_all_staged(specific_date=args.date)
    print(json.dumps(res, indent=2, ensure_ascii=False))
