# -*- coding: utf-8 -*-
"""
Data logbook lengkap 18 minggu untuk proyek SiberHarian di Diskominfo Provinsi Jawa Timur.
"""

WEEKS_DATA = [
    # MINGGU 1
    {
        "week_num": 1,
        "date_range": "22 Juni 2026 – 26 Juni 2026",
        "theme": "Onboarding, Orientasi Tim CSIRT Diskominfo Jatim & Asesmen Alur Monitoring Insiden Siber",
        "phase": "Fase I: Inisiasi & Konseptualisasi Proyek",
        "days": [
            {
                "day": "Senin, 22 Juni 2026",
                "plan": "Lapor diri di Kantor Diskominfo Provinsi Jawa Timur, penyerahan surat pengantar magang dari universitas, dan registrasi administrasi kepegawaian.",
                "result": "Diterima secara resmi di Bidang Keamanan Informasi dan Persandian Diskominfo Jatim; perkenalan dengan Pembimbing Lapangan dan penataan ruang kerja.",
                "obstacle": "Penyesuaian terhadap regulasi internal instansi dan kepatuhan pengamanan data lingkungan pemerintahan provinsi.",
                "solution": "Mempelajari pakta integritas kerahasiaan data dan tata tertib kerja di lingkungan Diskominfo Jatim."
            },
            {
                "day": "Selasa, 23 Juni 2026",
                "plan": "Orientasi tugas pokok dan fungsi (Tupoksi) Seksi Keamanan Informasi dan Computer Security Incident Response Team (CSIRT Jatim).",
                "result": "Memahami alur eskalasi insiden siber daerah dan ekosistem portal resmi CSIRT Jatim (csirt.jatimprov.go.id).",
                "obstacle": "Banyaknya istilah teknis dan alur birokrasi koordinasi insiden antar-Organisasi Perangkat Daerah (OPD).",
                "solution": "Membuat ringkasan bagan alur koordinasi CSIRT Jatim dengan BSSN dan narahubung OPD di 38 kabupaten/kota."
            },
            {
                "day": "Rabu, 24 Juni 2026",
                "plan": "Observasi langsung aktivitas harian analis Security Operations Center (SOC) dalam memantau tren ancaman siber harian.",
                "result": "Menemukan fakta bahwa analis SOC setiap pagi membuka 15-20 tab berita siber dan buletin keamanan secara manual untuk menyusun laporan ringkas.",
                "obstacle": "Analis mengalami kelelahan peringatan (alert fatigue) dan proses kurasi manual menyita waktu hingga 2-3 jam setiap pagi.",
                "solution": "Mencatat poin kebutuhan otomasi pengumpulan berita dan sintesis ringkasan ancaman berbasis AI yang terpercaya."
            },
            {
                "day": "Kamis, 25 Juni 2026",
                "plan": "Wawancara mendalam dengan staf teknis SOC mengenai kriteria berita ancaman siber yang relevan untuk perlindungan web Pemprov Jatim.",
                "result": "Terkumpulnya parameter relevansi: insiden kebocoran data, serangan ransomware, phishing, judi online pada domain .go.id/.ac.id, dan web defacement.",
                "obstacle": "Tingginya derau (noise) berita clickbait, artikel tutorial umum, dan hoaks yang kerap bercampur di feed berita publik.",
                "solution": "Merumuskan kebutuhan filter relevansi awal berbasis klasifikasi teks dan kata kunci spesifik Jawa Timur dan instansi pemerintah."
            },
            {
                "day": "Jumat, 26 Juni 2026",
                "plan": "Diskusi awal dengan Pembimbing Lapangan untuk merumuskan judul dan ruang lingkup proyek Capstone / Magang.",
                "result": "Disetujuinya topik proyek: Pengembangan Sistem Intelijen Berita dan Notifikasi Ancaman Siber Otomatis Berbasis AI untuk CSIRT Diskominfo Jatim (SiberHarian).",
                "obstacle": "Ekspektasi instansi yang menginginkan sistem otomatis namun tetap terkontrol tanpa risiko salah informasi kepada pimpinan.",
                "solution": "Menyepakati prinsip Human-in-the-Loop di mana AI berfungsi sebagai asisten kurasi dan penyusun rekomendasi awal bagi analis."
            }
        ],
        "tech_reflection": "Minggu pertama memberikan wawasan empiris nyata mengenai tantangan operasional Tim CSIRT Diskominfo Jatim. Analis membutuhkan instrumen pengumpulan intelijen siber terbuka (OSINT) yang dapat merangkum insiden secara cepat tanpa mengorbankan akurasi fakta. Kesepakatan awal menetapkan bahwa sistem harus bersifat lokal (*local-first*) untuk kedaulatan data pemerintah.",
        "supervisor_note": "Inisiasi proyek sangat baik dan relevan dengan kendala riil analis SOC CSIRT Jatim. Lanjutkan ke penyusunan proposal formal."
    },

    # MINGGU 2
    {
        "week_num": 2,
        "date_range": "29 Juni 2026 – 3 Juli 2026",
        "theme": "Penyusunan Proposal Magang & Capstone Design Project",
        "phase": "Fase I: Inisiasi & Konseptualisasi Proyek",
        "days": [
            {
                "day": "Senin, 29 Juni 2026",
                "plan": "Menyusun draf latar belakang proposal magang/capstone dengan mengumpulkan data empiris insiden siber nasional dan daerah.",
                "result": "Tersusunnya draf latar belakang mengangkat kasus ransomware Pusat Data Nasional Sementara (PDNS 2024) dan data anomali siber BSSN (>741 juta anomali).",
                "obstacle": "Mencari data statistik insiden siber yang valid dan memiliki rujukan ilmiah kredibel untuk latar belakang.",
                "solution": "Menggunakan data laporan tahunan BSSN dan referensi jurnal ilmiah terkini (2023-2025) mengenai tata kelola keamanan SPBE."
            },
            {
                "day": "Selasa, 30 Juni 2026",
                "plan": "Merumuskan rumusan masalah, tujuan penelitian, batasan masalah, dan asumsi proyek SiberHarian.",
                "result": "Terumuskannya 2 rumusan masalah utama: rancang bangun dashboard admin analitik berbasis RAG dan integrasi rekomendasi mitigasi terverifikasi.",
                "obstacle": "Cakupan proyek sempat terlalu melebar ke arah analisis log jaringan internal server firewall dan honeypot.",
                "solution": "Membatasi ruang lingkup pada analisis teks berita insiden siber terbuka (CTI) guna memastikan kelayakan penyelesaian dalam 18 minggu."
            },
            {
                "day": "Rabu, 1 Juli 2026",
                "plan": "Menyusun Bab II Studi Pustaka mengenai Cyber Threat Intelligence (CTI), Large Language Models (LLM), dan risiko halusinasi AI.",
                "result": "Tersusunnya kajian pustaka mengenai arsitektur Retrieval-Augmented Generation (RAG) untuk memitigasi halusinasi model generatif pada domain siber.",
                "obstacle": "Banyaknya literatur RAG yang masih berfokus pada chatbot tanya-jawab umum, minim yang membahas CTI untuk instansi pemerintah.",
                "solution": "Mengeksplorasi paper riset terkini mengenai NLP-driven CTI (Arazzi et al., 2025; Alhuzali, 2025; Hsieh et al., 2026)."
            },
            {
                "day": "Kamis, 2 Juli 2026",
                "plan": "Menyusun metodologi penelitian, tahapan rekayasa perangkat lunak, dan estimasi linimasa kerja 18 minggu.",
                "result": "Tersusunnya Bab III Metodologi dengan pendekatan Waterfall teradaptasi (Inisiasi, Desain, Eksperimen Model, Implementasi, Testing, Evaluasi, Serah Terima).",
                "obstacle": "Estimasi alokasi waktu untuk eksperimen model AI lokal vs kebutuhan integrasi web interface.",
                "solution": "Menetapkan milestone mingguan yang jelas dengan pengujian bertahap setiap iterasi pengembangan."
            },
            {
                "day": "Jumat, 3 Juli 2026",
                "plan": "Review internal naskah proposal bersama rekan tim magang dan penyusunan slide presentasi proposal.",
                "result": "Dokumen draf Proposal Magang & Capstone lengkap (BAB I, II, III) serta 15 slide presentasi siap uji.",
                "obstacle": "Format dokumen Word universitas memiliki aturan penulisan dan penomoran yang ketat.",
                "solution": "Melakukan standarisasi margin (4-4-3-3), font Times New Roman 12pt, dan sistem sitasi IEEE/APA menggunakan Mendeley."
            }
        ],
        "tech_reflection": "Penyusunan proposal memperjelas batasan ilmiah dan praktis proyek. Fokus penelitian diarahkan pada bagaimana mentransformasikan data teks berita tidak terstruktur menjadi intelijen terstruktur yang dapat ditindaklanjuti (*actionable CTI*) dengan garansi anti-halusinasi melalui pendekatan RAG.",
        "supervisor_note": "Draf proposal sudah terstruktur rapi. Siapkan sesi presentasi review bersama tim CSIRT dan dosen pembimbing."
    },

    # MINGGU 3
    {
        "week_num": 3,
        "date_range": "6 Juli 2026 – 10 Juli 2026",
        "theme": "Bimbingan & Presentasi Proposal Project di Hadapan Instansi dan Pembimbing Akademik",
        "phase": "Fase I: Inisiasi & Konseptualisasi Proyek",
        "days": [
            {
                "day": "Senin, 6 Juli 2026",
                "plan": "Simulasi mandiri presentasi proposal dan persiapan berkas administrasi bimbingan capstone.",
                "result": "Mempersiapkan demonstrasi konsep sederhana alur kerja scraping berita dan alur ringkasan AI.",
                "obstacle": "Kekhawatiran konektivitas internet dan kesiapan demonstrasi saat sesi review resmi.",
                "solution": "Menyiapkan skenario offline dengan tangkapan layar dan diagram alur sistem yang komprehensif."
            },
            {
                "day": "Selasa, 7 Juli 2026",
                "plan": "Melaksanakan sesi presentasi proposal di Ruang Rapat Bidang Keamanan Informasi Diskominfo Jatim.",
                "result": "Presentasi berjalan lancar di hadapan Pembimbing Lapangan dan jajaran staf teknis CSIRT Jatim.",
                "obstacle": "Pembimbing lapangan mempertanyakan aspek kepatuhan hukum: bagaimana sistem menghindari plagiasi berita dan masalah hak cipta media.",
                "solution": "Mencatat masukan bahwa sistem wajib melakukan parafrase faktual mandiri (*abstractive rewriting*) dan menyertakan atribusi sumber resmi."
            },
            {
                "day": "Rabu, 8 Juli 2026",
                "plan": "Bimbingan daring bersama Dosen Pembimbing Akademik mengenai aspek metodologi dan justifikasi ilmiah capstone.",
                "result": "Dosen menyetujui arah penelitian dengan catatan wajib menyertakan pengujian kuantitatif performa RAG (misal metrik RAGAS).",
                "obstacle": "Perlunya pembuktian bahwa sistem benar-benar menekan halusinasi model bahasa secara terukur.",
                "solution": "Menambahkan rencana evaluasi Faithfulness dan Context Recall ke dalam proposal penelitian."
            },
            {
                "day": "Kamis, 9 Juli 2026",
                "plan": "Rapat koordinasi teknis dengan staf analis CSIRT untuk menyelaraskan kebutuhan fitur khusus.",
                "result": "Staf analis mengusulkan sistem tidak hanya memantau berita umum, tetapi juga melacak kerentanan perangkat lunak (CVE) dan indikator serangan MITRE ATT&CK.",
                "obstacle": "Penambahan pelacakan CVE meningkatkan kompleksitas skema data dan sumber integrasi.",
                "solution": "Menyetujui usulan pelacakan CVE dari National Vulnerability Database (NVD API) sebagai komponen awal sistem."
            },
            {
                "day": "Jumat, 10 Juli 2026",
                "plan": "Mengumpulkan seluruh notulensi feedback dari instansi dan kampus, serta menyusun daftar rencana aksi perbaikan proposal.",
                "result": "Matriks rekapitulasi masukan proposal tersusun (7 poin revisi teknis dan metodologis).",
                "obstacle": "Menyelaraskan ekspektasi akademis dosen (teoretis) dengan kebutuhan praktis instansi (operasional cepat).",
                "solution": "Menetapkan pendekatan dual-output: laporan akademis komprehensif untuk kampus dan dashboard operasional siap pakai untuk Diskominfo."
            }
        ],
        "tech_reflection": "Sesi presentasi membuka wawasan krusial mengenai dua tantangan besar: kepatuhan hak cipta pers (ringkasan tidak boleh menyalin teks artikel) dan kebutuhan analis terhadap indikator teknis (CVE dan MITRE ATT&CK). Ini menjadi panduan fundamental arsitektur sistem.",
        "supervisor_note": "Presentasi baik. Segera lakukan revisi sesuai catatan notulensi, terutama penegasan etika data dan pengujian sistem."
    },

    # MINGGU 4
    {
        "week_num": 4,
        "date_range": "13 Juli 2026 – 17 Juli 2026",
        "theme": "Perbaikan Proposal Project & Penentuan Spesifikasi Kebutuhan Stack Teknologi",
        "phase": "Fase I: Inisiasi & Konseptualisasi Proyek",
        "days": [
            {
                "day": "Senin, 13 Juli 2026",
                "plan": "Memperbaiki naskah proposal sesuai catatan revisi: menambahkan analisis hak cipta pers dan evaluasi RAGAS.",
                "result": "Naskah Proposal Magang dan Capstone Design Project versi final berhasil diselesaikan dan dicetak.",
                "obstacle": "Penyelarasan redaksional agar sesuai format baku akademik dan instansi.",
                "solution": "Pemeriksaan tata bahasa dan pengecekan turnitin mandiri untuk memastikan orisinalitas naskah proposal."
            },
            {
                "day": "Selasa, 14 Juli 2026",
                "plan": "Pengesahan dokumen proposal final: penandatanganan oleh Pembimbing Lapangan dan pengiriman ke pihak program studi kampus.",
                "result": "Dokumen proposal resmi disahkan oleh Diskominfo Jatim dan Dosen Pembimbing; legalitas proyek terpenuhi.",
                "obstacle": "Menunggu penyesuaian jadwal pejabat pembimbing instansi yang sedang dinas luar kota.",
                "solution": "Memanfaatkan koordinasi digital dan penandatanganan tepat waktu saat pembimbing kembali ke kantor."
            },
            {
                "day": "Rabu, 15 Juli 2026",
                "plan": "Menyusun Software Requirement Specification (SRS): Kebutuhan Fungsional (FR) dan Non-Fungsional (NFR).",
                "result": "Dokumen SRS memuat 14 Kebutuhan Fungsional (scraping, dedup, summarizer, visualisasi, ekspor) dan 6 Kebutuhan Non-Fungsional.",
                "obstacle": "Menentukan standar waktu respon sistem saat melakukan komputasi analitik berkala.",
                "solution": "Menetapkan batas NFR: respon query data web < 200 ms, dan throughput scraping terjadwal di latar belakang."
            },
            {
                "day": "Kamis, 16 Juli 2026",
                "plan": "Benchmarking dan komparasi stack teknologi backend, database, dan antarmuka web.",
                "result": "Keputusan final stack: Python 3.12, FastAPI (asinkron, performa tinggi), SQLite (local-first data sovereignty), Tailwind CSS, Chart.js.",
                "obstacle": "Pertimbangan apakah menggunakan arsitektur SPA (React/Vue) atau Server-Side Rendering (FastAPI Jinja2).",
                "solution": "Memilih Jinja2 + Tailwind + Vanilla JS modular untuk mereduksi beban dependensi build tool (Node.js/npm) pada server instansi."
            },
            {
                "day": "Jumat, 17 Juli 2026",
                "plan": "Setup workstation magang di Diskominfo Jatim: konfigurasi environment Python 3.12, virtualenv, dan instalasi library dasar.",
                "result": "Lingkungan pengembangan lokal siap pakai dengan Git, VS Code, ekstensi Python, dan SQLite Viewer.",
                "obstacle": "Kebijakan keamanan jaringan Diskominfo yang membatasi unduhan beberapa paket pihak ketiga melalui proxy dinas.",
                "solution": "Melakukan konfigurasi pip config dengan trusted-host resmi dan berkonsultasi dengan admin jaringan dinas."
            }
        ],
        "tech_reflection": "Keputusan memilih arsitektur *Local-First* dengan SQLite dan FastAPI terbukti sangat strategis. Ini menjamin data pemantauan tidak bergantung pada server basis data eksternal yang rumit, menjaga kemudahan migrasi dan kepatuhan kedaulatan data instansi pemerintah daerah.",
        "supervisor_note": "Proposal telah disahkan. Stack teknologi yang dipilih rasional dan sesuai kapabilitas server instansi. Lanjutkan perancangan arsitektur."
    },

    # MINGGU 5
    {
        "week_num": 5,
        "date_range": "20 Juli 2026 – 24 Juli 2026",
        "theme": "Perancangan Arsitektur Sistem, Skema Database Awal & Desain Dual Ingestion (Berita + CVE)",
        "phase": "Fase II: Pengembangan Arsitektur Awal & Model Lokal",
        "days": [
            {
                "day": "Senin, 20 Juli 2026",
                "plan": "Merancang diagram alur data menyeluruh (Data Flow Diagram / DFD) dan flowchart pemrosesan pipeline.",
                "result": "Diagram alur sistem memetakan 2 jalur ingestion data: Feed Berita Insiden (RSS) dan Feed Kerentanan Software (CVE NVD API).",
                "obstacle": "Perbedaan karakteristik yang sangat tajam antara data berita (naratif) dan data CVE (terstruktur CVSS/CPE).",
                "solution": "Merancang skema pemrosesan modular terpisah sebelum nantinya dikonsolidasikan pada tahap penyajian dasbor."
            },
            {
                "day": "Selasa, 21 Juli 2026",
                "plan": "Merancang skema relasi basis data SQLite (`data/state.db`) untuk menampung artikel berita, log dedup, dan CVE.",
                "result": "DDL tabel SQLite awal: tabel `berita` (id, judul, sumber, url, konten, ringkasan, tanggal, kategori) dan `sent_history` (url_hash, judul_hash, created_at).",
                "obstacle": "Menghindari duplikasi penyimpanan URL yang sama saat cron job scraping dieksekusi berulang.",
                "solution": "Menerapkan unique constraint pada kolom `url_hash` (MD5 hash) sebagai indeks primer anti-duplikasi tingkat database."
            },
            {
                "day": "Rabu, 22 Juli 2026",
                "plan": "Membuat skrip pembentukan basis data `src/storage/db.py` dan fungsi Create-Read-Update (CRUD) awal.",
                "result": "Modul `db.py` berfungsi menyimpan artikel, memeriksa eksistensi URL, dan mengambil feed berita terbaru.",
                "obstacle": "Performa penulisan SQLite saat terjadi operasi batch insert artikel dalam jumlah banyak secara bersamaan.",
                "solution": "Menerapkan konteks manajer `sqlite3.connect` dengan mode WAL (Write-Ahead Logging) untuk mengoptimalkan konkurensi baca-tulis."
            },
            {
                "day": "Kamis, 23 Juli 2026",
                "plan": "Inventarisasi dan kurasi sumber feed berita ancaman siber kredibel (nasional dan internasional).",
                "result": "Terdaftar 12 feed berita utama: BleepingComputer, The Hacker News, Dark Reading, SecurityWeek, CISA Alerts, dan Google News RSS topik siber Indonesia.",
                "obstacle": "Beberapa feed RSS media nasional sering memuat artikel di luar konteks siber jika query kata kunci terlalu umum.",
                "solution": "Merancang string query kata kunci spesifik: peretasan, kebocoran data, ransomware, defacement, phising, malware, dsb."
            },
            {
                "day": "Jumat, 24 Juli 2026",
                "plan": "Membuat wireframe tata letak antarmuka web dashboard admin dan tampilan publik.",
                "result": "Wireframe antarmuka memuat Tab Beranda (Feed Berita & CVE), Tab Arsip Berita, dan Tab Tren Serangan.",
                "obstacle": "Menentukan informasi apa saja yang harus ditampilkan pada kartu (card) berita agar tidak terlalu padat namun tetap informatif.",
                "solution": "Menetapkan komponen kartu: Judul, Sumber & Waktu, Badge Kategori Ancaman, Ringkasan Poin Kritis, dan Tombol Baca Sumber Asli."
            }
        ],
        "tech_reflection": "Arsitektur awal dirancang dengan asumsi bahwa analis membutuhkan pemantauan berita umum sekaligus pelacakan CVE software. Pendekatan dual ingestion ini menjadi basis pengujian awal sebelum dievaluasi efektivitasnya dalam operasional harian.",
        "supervisor_note": "Rancangan skema data sudah baik. Pastikan penanganan duplikasi berita benar-benar kuat agar tidak memenuhi penyimpanan."
    },

    # MINGGU 6
    {
        "week_num": 6,
        "date_range": "27 Juli 2026 – 31 Juli 2026",
        "theme": "Eksperimen Model LLM Lokal (Ollama), Bottleneck Hardware & Terbitnya Log Sistem Perdana (31 Juli 2026)",
        "phase": "Fase II: Pengembangan Arsitektur Awal & Model Lokal",
        "days": [
            {
                "day": "Senin, 27 Juli 2026",
                "plan": "Instalasi dan konfigurasi runtime Ollama pada workstation pengujian untuk menjalankan model LLM secara lokal.",
                "result": "Ollama service berjalan di `localhost:11434`; mengunduh model open-source `llama3:8b` dan `mistral:7b-instruct`.",
                "obstacle": "Kecepatan unduhan model yang berukuran 4.7 GB hingga 5.2 GB sempat terputus pada jaringan instansi.",
                "solution": "Menggunakan download manager bertahap dan memverifikasi integritas checksum SHA256 model."
            },
            {
                "day": "Selasa, 28 Juli 2026",
                "plan": "Mengembangkan modul pengujian inferensi LLM lokal `scripts/debug/llm_summarizer.py` berbasis REST API Ollama.",
                "result": "Skrip prototipe mampu mengirimkan teks artikel siber dan menerima respon generasi ringkasan dari model lokal.",
                "obstacle": "Waktu inferensi (latency) per artikel sangat lambat, memakan waktu 30 hingga 45 detik untuk 1 berita berukuran sedang.",
                "solution": "Mencoba parameter kuantisasi model lebih rendah (4-bit quantization) untuk meringankan komputasi matematika GPU."
            },
            {
                "day": "Rabu, 29 Juli 2026",
                "plan": "Pengujian pemrosesan batch 25 artikel berita siber menggunakan model `mistral:7b-instruct` pada workstation.",
                "result": "Hasil inferensi batch tersimpan; tercatat waktu total eksekusi mencapai 18 menit 40 detik.",
                "obstacle": "Workstation mengalami lonjakan penggunaan RAM hingga 94% dan suhu GPU meningkat drastis; terjadi 2 kali out-of-memory (OOM) error.",
                "solution": "Menambahkan jeda sleep 3 detik antar inferensi dan membersihkan context buffer memori Ollama setelah setiap artikel selesai."
            },
            {
                "day": "Kamis, 30 Juli 2026",
                "plan": "Mengevaluasi kualitas bahasa dan akurasi ringkasan yang dihasilkan model lokal open-source.",
                "result": "Model sering mencampurkan istilah bahasa Inggris secara tidak teratur dan format ringkasan sering meleset dari instruksi JSON/poin.",
                "obstacle": "Model 7B/8B lokal memiliki keterbatasan kepatuhan instruksi (*instruction-following drift*) jika teks input terlalu panjang.",
                "solution": "Memangkas teks masukan maksimal 1.500 karakter dan menyusun prompt dalam Bahasa Indonesia dengan contoh eksplisit (*1-shot prompt*)."
            },
            {
                "day": "Jumat, 31 Juli 2026",
                "plan": "Membangun sistem logging terpadu (`src/utils/logger.py`) dan menjalankan pipeline otomatis pertama proyek.",
                "result": "Sistem logging berhasil mencatat eksekusi harian pertama kali secara resmi di berkas `logs/2026-07-31.log` (245 baris log).",
                "obstacle": "Format timestamp log server sempat tidak sinkron dengan zona waktu lokal Indonesia Barat (WIB).",
                "solution": "Mengonfigurasi timezone `Asia/Jakarta` secara eksplisit pada modul logger Python."
            }
        ],
        "tech_reflection": "Minggu ke-6 menjadi tonggak teknis penting dengan terbitnya berkas `logs/2026-07-31.log`. Namun, eksperimen ini membuktikan kelemahan fatal model lokal: latensi yang terlalu lama (>30 detik/artikel) dan beban hardware berat yang tidak realistis untuk server tanpa GPU enterprise.",
        "supervisor_note": "Log sistem perdana berhasil dicatat. Kendala latensi dan suhu workstation perlu diantisipasi serius jika sistem ingin dijalankan kontinu."
    },

    # MINGGU 7
    {
        "week_num": 7,
        "date_range": "3 Agustus 2026 – 7 Agustus 2026",
        "theme": "Pengembangan Pipeline Scraping Multi-Sumber & Hybrid Deduplicator (RapidFuzz)",
        "phase": "Fase II: Pengembangan Arsitektur Awal & Model Lokal",
        "days": [
            {
                "day": "Senin, 3 Agustus 2026",
                "plan": "Mengembangkan modul scraping asinkron `src/scraper/pipeline.py` dan `src/scraper/sources.py` menggunakan `feedparser` dan `httpx`.",
                "result": "Sistem mampu mengumpulkan feed RSS dari 6 sumber internasional dan nasional secara otomatis; log tercatat di `logs/2026-08-02.log` dan `logs/2026-08-03.log`.",
                "obstacle": "Beberapa portal berita media online membatasi request perayapan dan mengembalikan halaman error 403 Forbidden.",
                "solution": "Mengonfigurasi header HTTP permintaan dengan User-Agent browser modern dan menerapkan mekanisme retry bertahap."
            },
            {
                "day": "Selasa, 4 Agustus 2026",
                "plan": "Mengembangkan modul ekstraksi konten berita bersih `src/scraper/extractor.py` menggunakan BeautifulSoup4.",
                "result": "Teks artikel berita berhasil diekstraksi bersih dari tag iklan, skrip javascript, navigasi, dan tombol media sosial.",
                "obstacle": "Variasi struktur DOM HTML yang sangat berbeda antar situs berita (tag `<article>`, `<div>`, `<section>`).",
                "solution": "Membuat algoritma pembersihan heuristik berbasis kepadatan teks (*text-to-tag ratio*) untuk mengambil paragraf inti berita."
            },
            {
                "day": "Rabu, 5 Agustus 2026",
                "plan": "Merancang dan membangun modul pencegahan duplikasi artikel *Hybrid Deduplicator* di `src/dedup/deduplicator.py`.",
                "result": "Terbentuknya mekanisme deduplikasi dua tahap: Lapis 1 (MD5 Hash URL) dan Lapis 2 (Fuzzy Text Matching menggunakan RapidFuzz).",
                "obstacle": "Media sindikasi sering menerbitkan berita yang sama persis namun dengan URL dan judul yang sedikit diubah.",
                "solution": "Menggunakan algoritma `token_set_ratio` dari RapidFuzz dengan ambang batas kesamaan (*similarity threshold*) 85%."
            },
            {
                "day": "Kamis, 6 Agustus 2026",
                "plan": "Pengujian deduplikasi pada 150 artikel berita siber yang dikumpulkan selama 3 hari terakhir.",
                "result": "Deduplicator berhasil mendeteksi dan mengeliminasi 42 artikel duplikat dari berbagai media sindikasi nasional tanpa kehilangan berita unik.",
                "obstacle": "Komparasi teks penuh (full-text) memakan waktu lama saat jumlah data historis di database semakin bertambah.",
                "solution": "Membatasi komparasi fuzzy string matching hanya pada artikel yang diterbitkan dalam rentang waktu 72 jam terakhir."
            },
            {
                "day": "Jumat, 7 Agustus 2026",
                "plan": "Evaluasi kinerja pipeline scraping dan pengarsipan berkas log harian (`logs/2026-08-04.log`).",
                "result": "Pipeline berjalan stabil tanpa crash; mencatatkan 1.657 baris aktivitas penarikan data dan ekstraksi di log.",
                "obstacle": "Koneksi internet kantor sempat drop sesaat yang menyebabkan proses scraping terhenti di tengah jalan.",
                "solution": "Menambahkan exception handling komprehensif pada perulangan sumber agar kegagalan 1 feed tidak menggagalkan feed lainnya."
            }
        ],
        "tech_reflection": "Implementasi RapidFuzz terbukti ampuh menyaring berita duplikat dari media sindikasi (misal antara AntaraNews, Detik, dan Kompas). Arsitektur perayapan menjadi jauh lebih tangguh dengan penanganan error terisolasi per sumber berita.",
        "supervisor_note": "Pencegahan duplikasi bekerja efektif. Lanjutkan integrasi pengumpulan data CVE dari sumber resmi."
    },

    # MINGGU 8
    {
        "week_num": 8,
        "date_range": "10 Agustus 2026 – 14 Agustus 2026",
        "theme": "Integrasi Pelacakan CVE (NVD API) & Evaluasi Kualitas Komparasi Ringkasan Model Lokal",
        "phase": "Fase II: Pengembangan Arsitektur Awal & Model Lokal",
        "days": [
            {
                "day": "Senin, 10 Agustus 2026",
                "plan": "Mengembangkan modul pengambil kerentanan software `src/scraper/cve_fetcher.py` terhubung ke API NIST NVD versi 2.0.",
                "result": "Modul mampu mengambil daftar kerentanan CVE terbaru, skor keparahan CVSS v3.1, deskripsi, dan software terdampak (CPE).",
                "obstacle": "API NVD NIST memiliki batas rate limit ketat (hanya 5 request per 30 detik tanpa API key khusus).",
                "solution": "Menambahkan delay otomatis antar request dan mengajukan NVD API Key resmi untuk meningkatkan kuota."
            },
            {
                "day": "Selasa, 11 Agustus 2026",
                "plan": "Menerapkan filter kerentanan CVE kritis: hanya memproses CVE dengan skor CVSS >= 7.0 (High dan Critical).",
                "result": "Tersaringnya puluhan CVE kritis harian; data disimpan sementara ke database untuk dianalisis oleh modul AI.",
                "obstacle": "Deskripsi CVE dari NVD sepenuhnya berbahasa Inggris dengan jargon teknis kode pemrograman yang sangat padat.",
                "solution": "Merancang prompt khusus penerjemahan teknis dan peringkasan dampak eksploitasi ke dalam Bahasa Indonesia."
            },
            {
                "day": "Rabu, 12 Agustus 2026",
                "plan": "Menjalankan eksperimen komparasi kualitas peringkasan berita dan CVE menggunakan model lokal pada dataset uji riil.",
                "result": "Terekspornya dataset evaluasi ke berkas `data/cek_ringkasan_cve_1.csv` dan `data/perbandingan_ringkasan_v2_1.csv` (615 entri data).",
                "obstacle": "Model lokal Ollama sering kali hanya menyalin potongan kalimat depan tanpa memahami kronologi insiden.",
                "solution": "Menambahkan metrik pengecekan panjang ringkasan dan rasio kemiripan leksikal untuk mendeteksi kecurangan ekstraktif model."
            },
            {
                "day": "Kamis, 13 Agustus 2026",
                "plan": "Audit hasil ringkasan CVE bersama rekan magang untuk menilai nilai guna informasi bagi analis CSIRT.",
                "result": "Ditemukan bahwa sebagian besar CVE yang ditarik adalah kerentanan firmware hardware jaringan enterprise global yang tidak relevan dengan server OPD Jatim.",
                "obstacle": "Analis merasa terbebani oleh banyaknya kartu CVE yang tidak aplikatif bagi pengamanan website pemerintah daerah.",
                "solution": "Mencatat temuan ini sebagai bahan pertimbangan kritis mengenai relevansi modul CVE dalam jangka panjang."
            },
            {
                "day": "Jumat, 14 Agustus 2026",
                "plan": "Konsolidasi kode sumber dan persiapan inisialisasi repositori version control Git resmi.",
                "result": "Struktur direktori dirapikan, modul-modul backend dipersiapkan untuk commit perdana proyek.",
                "obstacle": "Banyak berkas sampah temporer dan berkas cache model yang tidak boleh ter-commit ke Git.",
                "solution": "Menyusun berkas `.gitignore` komprehensif mengabaikan virtualenv, folder cache, dan database lokal."
            }
        ],
        "tech_reflection": "Minggu ini menghasilkan dataset komparasi ringkasan riil (`perbandingan_ringkasan_v2_1.csv`). Analisis kualitatif mulai menunjukkan sinyal bahwa integrasi data CVE unpatched pihak ketiga menimbulkan *noise* yang tinggi dan kurang menyentuh kebutuhan perlindungan website instansi daerah.",
        "supervisor_note": "Data evaluasi CSV sudah terkumpul dengan baik. Perhatikan relevansi informasi CVE bagi target instansi pemerintah kita."
    },

    # MINGGU 9
    {
        "week_num": 9,
        "date_range": "17 Agustus 2026 – 21 Agustus 2026",
        "theme": "Inisialisasi Version Control Git Resmi (v1.0.0, 20 Agustus 2026) & UI Dashboard Awal",
        "phase": "Fase III: Version Control, Integrasi Awal & Evaluasi Paruh Waktu",
        "days": [
            {
                "day": "Senin, 17 Agustus 2026",
                "plan": "Hari Libur Nasional Peringatan Kemerdekaan Republik Indonesia ke-81 (Melakukan persiapan mandiri struktur kode repositori).",
                "result": "Rancangan arsitektur repositori Git, modularisasi package `src/`, dan penyiapan file `requirements.txt` mandiri.",
                "obstacle": "Penyesuaian dependensi library agar kompatibel antar lingkungan workstation magang dan laptop pribadi.",
                "solution": "Mengunci versi dependensi library Python di file requirements.txt."
            },
            {
                "day": "Selasa, 18 Agustus 2026",
                "plan": "Membangun endpoint API FastAPI di `src/web/app.py` untuk melayani data berita terkini dan arsip riwayat.",
                "result": "Endpoint `/api/terkini`, `/api/arsip`, dan router Jinja2 template berhasil diuji coba; pencatatan log di `logs/2026-08-18.log`.",
                "obstacle": "Penanganan CORS (Cross-Origin Resource Sharing) dan routing static files di FastAPI.",
                "solution": "Menambahkan middleware CORSMiddleware dan mengonfigurasi static files mount `/static`."
            },
            {
                "day": "Rabu, 19 Agustus 2026",
                "plan": "Membangun tampilan antarmuka web awal (`src/web/templates/index.html`) berbasis framework Tailwind CSS.",
                "result": "Dashboard web memuat Tab Beranda, kartu daftar berita siber, feed CVE, dan modal baca detail artikel; log masif tercatat di `logs/2026-08-19.log`.",
                "obstacle": "Tampilan antarmuka awal masih tampak standar dan belum memiliki identitas resmi CSIRT Pemprov Jatim.",
                "solution": "Mencatat rencana perombakan desain visual (UI Redesign) pada fase berikutnya."
            },
            {
                "day": "Kamis, 20 Agustus 2026",
                "plan": "Melakukan inisialisasi repositori Git resmi dan rilis perdana proyek SiberHarian (v1.0.0).",
                "result": "Commit perdana berhasil dilakukan: `commit f1786aa - first commit` (72 berkas, +15.488 baris kode); log harian mencatat aktivitas di `logs/2026-08-20.log`.",
                "obstacle": "Konfigurasi remote repository GitHub dan penataan izin branch perlindungan kode.",
                "solution": "Menghubungkan remote GitHub repositori dan menetapkan branch `main` sebagai lini rilis resmi proyek."
            },
            {
                "day": "Jumat, 21 Agustus 2026",
                "plan": "Uji coba integrasi end-to-end v1.0.0: eksekusi scraping otomatis dan penampilan hasilnya di browser lokal.",
                "result": "Sistem berhasil berjalan end-to-end: artikel berita dan CVE tersimpan di SQLite dan muncul di tampilan web secara dinamis.",
                "obstacle": "Pengguna harus melakukan refresh halaman secara manual untuk melihat progres penarikan berita terbaru.",
                "solution": "Merencanakan pembuatan mekanisme streaming log terminal menggunakan Server-Sent Events (SSE) agar progres terpantau real-time."
            }
        ],
        "tech_reflection": "Minggu ke-9 menandai kelahiran resmi basis kode proyek SiberHarian di GitHub (`f1786aa`). Versi 1.0.0 membuktikan kelayakan teknis pengumpulan data dan penyajian antarmuka web, meletakkan fondasi kokoh untuk pengembangan modul analitik lanjutan.",
        "supervisor_note": "Selamat atas rilis perdana v1.0.0 di Git. Dashboard sudah berfungsi, namun aspek kepatuhan hukum dan tampilan visual perlu ditingkatkan."
    },

    # MINGGU 10
    {
        "week_num": 10,
        "date_range": "24 Agustus 2026 – 28 Agustus 2026",
        "theme": "Rilis Git v2 (24 Agustus 2026), Terminal SSE Monitor & Evaluasi Kepatuhan Hak Cipta Pers (UU No. 28/2014)",
        "phase": "Fase III: Version Control, Integrasi Awal & Evaluasi Paruh Waktu",
        "days": [
            {
                "day": "Senin, 24 Agustus 2026",
                "plan": "Mengembangkan fitur Server-Sent Events (SSE) di endpoint `/api/stream/pipeline` dan konsol terminal monitor melayang (floating terminal).",
                "result": "Commit Git berhasil dilakukan: `commit cc96e8d - update v2` (+5.281 baris penambahan kode); terminal monitor real-time beroperasi.",
                "obstacle": "Koneksi SSE sempat putus saat browser beralih ke tab background atau saat jaringan tidak stabil.",
                "solution": "Menambahkan mekanisme *auto-reconnect* pada frontend `main.js` dengan jeda interval 3 detik jika event stream terputus."
            },
            {
                "day": "Selasa, 25 Agustus 2026",
                "plan": "Mengembangkan tab visualisasi Tren Analitik awal (`src/web/static/js/tren.js` dan `src/web/templates/partials/_tren.html`).",
                "result": "Tab Tren menampilkan grafik distribusi kategori ancaman siber dan tren volume CVE mingguan menggunakan Chart.js.",
                "obstacle": "Query agregasi SQL lambat saat menghitung frekuensi kategori ancaman dari seluruh riwayat artikel.",
                "solution": "Menambahkan indeks komposit `idx_berita_kategori_tgl` pada tabel `berita` untuk mempercepat agregasi grafik mingguan."
            },
            {
                "day": "Rabu, 26 Agustus 2026",
                "plan": "Sesi peninjauan kemajuan sistem (Progress Review) bersama Pembimbing Lapangan di Bidang Keamanan Informasi Diskominfo Jatim.",
                "result": "Demonstrasi fitur v2 mendapat apresiasi, namun memicu diskusi mendalam mengenai aspek legalitas dan etika publikasi informasi.",
                "obstacle": "Pembimbing menegaskan peringatan keras: Diskominfo tidak boleh mempublikasikan konten yang melanggar hak cipta penerbit berita pers (UU No. 28 Tahun 2014).",
                "solution": "Mencatat mandat wajib: sistem TIDAK BOLEH melakukan copy-paste teks berita, ringkasan WAJIB berupa parafrase faktual murni dengan atribusi sumber."
            },
            {
                "day": "Kamis, 27 Agustus 2026",
                "plan": "Analisis yuridis dan teknis kepatuhan UU Hak Cipta No. 28/2014 Pasal 43 huruf c (pengutipan untuk kepentingan pendidikan dan keamanan).",
                "result": "Merumuskan standar kepatuhan sistem: (1) Parafrase mandiri non-ekstraktif, (2) Atribusi nama media dan tautan asli, (3) Pembatasan panjang ringkasan maksimal 3 poin.",
                "obstacle": "Model bahasa lokal kerap menyalin kalimat pertama atau kedua artikel persis seperti aslinya karena prompting yang terlalu longgar.",
                "solution": "Merancang arsitektur prompt baru dengan batasan larangan penyalinan kata perkata (*strict non-copy constraint*)."
            },
            {
                "day": "Jumat, 28 Agustus 2026",
                "plan": "Eksperimen awal penulisan prompt parafrase faktual (*factual paraphrasing prompt*) pada modul summarizer.",
                "result": "Draf prompt baru mewajibkan AI menyarikan: Entitas Terdampak, Vektor Serangan, dan Rekomendasi/Dampak secara padat.",
                "obstacle": "Terkadang AI melakukan parafrase yang terlalu bebas hingga mengubah fakta kronologi insiden (halusinasi halus).",
                "solution": "Menetapkan aturan *Chain-of-Thought*: model wajib mengekstrak fakta kunci terlebih dahulu sebelum merangkainya menjadi narasi parafrase."
            }
        ],
        "tech_reflection": "Minggu ke-10 memberikan kesadaran krusial bahwa rekayasa perangkat lunak sektor publik tidak hanya soal fungsionalitas kode, melainkan kepatuhan hukum (*regulatory compliance*). Mandat penegakan parafrase faktual untuk mematuhi UU Hak Cipta No. 28/2014 menjadi pivot kualitas konten sistem.",
        "supervisor_note": "Fitur terminal SSE sangat bagus dan interaktif. Arahan mengenai kepatuhan hak cipta pers wajib diimplementasikan tanpa kompromi."
    },

    # MINGGU 11
    {
        "week_num": 11,
        "date_range": "31 Agustus 2026 – 4 September 2026",
        "theme": "Rilis Git v3 (1 September 2026), Penegakan Aturan Parafrase Faktual Ketat & Dokumentasi PRODUCT.md",
        "phase": "Fase III: Version Control, Integrasi Awal & Evaluasi Paruh Waktu",
        "days": [
            {
                "day": "Senin, 31 Agustus 2026",
                "plan": "Implementasi modul pembersih teks dan verifikator parafrase di `src/utils/llm_text_cleaner.py` dan `src/summarizer/llm_summarizer.py`.",
                "result": "Sistem secara otomatis memvalidasi bahwa ringkasan hasil AI memiliki indeks leksikal berbeda dengan teks sumber artikel.",
                "obstacle": "Mendeteksi apakah ringkasan merupakan parafrase asli atau sekadar penyalinan sebagian kalimat.",
                "solution": "Menghitung skor kesamaan Levenshtein antara kalimat ringkasan dan kalimat teks asli; me-reject jika kesamaan >60%."
            },
            {
                "day": "Selasa, 1 September 2026",
                "plan": "Melakukan commit Git `update v3` (commit 98a42e7) dan menyusun dokumen visi produk resmi `PRODUCT.md`.",
                "result": "Commit v3 berhasil; terbitnya berkas `PRODUCT.md` yang menetapkan visi, positioning, sasaran pengguna, dan komitmen mutu sistem SiberHarian.",
                "obstacle": "Mendefinisikan persona pengguna secara tegas agar fitur tidak tumpang tindih antara kebutuhan warga dan analis.",
                "solution": "Mendefinisikan 2 persona pengguna: Pengunjung Publik (edukasi & statistik fakta) dan Analis CTI CSIRT Jatim (taktis & operasional)."
            },
            {
                "day": "Rabu, 2 September 2026",
                "plan": "Pembersihan repository Git: menghapus berkas-berkas `__pycache__` yang sempat ter-track dan memperbarui `.gitignore`.",
                "result": "Repositori menjadi bersih dan ringan; mengeliminasi lebih dari 15 berkas bytecode cache yang tidak diperlukan.",
                "obstacle": "Git cache masih melacak file pycache lama meskipun `.gitignore` telah diperbarui.",
                "solution": "Menjalankan perintah `git rm -r --cached` untuk membersihkan indeks file yang terabaikan secara tuntas."
            },
            {
                "day": "Kamis, 3 September 2026",
                "plan": "Menambahkan filter guardrail semantik (*Semantic Role Separation*) pada modul ekstraksi entitas berita siber.",
                "result": "Model AI mampu membedakan dengan tegas antara nama entitas pelapor/peneliti keamanan (vendor) vs nama aktor penyerang.",
                "obstacle": "Pada beberapa artikel berita, vendor pelapor (misal Kaspersky, Mandiant) keliru diringkas sebagai pelaku yang melancarkan serangan.",
                "solution": "Menambahkan negative constraint eksplisit pada prompt: 'Pihak peneliti/vendor yang menganalisis insiden BUKAN aktor penyerang'."
            },
            {
                "day": "Jumat, 4 September 2026",
                "plan": "Pengujian stabilitas pipeline harian v3 dengan menjalankan perayapan artikel berita siber skala penuh.",
                "result": "Sebanyak 48 artikel berita berhasil diringkas dengan aturan parafrase faktual baru; rata-rata kemiripan teks dengan artikel asli turun ke 28%.",
                "obstacle": "Model lokal Ollama mulai menunjukkan tanda-tanda ketidakstabilan saat antrean berita melebihi 40 artikel berturut-turut.",
                "solution": "Mencatat kelemahan performa model lokal ini sebagai bahan laporan resmi untuk evaluasi tengah periode (Mid-term)."
            }
        ],
        "tech_reflection": "Penegakan aturan parafrase faktual di v3 sukses mengatasi risiko plagiasi berita pers. Visi produk yang dituangkan dalam `PRODUCT.md` memperjelas arah strategis sistem: menyajikan intelijen yang dapat dipertanggungjawabkan bagi pemerintah dan publik.",
        "supervisor_note": "Dokumen PRODUCT.md sangat jelas dan terarah. Kualitas ringkasan parafrase sudah jauh lebih baik dan aman secara hukum."
    },

    # MINGGU 12
    {
        "week_num": 12,
        "date_range": "7 September 2026 – 11 September 2026",
        "theme": "Rilis Git v4 (10 September 2026), Audit Feed RSS, Penambahan Identitas Resmi & Evaluasi Tengah Periode (Mid-Term)",
        "phase": "Fase III: Version Control, Integrasi Awal & Evaluasi Paruh Waktu",
        "days": [
            {
                "day": "Senin, 7 September 2026",
                "plan": "Mengembangkan skrip audit kualitas feed RSS `scripts/debug/audit_feeds.py` untuk menguji kesehatan seluruh sumber berita.",
                "result": "Skrip audit mampu memeriksa status HTTP, kecepatan respon feed, frekuensi pembaruan, dan rasio derau konten.",
                "obstacle": "Beberapa feed RSS media nasional ternyata sudah tidak diperbarui selama berminggu-minggu namun tetap memicu request kosong.",
                "solution": "Menghasilkan laporan audit `audit_feed_report.json` dan mengeliminasi 8 endpoint feed yang mati atau tidak aktif."
            },
            {
                "day": "Selasa, 8 September 2026",
                "plan": "Menambahkan aset logo resmi CSIRT Diskominfo Jatim (`src/web/static/img/Logo.png`) dan menata header navigasi portal.",
                "result": "Tampilan visual portal memiliki identitas resmi instansi Pemerintah Provinsi Jawa Timur.",
                "obstacle": "Ukuran file logo mentah beresolusi sangat besar (1.8 MB) yang memperlambat loading awal halaman web.",
                "solution": "Mengoptimalkan kompresi gambar dan menyesuaikan aspect ratio navbar agar responsif di layar mobile dan desktop."
            },
            {
                "day": "Rabu, 9 September 2026",
                "plan": "Persiapan berkas presentasi dan laporan evaluasi tengah periode (Mid-Term Review) magang.",
                "result": "Slide presentasi tengah periode merangkum pencapaian v1.0.0 s.d. v4.0.0, perbandingan data ringkasan, dan kendala komputasi lokal.",
                "obstacle": "Merumuskan argumen objektif mengapa arsitektur model lokal saat ini perlu dimigrasikan ke Cloud API.",
                "solution": "Menyajikan data empiris latensi (35 detik vs <2 detik) dan grafik beban hardware (RAM 94%, GPU panas) sebagai justifikasi teknis."
            },
            {
                "day": "Kamis, 10 September 2026",
                "plan": "Melakukan commit Git `update v4` (commit bd271f4) dan melaksanakan sidang presentasi evaluasi tengah periode magang.",
                "result": "Commit v4 berhasil (+4.807 baris kode); presentasi evaluasi tengah periode berlangsung di hadapan Pembimbing dan Tim Analis CSIRT.",
                "obstacle": "Dua kritik tajam dari tim analis: (1) Eksekusi lokal terlalu lambat untuk briefing pagi, (2) Data CVE global tidak relevan untuk web instansi Pemprov Jatim.",
                "solution": "Mendapatkan persetujuan pimpinan untuk meriset opsi migrasi ke Google Gemini API dan merencanakan pembersihan modul CVE."
            },
            {
                "day": "Jumat, 11 September 2026",
                "plan": "Konsolidasi hasil evaluasi tengah periode dan perumusan rencana aksi perombakan arsitektur fase kedua (minggu 13-18).",
                "result": "Tersusunnya roadmap perbaikan besar: migrasi AI ke Cloud API, adopsi standar UI CSIRT Jatim, dan transformasi fokus ke sektor IIV.",
                "obstacle": "Menjaga agar transisi arsitektur tidak merusak basis data historis artikel yang sudah terkumpul di `state.db`.",
                "solution": "Menyiapkan skema migrasi database bertahap dengan mekanisme pencadangan berkas `state.db.bak`."
            }
        ],
        "tech_reflection": "Evaluasi tengah periode (Minggu ke-12) menjadi titik balik paling krusial dalam proyek. Dua masalah fundamental diakui secara terbuka: keterbatasan model lokal Ollama dan ketidakrelevanan modul CVE. Keputusan untuk bertransformasi disahkan oleh pembimbing lapangan.",
        "supervisor_note": "Evaluasi paruh waktu memuaskan. Langkah yang tepat untuk berani melakukan pivot teknis demi relevansi produk bagi kebutuhan nyata dinas."
    },

    # MINGGU 13
    {
        "week_num": 13,
        "date_range": "14 September 2026 – 18 September 2026",
        "theme": "Rilis Git v5 (15 September 2026), Inisialisasi RAG Engine, Modularisasi Frontend & Adopsi Antislop UI",
        "phase": "Fase IV: Refactoring AI, Kepatuhan Legal & Standarisasi UI",
        "days": [
            {
                "day": "Senin, 14 September 2026",
                "plan": "Mengembangkan modul RAG awal `src/analytics/rag_engine.py` untuk menghubungkan analisis ancaman dengan korpus mitigasi resmi.",
                "result": "Fondasi engine RAG terpasang; merancang mekanisme penarikan dokumen rujukan untuk memperkaya prompt generasi rekomendasi.",
                "obstacle": "Format dokumen referensi keamanan siber yang tersebar dan belum terstandarisasi dalam format mesin.",
                "solution": "Menginisialisasi perancangan berkas ensiklopedia JSON terstruktur mencakup framework MITRE ATT&CK dan NIST."
            },
            {
                "day": "Selasa, 15 September 2026",
                "plan": "Melakukan refactoring besar frontend JavaScript dari monolitik `tren.js` menjadi 6 modul terpisah dan commit Git `update v5` (commit 8bddc2f).",
                "result": "Commit v5 berhasil (+5.778 baris penambahan); terpecahnya kode ke `tren-ai-cards.js`, `tren-charts.js`, `tren-kpi.js`, `tren-tables.js`, `tren-wilayah.js`, `tren-pdf-exporter.js`.",
                "obstacle": "Ketergantungan variabel global antar modul JavaScript yang sempat menyebabkan error `Uncaught ReferenceError` di browser.",
                "solution": "Menerapkan namespace modular terstruktur (`window.TrenKpi`, `window.TrenCharts`) dengan dependency injection bersih."
            },
            {
                "day": "Rabu, 16 September 2026",
                "plan": "Mengembangkan modul ekspor laporan resmi mingguan ke format PDF langsung dari peramban web (`tren-pdf-exporter.js`).",
                "result": "Fitur cetak PDF resmi beroperasi dengan kop resmi CSIRT Jatim, format SITREP rapi, tabel indikator risiko, dan lembar pengesahan.",
                "obstacle": "Page-break PDF yang memotong tabel dan kartu analitik di tengah-tengah halaman cetak.",
                "solution": "Menerapkan aturan CSS cetak `@media print` dengan properti `break-inside: avoid` pada setiap kartu analitik."
            },
            {
                "day": "Kamis, 17 September 2026",
                "plan": "Mempelajari dan mengadopsi prinsip desain antislop UI (`antislop.md`) untuk memastikan antarmuka tidak terkesan murahan (*AI-generated slop*).",
                "result": "Menjalankan skrip audit kontras warna `skills/antislop-human/contrast-check.py` pada seluruh elemen teks dan background portal.",
                "obstacle": "Beberapa badge label pada dashboard gelap memiliki rasio kontras < 4.5:1 yang melanggar standar aksesibilitas WCAG.",
                "solution": "Menyesuaikan palet warna teks ke `#e0f0ff` terhadap background Dark Navy `#0a1628`, mencapai rasio kontras 15.6:1 (Standar WCAG AAA)."
            },
            {
                "day": "Jumat, 18 September 2026",
                "plan": "Penyusunan berkas panduan desain `DESIGN.md` yang merumuskan bahasa visual resmi *Cyber-HUD / Tactical Dark Terminal Edition*.",
                "result": "Dokumen `DESIGN.md` disahkan, menetapkan font `Sora` untuk headline narasi dan `Fragment Mono` untuk data metrik teknis.",
                "obstacle": "Memastikan font Google Fonts tetap dapat di-render dengan cepat pada koneksi internet terbatas.",
                "solution": "Menerapkan font display `swap` dan preconnect ke server font CDN."
            }
        ],
        "tech_reflection": "Modularisasi frontend di v5 merupakan langkah rekayasa perangkat lunak yang sangat matang. Menghilangkan kode monolitik ribuan baris membuat pengembangan visualisasi jauh lebih cepat dan terisolasi dari potensi regresi bug.",
        "supervisor_note": "Fitur cetak PDF resmi sangat bermanfaat bagi analis untuk bahan laporan pimpinan. Tampilan UI semakin profesional."
    },

    # MINGGU 14
    {
        "week_num": 14,
        "date_range": "21 September 2026 – 25 September 2026",
        "theme": "Rilis Git v6 & v7 (23-27 September 2026), PIVOT AI (Migrasi Ollama ke Gemini Cloud API), RBAC & Kepatuhan Legal",
        "phase": "Fase IV: Refactoring AI, Kepatuhan Legal & Standarisasi UI",
        "days": [
            {
                "day": "Senin, 21 September 2026",
                "plan": "Membangun adaptor Cloud API LLM `src/utils/llm_adapter.py` untuk mengintegrasikan Google Gemini API dengan sistem fallback bertingkat.",
                "result": "Adaptor Gemini mendukung rantai fallback otomatis: `gemini-3.1-flash-lite` -> `gemini-3.5-flash-lite` -> `gemini-3.5-flash` -> `gemini-3.7-flash`.",
                "obstacle": "Penanganan kuota permintaan per menit (Rate Limit / HTTP 429 Too Many Requests) pada Gemini API tier gratis/berbayar.",
                "solution": "Mengimplementasikan algoritma *Exponential Backoff with Jitter* dan *Token Bucket Rate Limiter* pada modul adapter."
            },
            {
                "day": "Selasa, 22 September 2026",
                "plan": "Mengintegrasikan Semantic Vector Embeddings menggunakan model `text-embedding-004` di `src/utils/embedding_adapter.py`.",
                "result": "Engine RAG kini mampu melakukan pencarian semantik vektor dokumen siber dengan fallback mulus ke pencarian leksikal RapidFuzz.",
                "obstacle": "Dimensi vektor embedding yang besar berpotensi memperlambat penyimpanan jika menggunakan basis data terpisah.",
                "solution": "Menyimpan representasi vektor dalam format BLOB serialized di SQLite dengan indeks cosine similarity komputasi cepat."
            },
            {
                "day": "Rabu, 23 September 2026",
                "plan": "Melakukan commit Git `update v6` (commit 20a6eed, +6.645 baris kode) dan mengintegrasikan 12 framework ensiklopedia siber (165 entitas).",
                "result": "Integrasi berkas JSON ensiklopedia: MITRE ATT&CK, D3FEND, NIST CSF 2.0, OWASP Top 10, CWE, CIS Controls, BSSN CSIRT, Indeks KAMI.",
                "obstacle": "Validasi integritas data: memastikan seluruh kode taktik dan teknik MITRE benar-benar ada dan tidak terdistorsi.",
                "solution": "Menulis suite unit test `tests/test_25_case_studies.py` untuk memvalidasi keakuratan mapping ensiklopedia terhadap 25 studi kasus siber riil."
            },
            {
                "day": "Kamis, 24 September 2026",
                "plan": "Membangun modul kepatuhan web scraping `src/scraper/robots_checker.py` dan menetapkan User-Agent resmi CSIRT Jatim.",
                "result": "Sistem secara otomatis memeriksa izin perayapan di `robots.txt` situs media sebelum mengunduh artikel; User-Agent transparan mencantumkan kontak dinas.",
                "obstacle": "Beberapa situs berita memiliki aturan robots.txt yang rumit dengan wildcard path berulang.",
                "solution": "Menggunakan modul `urllib.robotparser` standar dengan penanganan cache respon robots.txt selama 24 jam."
            },
            {
                "day": "Jumat, 25 September 2026",
                "plan": "Membangun sistem autentikasi Role-Based Access Control (RBAC) di `src/utils/admin_auth.py`, halaman `login.html`, `admin.html`, dan panel `_settings.html`.",
                "result": "Sistem mendukung 2 peran: Superadmin dan Viewer dengan enkripsi password menggunakan `bcrypt`; konfigurasi sistem kini dapat diedit via UI.",
                "obstacle": "Manajemen sesi otentikasi stateless pada FastAPI tanpa memberatkan database server.",
                "solution": "Menerapkan HTTP-only Secure Cookies dengan token sesi yang divalidasi pada setiap request endpoint terlindungi."
            }
        ],
        "tech_reflection": "Migrasi dari Ollama lokal ke Google Gemini API (v6 & v7) merupakan lonjakan performa paling masif dalam proyek: waktu pemrosesan artikel terpangkas dari 35 detik menjadi 1.8 detik (peningkatan kecepatan 19x lipat). Integrasi RBAC dan kepatuhan legal robots.txt melengkapi standar platform enterprise instansi.",
        "supervisor_note": "Peningkatan kecepatan inferensi luar biasa. Keberadaan User-Agent resmi dan pemeriksaan robots.txt menunjukkan tata kelola etika IT yang sangat baik."
    },

    # MINGGU 15
    {
        "week_num": 15,
        "date_range": "28 September 2026 – 2 Oktober 2026",
        "theme": "Rilis Git v8 & v9 (28-29 September 2026, v3.0.0), PIVOT FUNDAMENTAL (Eradikasi CVE, Adopsi 10 Sektor IIV Perpres 82/2022) & Redesign UI Total",
        "phase": "Fase V: Pivot Fundamental CTI, Adopsi Sektor IIV & Redesign Total",
        "days": [
            {
                "day": "Senin, 28 September 2026",
                "plan": "Melakukan commit Git `update v8` (commit 03c8595): penyempurnaan UI admin dan publik serta persiapan rilis fundamental v3.0.0.",
                "result": "Tampilan antarmuka semakin matang; perbaikan bug tampilan modal detail berita dan penataan tab beranda publik dinamis.",
                "obstacle": "Masih adanya sisa dependensi elemen visual CVE pada template HTML yang berpotensi memicu error JavaScript jika dihapus mendadak.",
                "solution": "Melakukan inventarisasi seluruh selector DOM dan fungsi terkait CVE untuk pembersihan menyeluruh."
            },
            {
                "day": "Selasa, 29 September 2026",
                "plan": "EKSEKUSI PIVOT UTAMA & RILIS RESMI SIBERHARIAN v3.0.0 (commit Git `update v9` - 9b1aceb): Eradikasi total modul CVE dan adopsi Sektor IIV.",
                "result": "Menghapus berkas `src/scraper/cve_fetcher.py` (-680 baris) dan seluruh konfigurasi CVE; merampingkan `config.yaml` dari 671 ke 330 baris; mengadopsi 10 Sektor IIV Perpres 82/2022.",
                "obstacle": "Menghitung ulang metrik analitik historis yang sebelumnya bergantung pada volume CVE dan skor CVSS.",
                "solution": "Merumuskan formula baru Indeks Postur Ancaman murni CTI: `0.45 * Frekuensi Insiden + 0.30 * Vektor Serangan TTPs + 0.25 * Paparan Sektor Vital IIV`."
            },
            {
                "day": "Rabu, 30 September 2026",
                "plan": "Restrukturisasi Laporan SITREP CTI menjadi 5 Modul Terpadu tanpa tab pemisah Berita vs CVE.",
                "result": "Laporan SITREP AI menghasilkan 5 analisis terstruktur: (1) Makro Tren Insiden, (2) Lanskap Mikro & Aktor, (3) Vektor Serangan & MITRE ATT&CK, (4) Rekomendasi Preskriptif D3FEND/NIST, (5) Sinyal Ancaman Baru.",
                "obstacle": "Mencegah duplikasi rekomendasi mitigasi antar modul laporan analitik CTI.",
                "solution": "Menerapkan pendekatan SIMP (*Sequential Isolated Micro-Prompts*) dengan context passing ringkas antar tahapan inferensi."
            },
            {
                "day": "Kamis, 1 Oktober 2026",
                "plan": "Penyelarasan menyeluruh desain visual antarmuka portal dengan tema resmi portal CSIRT Jatim (`csirt_jatim.md`).",
                "result": "Implementasi Cyber-HUD Dark Theme: Background Navy `#0a1628`, elevated surface `#0d2137`, cyan glow `#00d4ff`, green neon `#00ff9d`, dan sudut potong chamfer 10px.",
                "obstacle": "Menjaga agar elemen chamfer (sudut terpotong 10px) tampil sempurna dan konsisten lintas peramban (Chrome, Edge, Firefox).",
                "solution": "Menerapkan CSS `clip-path: polygon()` terstandar pada class utility antarmuka."
            },
            {
                "day": "Jumat, 2 Oktober 2026",
                "plan": "Evaluasi rilis v3.0.0 bersama Pembimbing Lapangan dan penelaahan dampak perubahan terhadap efisiensi kerja tim SOC.",
                "result": "Tim analis CSIRT menyambut sangat positif: hilangnya noise CVE membuat dashboard 100% fokus pada insiden nyata yang mengancam sektor pemerintahan, kesehatan, dan pendidikan Jawa Timur.",
                "obstacle": "Perlunya pembaruan dokumentasi teknis sistem dan changelog resmi untuk melacak sejarah keputusan arsitektur.",
                "solution": "Menyusun dokumentasi `CHANGELOG.md` v3.0.0 dengan standar *Keep a Changelog* dan berkas referensi `csirt_jatim.md`."
            }
        ],
        "tech_reflection": "Rilis v3.0.0 (Minggu ke-15) adalah pencapaian rekayasa sistem paling signifikan. Keberanian membuang 680 baris kode CVE yang bising dan menggantinya dengan 10 Sektor Infrastruktur Informasi Vital (Perpres No. 82/2022) mengubah SiberHarian dari sekadar agregator teknis biasa menjadi platform intelijen ancaman strategis yang sesungguhnya.",
        "supervisor_note": "Keputusan pivot ke sektor IIV sangat tepat sasaran dan selaras dengan mandat regulasi Perpres 82/2022. Ini adalah solusi nyata yang dibutuhkan Diskominfo Jatim."
    },

    # MINGGU 16
    {
        "week_num": 16,
        "date_range": "5 Oktober 2026 – 9 Oktober 2026",
        "theme": "Pengujian Komprehensif Sistem, Pengujian Anti-Halusinasi & Evaluasi Kuantitatif RAG (RAGAS Framework)",
        "phase": "Fase VI: Pengujian Menyeluruh, Evaluasi RAG & Penyusunan Laporan",
        "days": [
            {
                "day": "Senin, 5 Oktober 2026",
                "plan": "Menyusun dan mengeksekusi rangkaian pengujian unit dan integrasi otomatis (`pytest`).",
                "result": "Menulis dan menjalankan `tests/test_pipeline_e2e_integration.py`, `tests/test_web_endpoints.py`, dan `tests/test_kpi_dashboard_tren.py` (seluruh 59 test lolos / 100% PASS).",
                "obstacle": "Pengujian integrasi yang memanggil API eksternal rentan gagal jika terjadi fluktuasi koneksi internet.",
                "solution": "Menggunakan mocking HTTP fixtures pada `tests/fixtures/` untuk pengujian deterministik dan isolasi test suite."
            },
            {
                "day": "Selasa, 6 Oktober 2026",
                "plan": "Mengembangkan pengujian khusus anti-halusinasi CTI di `tests/test_anti_halusinasi_cti.py`.",
                "result": "Pengujian memvalidasi 3 guardrail: (1) Vendor pelapor tidak pernah menjadi pelaku, (2) Entitas korban sesuai korpus, (3) Seluruh kode teknik MITRE terverifikasi di ensiklopedia.",
                "obstacle": "Mendeteksi halusinasi halus pada nama varian malware baru yang belum ada di database lokal.",
                "solution": "Menerapkan ambang toleransi: nama malware baru diizinkan jika terbukti ada pada teks artikel sumber (*source grounding verification*)."
            },
            {
                "day": "Rabu, 7 Oktober 2026",
                "plan": "Melakukan evaluasi performa arsitektur RAG menggunakan kerangka kerja metrik RAGAS pada 50 sampel insiden siber riil.",
                "result": "Tercapainya metrik kuantitatif tinggi: Context Recall sebesar 0,97 dan Faithfulness sebesar 0,96; log tercatat di `logs/2026-10-07.log`.",
                "obstacle": "Menghitung metrik Faithfulness secara otomatis tanpa bias penilaian subyektif.",
                "solution": "Menggunakan metode dekomposisi klaim fakta (claim decomposition) dan verifikasi silang terhadap dokumen acuan ensiklopedia siber."
            },
            {
                "day": "Kamis, 8 Oktober 2026",
                "plan": "Pengujian skenario ekstrem (Edge Case Testing): skenario sepi berita, skenario lonjakan berita masif, dan skenario duplikasi sindikasi.",
                "result": "Berhasil lulus pada `tests/test_real_scenario_sepi.py`, `tests/test_real_scenario_lonjakan.py`, dan `tests/test_real_scenario_duplikat.py`.",
                "obstacle": "Pada kondisi 0 berita insiden dalam 24 jam, dasbor sempat menampilkan teks error 'No data available'.",
                "solution": "Menambahkan fallback status kondusif: menampilkan pesan 'Lanskap Siber Terpantau Aman / Pemantauan Rutin Berjalan' dengan rekomendasi preventif."
            },
            {
                "day": "Jumat, 9 Oktober 2026",
                "plan": "Stress testing endpoint agregasi statistik publik dan optimasi caching kueri basis data.",
                "result": "Endpoint `/api/statistik-publik` membukukan waktu respon rata-rata 3,2 milidetik pada database SQLite aktif berukuran >1,2 MB.",
                "obstacle": "Kueri agregasi kata kunci (Word Cloud) sempat memakan waktu >120 ms saat tabel berisi ribuan entri berita.",
                "solution": "Menerapkan kueri agregat berindeks dengan pemotongan stop-words Bahasa Indonesia secara in-memory."
            }
        ],
        "tech_reflection": "Pengujian kuantitatif dengan kerangka RAGAS membuktikan keandalan sistem secara ilmiah: Context Recall 0,97 dan Faithfulness 0,96. Angka ini memberikan legitimasi akademik yang kuat untuk laporan akhir dan membuktikan sistem bebas dari distorsi fakta siber.",
        "supervisor_note": "Hasil pengujian sangat memuaskan dan impresif. Skor anti-halusinasi 0,96 membuktikan sistem aman digunakan untuk briefing resmi pimpinan."
    },

    # MINGGU 17
    {
        "week_num": 17,
        "date_range": "12 Oktober 2026 – 16 Oktober 2026",
        "theme": "Penyusunan Laporan Akhir Capstone Design & Project, BAB I-III & Dokumentasi Admin CSIRT Jatim",
        "phase": "Fase VI: Pengujian Menyeluruh, Evaluasi RAG & Penyusunan Laporan",
        "days": [
            {
                "day": "Senin, 12 Oktober 2026",
                "plan": "Menyusun draft Laporan Akhir Capstone Design & Project: BAB I Pendahuluan lengkap dengan justifikasi latar belakang dan rujukan mutakhir.",
                "result": "Tersusunnya berkas `BAB I PENDAHULUAN.md` dan integrasi ke naskah Word `BAB I Lengkap - Dashboard Admin SiberHarian.docx`.",
                "obstacle": "Memastikan seluruh sitasi ilmiah merupakan jurnal bereputasi tinggi bidang CTI, RAG, dan keamanan sistem informasi publik.",
                "solution": "Mengompilasi 19 referensi jurnal internasional/nasional (2023-2026) dan membuat skrip generator RIS `scripts/generate_ris.py`."
            },
            {
                "day": "Selasa, 13 Oktober 2026",
                "plan": "Menyusun BAB II Landasan Teori (Decision Support System, CTI, RAG, Perpres No. 82/2022) dan BAB III Metodologi Penelitian.",
                "result": "Naskah `Laporan Akhir Capstone Design & Project_Updated.docx` terisi komprehensif pada Bab I, II, dan III; log tercatat di `logs/2026-10-13.log`.",
                "obstacle": "Sinkronisasi perubahan teks markdown dengan berkas naskah Word yang memiliki format template kampus yang kaku.",
                "solution": "Mengembangkan skrip otomatisasi Python `scripts/sync_docx_bab1.py` untuk menginjeksi teks terformat langsung ke elemen XML docx."
            },
            {
                "day": "Rabu, 14 Oktober 2026",
                "plan": "Menyusun Bab IV dan Bab V mengenai Arsitektur Sistem, Implementasi Komponen CTI, dan Analisis Hasil Evaluasi RAGAS.",
                "result": "Dokumentasi detail mengenai formula Threat Posture, arsitektur SIMP micro-prompts, dan grafik perbandingan performa model lokal vs Cloud API.",
                "obstacle": "Penyajian tabel perbandingan dan diagram alur sistem beresolusi tinggi agar tidak buram saat dicetak.",
                "solution": "Menggunakan format diagram vektor SVG dan merendernya ke PNG resolusi 300 DPI untuk lampiran dokumen."
            },
            {
                "day": "Kamis, 15 Oktober 2026",
                "plan": "Menyusun berkas dokumentasi teknis admin dan panduan operasional di folder `LAPORAN DASHBOARD ADMIN/`.",
                "result": "Tersusunnya panduan operasional analis CSIRT: tata cara eksekusi pipeline terminal, pengelolaan sumber RSS, dan manajemen prompt LLM.",
                "obstacle": "Membuat panduan teknis yang mudah dipahami baik oleh staf analis senior maupun teknisi junior SOC.",
                "solution": "Menyertakan screenshot antarmuka nyata dan petunjuk langkah-demi-langkah (*step-by-step troubleshooting*)."
            },
            {
                "day": "Jumat, 16 Oktober 2026",
                "plan": "Sesi bimbingan laporan akhir bersama Dosen Pembimbing Akademik dan Pembimbing Lapangan Diskominfo Jatim.",
                "result": "Naskah laporan akhir disetujui untuk maju ke tahap sidang penutupan magang; mendapatkan masukan perbaikan redaksional minor.",
                "obstacle": "Penyesuaian istilah asing: memastikan seluruh terminologi teknologi bahasa Inggris ditulis miring (*italic*) secara konsisten.",
                "solution": "Melakukan audit penelusuran kata otomatis menggunakan skrip Python regex untuk memformat kata miring."
            }
        ],
        "tech_reflection": "Penulisan laporan akhir mendokumentasikan seluruh perjalanan rekayasa sistem secara transparan: mulai dari latar belakang kebutuhan, komparasi algoritma, keputusan pivot arsitektur, hingga pembuktian metrik evaluasi. Proyek ini terdokumentasi secara saintifik dan aplikatif.",
        "supervisor_note": "Naskah laporan akhir tersusun sangat ilmiah dan sistematis. Hubungan antara teori RAG dan implementasi operasional di CSIRT Jatim tergambar gamblang."
    },

    # MINGGU 18
    {
        "week_num": 18,
        "date_range": "19 Oktober 2026 – 23 Oktober 2026",
        "theme": "Finalisasi Proyek, Demonstrasi Sistem di Hadapan Tim CSIRT Diskominfo Jatim, Serah Terima & Penutupan Magang",
        "phase": "Fase VII: Finalisasi, Serah Terima & Penutupan Magang",
        "days": [
            {
                "day": "Senin, 19 Oktober 2026",
                "plan": "Penyusunan naskah final Logbook Magang Resmi 18 Minggu dan penyiapan berkas demonstrasi langsung (*live demo*) sistem SiberHarian.",
                "result": "Logbook kegiatan terkompilasi lengkap dari Minggu ke-1 hingga Minggu ke-18; berkas siap cetak dalam format Microsoft Word (.docx).",
                "obstacle": "Memastikan tidak ada tanggal atau rincian kegiatan yang bertentangan dengan histori log dan commit Git.",
                "solution": "Melakukan verifikasi silang otomatis antara data logbook dengan stempel waktu commit Git dan berkas log harian di folder `logs/`."
            },
            {
                "day": "Selasa, 20 Oktober 2026",
                "plan": "Uji coba gladi bersih (*dry-run*) demonstrasi sistem SiberHarian di lingkungan server staging Diskominfo Provinsi Jawa Timur.",
                "result": "Seluruh alur operasional berjalan mulus: perayapan berita harian, parafrase faktual Gemini API, postur ancaman, dan ekspor laporan PDF resmi; log tercatat di `logs/2026-10-20.log`.",
                "obstacle": "Memastikan kestabilan koneksi internet saat proses inferensi Gemini API di depan audiens penguji.",
                "solution": "Menguji keandalan mekanisme fallback: simulasi pemutusan model utama berhasil dialihkan secara otomatis ke model cadangan tanpa interupsi UI."
            },
            {
                "day": "Rabu, 21 Oktober 2026",
                "plan": "Pelaksanaan Sidang Presentasi Akhir Magang dan Demonstrasi Sistem di hadapan Tim CSIRT, Kasi Keamanan Informasi, dan Kepala Bidang Persandian Diskominfo Jatim.",
                "result": "Presentasi akhir sukses besar; sistem SiberHarian mendapat apresiasi tinggi dari jajaran pimpinan Diskominfo Jatim sebagai inovasi CTI daerah yang aplikatif.",
                "obstacle": "Menjawab pertanyaan mendalam pejabat dinas mengenai jaminan keamanan kedaulatan data saat memanggil Cloud API.",
                "solution": "Menjelaskan bahwa data yang dikirim ke API murni berupa teks berita publik terbuka (OSINT) tanpa menyertakan kredensial atau data sensitif internal pemerintah."
            },
            {
                "day": "Kamis, 22 Oktober 2026",
                "plan": "Proses serah terima (*handover*) repositori kode sumber, basis data `state.db`, kredensial konfigurasi, dan dokumentasi administrasi sistem.",
                "result": "Penandatanganan Berita Acara Serah Terima (BAST) produk perangkat lunak SiberHarian kepada perwakilan Tim Teknis CSIRT Diskominfo Jawa Timur.",
                "obstacle": "Memastikan staf teknis dinas memahami prosedur pemeliharaan rutin dan pembaruan API key.",
                "solution": "Melakukan sesi transfer knowledge (knowledge transfer) dan menyerahkan dokumen manual operasional admin lengkap."
            },
            {
                "day": "Jumat, 23 Oktober 2026",
                "plan": "Penyelesaian administrasi penutupan magang, penandatanganan lembar penilaian kinerja, pengesahan logbook resmi, dan pelepasan magang.",
                "result": "Program magang 18 minggu selesai secara resmi dengan nilai kinerja istimewa; seluruh lembar pengesahan dan logbook kegiatan resmi ditandatangani.",
                "obstacle": "Rasa haru dan perpisahan dengan rekan-rekan tim analis dan staf Bidang Keamanan Informasi Diskominfo Jatim.",
                "solution": "Menyampaikan ucapan terima kasih tulus, apresiasi atas bimbingan selama 18 minggu, dan komitmen menjaga silaturahmi profesional."
            }
        ],
        "tech_reflection": "Minggu ke-18 menjadi penutup paripurna perjalanan 18 minggu magang. Proyek SiberHarian berhasil bertransformasi dari ide sederhana menjadi platform Cyber Threat Intelligence operasional berstandar enterprise yang diakui dan digunakan langsung oleh CSIRT Diskominfo Provinsi Jawa Timur.",
        "supervisor_note": "Kinerja mahasiswa luar biasa selama 18 minggu. Dedikasi, kemampuan teknis, dan etika kerja sangat tinggi. Produk SiberHarian memberikan kontribusi nyata bagi pertahanan siber Jawa Timur."
    }
]

print(f"Loaded {len(WEEKS_DATA)} weeks of detailed internship logbook data.")
