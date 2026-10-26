# -*- coding: utf-8 -*-
cyber_settings = """<!-- partials/_settings.html -->
<div class="space-y-6 animate-fade-in" x-data="settingsPanel()">
    <!-- Header -->
    <div class="flex flex-col md:flex-row md:items-end justify-between gap-4 border-b border-[#1a3a5c] pb-5">
        <div>
            <div class="inline-flex items-center gap-1.5 text-[11px] font-mono font-bold text-[#00ff9d] bg-[#0d2137] border border-[#00ff9d]/30 px-3 py-0.5 rounded-full mb-2 shadow-[0_0_10px_rgba(0,255,157,0.15)]">
                <span class="w-1.5 h-1.5 rounded-full bg-[#00ff9d] animate-pulse"></span>
                <span>[ KONFIGURASI SISTEM CTI ]</span>
            </div>
            <h2 class="text-xl sm:text-2xl font-extrabold text-[#e0f0ff] font-['Sora'] tracking-tight flex items-center gap-2">
                <span class="material-symbols-outlined text-[#00d4ff]">settings</span>
                Pengaturan Sistem CTI Diskominfo Jatim
            </h2>
            <p class="text-xs sm:text-sm text-[#8892b0] mt-1">
                Manajemen LLM Gemini, Kata Kunci Scraping, Template Prompt Intelijen, Sumber Feed RSS, Referensi CTI, dan Akun Admin.
            </p>
        </div>
        <div class="flex items-center gap-2 shrink-0">
            <span x-show="role === 'superadmin'" class="px-2.5 py-1 rounded-full text-xs font-mono font-bold bg-[#00ff9d]/10 text-[#00ff9d] border border-[#00ff9d]/30 flex items-center gap-1.5">
                <span class="material-symbols-outlined text-sm">verified_user</span> Superadmin (Akses Penuh)
            </span>
            <span x-show="role === 'viewer'" class="px-2.5 py-1 rounded-full text-xs font-mono font-bold bg-[#ff8800]/10 text-[#ff8800] border border-[#ff8800]/30 flex items-center gap-1.5">
                <span class="material-symbols-outlined text-sm">visibility</span> Mode Viewer (Hanya Lihat)
            </span>
        </div>
    </div>

    <!-- Main Navigation Tabs -->
    <div class="flex border-b border-[#1a3a5c] bg-[#0d2137]/90 rounded-t-xl px-2 gap-1 overflow-x-auto custom-scrollbar">
        <!-- 1. Umum & LLM -->
        <button @click="activeTab = 'umum'" 
                :class="{'border-b-2 border-[#00d4ff] text-[#00d4ff] bg-[#0a1628]/80 font-bold': activeTab === 'umum', 'text-[#8892b0] hover:text-[#e0f0ff] hover:bg-[#132c4a]/40 font-medium': activeTab !== 'umum'}" 
                class="px-4 py-3 text-xs sm:text-sm font-mono transition-all flex items-center gap-2 cursor-pointer shrink-0 rounded-t-lg">
            <span class="material-symbols-outlined text-base">tune</span> Umum &amp; LLM
        </button>

        <!-- 2. Kata Kunci Scraping (Dedicated Tab) -->
        <button @click="activeTab = 'keywords'" 
                :class="{'border-b-2 border-[#00d4ff] text-[#00d4ff] bg-[#0a1628]/80 font-bold': activeTab === 'keywords', 'text-[#8892b0] hover:text-[#e0f0ff] hover:bg-[#132c4a]/40 font-medium': activeTab !== 'keywords'}" 
                class="px-4 py-3 text-xs sm:text-sm font-mono transition-all flex items-center gap-2 cursor-pointer shrink-0 rounded-t-lg">
            <span class="material-symbols-outlined text-base">manage_search</span> Kata Kunci Scraping
        </button>

        <!-- 3. Template Prompt LLM -->
        <button @click="activeTab = 'prompts'" 
                :class="{'border-b-2 border-[#00d4ff] text-[#00d4ff] bg-[#0a1628]/80 font-bold': activeTab === 'prompts', 'text-[#8892b0] hover:text-[#e0f0ff] hover:bg-[#132c4a]/40 font-medium': activeTab !== 'prompts'}" 
                class="px-4 py-3 text-xs sm:text-sm font-mono transition-all flex items-center gap-2 cursor-pointer shrink-0 rounded-t-lg">
            <span class="material-symbols-outlined text-base">psychology</span> Template Prompt LLM
        </button>

        <!-- 4. Sumber RSS (2 Sub-Tab) -->
        <button @click="activeTab = 'rss'" 
                :class="{'border-b-2 border-[#00d4ff] text-[#00d4ff] bg-[#0a1628]/80 font-bold': activeTab === 'rss', 'text-[#8892b0] hover:text-[#e0f0ff] hover:bg-[#132c4a]/40 font-medium': activeTab !== 'rss'}" 
                class="px-4 py-3 text-xs sm:text-sm font-mono transition-all flex items-center gap-2 cursor-pointer shrink-0 rounded-t-lg">
            <span class="material-symbols-outlined text-base">rss_feed</span> Sumber RSS
        </button>

        <!-- 5. Sumber Referensi CTI -->
        <button @click="activeTab = 'referensi'; fetchReferenceInfo()" 
                :class="{'border-b-2 border-[#00d4ff] text-[#00d4ff] bg-[#0a1628]/80 font-bold': activeTab === 'referensi', 'text-[#8892b0] hover:text-[#e0f0ff] hover:bg-[#132c4a]/40 font-medium': activeTab !== 'referensi'}" 
                class="px-4 py-3 text-xs sm:text-sm font-mono transition-all flex items-center gap-2 cursor-pointer shrink-0 rounded-t-lg">
            <span class="material-symbols-outlined text-base">database</span> Sumber Referensi CTI
        </button>

        <!-- 6. Akun Admin -->
        <button @click="activeTab = 'akun'" 
                :class="{'border-b-2 border-[#00d4ff] text-[#00d4ff] bg-[#0a1628]/80 font-bold': activeTab === 'akun', 'text-[#8892b0] hover:text-[#e0f0ff] hover:bg-[#132c4a]/40 font-medium': activeTab !== 'akun'}" 
                class="px-4 py-3 text-xs sm:text-sm font-mono transition-all flex items-center gap-2 cursor-pointer shrink-0 rounded-t-lg">
            <span class="material-symbols-outlined text-base">shield_person</span> Akun Admin
        </button>
    </div>

    <!-- TAB 1: UMUM & LLM -->
    <div x-show="activeTab === 'umum'" class="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <!-- Gemini API Key Card -->
        <div class="card-cyber p-5 sm:p-6 bg-[#0d2137]/80 border border-[#1a3a5c] rounded-xl space-y-4">
            <div class="flex items-center justify-between pb-3 border-b border-[#1a3a5c]">
                <h3 class="text-base font-bold text-[#e0f0ff] font-['Sora'] flex items-center gap-2">
                    <span class="material-symbols-outlined text-[#00d4ff]">memory</span>
                    Kredensial Google Gemini API
                </h3>
                <span class="text-[11px] font-mono font-bold px-2.5 py-0.5 rounded-full"
                      :class="apiKeysList.length > 0 ? 'bg-[#00ff9d]/10 text-[#00ff9d] border border-[#00ff9d]/30' : 'bg-[#ff3366]/10 text-[#ff3366] border border-[#ff3366]/30'"
                      x-text="apiKeysList.length > 0 ? apiKeysList.length + ' Key Aktif' : 'Belum Disetel'"></span>
            </div>

            <div>
                <label class="block text-xs font-mono font-semibold text-[#8892b0] mb-1.5">
                    Gemini API Key (Mendukung Multi-Key Rotasi Otomatis &amp; Kuota Proaktif):
                </label>
                <textarea x-model="gemini.api_key" rows="3" 
                          placeholder="Tempel API Key Google AI Studio di sini (pisahkan dengan koma atau baris baru jika lebih dari satu)" 
                          class="w-full text-xs font-mono p-3 rounded-lg border border-[#1a3a5c] bg-[#0a1628] text-[#e0f0ff] placeholder-[#7d8ca6] focus:border-[#00d4ff] focus:ring-1 focus:ring-[#00d4ff] outline-none transition-colors" 
                          :disabled="role === 'viewer'"></textarea>
                <p class="text-[11px] font-mono text-[#8892b0] mt-1.5 leading-relaxed">
                    Sistem mendeteksi ambang batas proaktif (90%-95% RPM). Model embedding otomatis berganti pada 90 RPM (kuota 100 RPM), dan 7 model narasi berganti sebelum menyentuh batas limit. Jika seluruh model pada satu kunci jenuh, sistem beralih ke kunci berikutnya.
                </p>
            </div>

            <!-- Tombol Aksi Kunci API -->
            <div class="flex items-center gap-2.5 pt-2">
                <button type="button" 
                        @click="testApiKeyConnection()" 
                        :disabled="testingApiKey || !gemini.api_key.trim()"
                        class="px-3.5 py-2 rounded-lg border border-[#00d4ff]/40 bg-[#00d4ff]/10 hover:bg-[#00d4ff]/20 text-[#00d4ff] text-xs font-mono font-semibold transition-all flex items-center gap-1.5 cursor-pointer disabled:opacity-50">
                    <span class="material-symbols-outlined text-sm" :class="testingApiKey ? 'animate-spin' : ''" x-text="testingApiKey ? 'refresh' : 'network_check'"></span>
                    <span x-text="testingApiKey ? 'Menguji Koneksi...' : 'Uji Koneksi API'"></span>
                </button>
                <button type="button" 
                        @click="saveApiKeysOnly()" 
                        x-show="role === 'superadmin'" 
                        class="px-3.5 py-2 rounded-lg bg-[#00ff9d]/20 hover:bg-[#00ff9d]/30 border border-[#00ff9d]/40 text-[#00ff9d] text-xs font-mono font-bold flex items-center gap-1.5 transition-all cursor-pointer">
                    <span class="material-symbols-outlined text-sm">save</span>
                    <span>Simpan API Key</span>
                </button>
            </div>

            <!-- Alert Hasil Uji Koneksi -->
            <div x-show="testResult !== null" x-transition class="p-3 rounded-lg border text-xs font-mono flex items-start justify-between gap-2"
                 :class="testResult && testResult.ok ? 'bg-[#00ff9d]/10 border-[#00ff9d]/30 text-[#00ff9d]' : 'bg-[#ff3366]/10 border-[#ff3366]/30 text-[#ff3366]'">
                <div class="flex items-start gap-2">
                    <span class="material-symbols-outlined text-sm mt-0.5" x-text="testResult && testResult.ok ? 'check_circle' : 'cancel'"></span>
                    <span x-text="testResult ? testResult.message : ''"></span>
                </div>
                <button type="button" @click="testResult = null" class="text-xs opacity-60 hover:opacity-100 cursor-pointer">✕</button>
            </div>
        </div>

        <!-- Parameter Inferensi & Rantai Model -->
        <div class="card-cyber p-5 sm:p-6 bg-[#0d2137]/80 border border-[#1a3a5c] rounded-xl space-y-4">
            <div class="pb-3 border-b border-[#1a3a5c]">
                <h3 class="text-base font-bold text-[#e0f0ff] font-['Sora'] flex items-center gap-2">
                    <span class="material-symbols-outlined text-[#00ff88]">tune</span>
                    Parameter Inferensi LLM
                </h3>
            </div>

            <div>
                <label class="block text-xs font-mono font-semibold text-[#8892b0] mb-1.5">Temperature Inferensi (0.0 - 1.0):</label>
                <input type="number" x-model="gemini.temperature" step="0.1" min="0" max="1" 
                       class="w-full text-xs font-mono p-2.5 rounded-lg border border-[#1a3a5c] bg-[#0a1628] text-[#e0f0ff] focus:border-[#00d4ff] focus:ring-1 focus:ring-[#00d4ff] outline-none" 
                       :disabled="role === 'viewer'" />
                <p class="text-[11px] font-mono text-[#8892b0] mt-1.5">
                    Rekomendasi CTI: <span class="text-[#00ff9d] font-bold">0.1</span> untuk hasil inferensi intelijen yang presisi, deterministik, dan terikat fakta berita.
                </p>
            </div>

            <div>
                <label class="block text-xs font-mono font-semibold text-[#8892b0] mb-1.5">Fallback Model Chain (Urutan Model Narasi):</label>
                <textarea x-model="gemini.model_chain" rows="3" 
                          class="w-full text-xs font-mono p-2.5 rounded-lg border border-[#1a3a5c] bg-[#0a1628] text-[#e0f0ff] focus:border-[#00d4ff] focus:ring-1 focus:ring-[#00d4ff] outline-none" 
                          :disabled="role === 'viewer'"></textarea>
                <p class="text-[11px] font-mono text-[#8892b0] mt-1.5 leading-relaxed">
                    Urutan failover otomatis jika kuota atau rate limit model tercapai. Tersedia: gemini-2.5-flash, gemini-2.5-flash-lite, gemini-3-flash, gemini-3.1-flash-lite, gemini-3.6-flash, gemini-3.5-flash-lite, gemini-3.8-flash.
                </p>
            </div>

            <div class="pt-2">
                <button @click="saveUmum()" x-show="role === 'superadmin'" 
                        class="bg-[#00d4ff] hover:bg-[#00ff9d] text-[#0a1628] px-4 py-2 rounded-lg text-xs font-bold font-mono uppercase tracking-wider flex items-center gap-1.5 transition-all shadow-[0_0_15px_rgba(0,212,255,0.25)] cursor-pointer">
                    <span class="material-symbols-outlined text-sm">save</span>
                    <span>Simpan Pengaturan LLM</span>
                </button>
            </div>
        </div>
    </div>

    <!-- TAB 2: KATA KUNCI SCRAPING (DEDICATED TAB - CHIPS, ADD, DELETE, CONFIRM) -->
    <div x-show="activeTab === 'keywords'" class="space-y-6">
        <div class="card-cyber p-5 sm:p-6 bg-[#0d2137]/80 border border-[#1a3a5c] rounded-xl space-y-6">
            <div class="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-[#1a3a5c] gap-3">
                <div>
                    <h3 class="text-base font-bold text-[#e0f0ff] font-['Sora'] flex items-center gap-2">
                        <span class="material-symbols-outlined text-[#00d4ff]">manage_search</span>
                        Filter Kata Kunci Scraping &amp; Klasifikasi Relevansi
                    </h3>
                    <p class="text-xs text-[#8892b0] mt-1">
                        Kelola kamus kata kunci penyaring berita siber secara visual. Tidak perlu menulis koma, cukup tambah atau hapus tag kata kunci secara langsung.
                    </p>
                </div>
                <button @click="saveKeywords()" x-show="role === 'superadmin'" 
                        class="bg-[#00d4ff] hover:bg-[#00ff9d] text-[#0a1628] px-4 py-2 rounded-lg text-xs font-bold font-mono uppercase tracking-wider flex items-center gap-1.5 transition-all shadow-[0_0_15px_rgba(0,212,255,0.25)] cursor-pointer shrink-0">
                    <span class="material-symbols-outlined text-sm">save</span>
                    <span>Simpan Seluruh Kata Kunci</span>
                </button>
            </div>

            <!-- Group 1: Indikator Insiden (Mandiri) -->
            <div class="p-4 rounded-xl border border-[#1a3a5c] bg-[#0a1628]/60 space-y-3">
                <div class="flex items-center justify-between">
                    <div class="flex items-center gap-2">
                        <span class="w-2.5 h-2.5 rounded-full bg-[#00ff9d]"></span>
                        <h4 class="text-sm font-bold text-[#e0f0ff] font-mono">1. Indikator Insiden (Mandiri / Bahasa Indonesia)</h4>
                    </div>
                    <span class="text-xs font-mono font-bold px-2 py-0.5 rounded bg-[#00ff9d]/10 text-[#00ff9d] border border-[#00ff9d]/30" 
                          x-text="keywordsList.mandiri.length + ' Kata Kunci'"></span>
                </div>
                <p class="text-xs text-[#8892b0] leading-relaxed">
                    <span class="text-[#00ff9d] font-bold">Fungsi:</span> Kata kunci berkekuatan mandiri yang <em class="text-[#e0f0ff]">pasti menandakan insiden siber</em> (contoh: kebocoran data, ransomware, phishing, peretasan). Jika artikel memuat salah satu kata ini, artikel otomatis dinyatakan relevan.
                </p>

                <!-- Chips Container -->
                <div class="flex flex-wrap gap-2 pt-1 min-h-[42px] p-2.5 rounded-lg border border-[#1a3a5c] bg-[#070d1e]">
                    <template x-for="(kw, idx) in keywordsList.mandiri" :key="'man-'+idx">
                        <span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-[#0d2137] border border-[#00ff9d]/30 text-xs font-mono text-[#00ff9d] hover:border-[#00ff9d] transition-all">
                            <span x-text="kw"></span>
                            <button type="button" @click="removeKeyword('mandiri', idx)" x-show="role === 'superadmin'" 
                                    class="text-[#7d8ca6] hover:text-[#ff3366] text-xs cursor-pointer font-bold ml-0.5" title="Hapus kata kunci">✕</button>
                        </span>
                    </template>
                    <span x-show="keywordsList.mandiri.length === 0" class="text-xs text-[#7d8ca6] italic py-1 font-mono">Belum ada kata kunci mandiri.</span>
                </div>

                <!-- Input Tambah Baru -->
                <div class="flex items-center gap-2 pt-1" x-show="role === 'superadmin'">
                    <input type="text" x-model="newKw.mandiri" @keydown.enter.prevent="addKeyword('mandiri')" 
                           placeholder="Ketik kata kunci indikator mandiri baru lalu tekan Enter / Tambah..." 
                           class="flex-1 text-xs font-mono p-2.5 rounded-lg border border-[#1a3a5c] bg-[#0d2137] text-[#e0f0ff] placeholder-[#7d8ca6] focus:border-[#00d4ff] outline-none">
                    <button type="button" @click="addKeyword('mandiri')" 
                            class="px-3.5 py-2 rounded-lg bg-[#00ff9d]/20 hover:bg-[#00ff9d]/30 border border-[#00ff9d]/40 text-[#00ff9d] text-xs font-mono font-bold flex items-center gap-1 cursor-pointer">
                        <span class="material-symbols-outlined text-sm">add</span> Tambah
                    </button>
                </div>
            </div>

            <!-- Group 2: Objek Data Sensitif -->
            <div class="p-4 rounded-xl border border-[#1a3a5c] bg-[#0a1628]/60 space-y-3">
                <div class="flex items-center justify-between">
                    <div class="flex items-center gap-2">
                        <span class="w-2.5 h-2.5 rounded-full bg-[#00d4ff]"></span>
                        <h4 class="text-sm font-bold text-[#e0f0ff] font-mono">2. Objek Data Sensitif (Butuh Indikator Aksi)</h4>
                    </div>
                    <span class="text-xs font-mono font-bold px-2 py-0.5 rounded bg-[#00d4ff]/10 text-[#00d4ff] border border-[#00d4ff]/30" 
                          x-text="keywordsList.data.length + ' Kata Kunci'"></span>
                </div>
                <p class="text-xs text-[#8892b0] leading-relaxed">
                    <span class="text-[#00d4ff] font-bold">Fungsi:</span> Entitas data rahasia warga atau instansi (contoh: ktp, nik, kartu keluarga, npwp, data nasabah, bpjs). Kata ini <em class="text-[#e0f0ff]">tidak berdiri sendiri</em>—hanya memicu status relevan jika ditemukan bersamaan dengan indikator aksi (misal: KTP + bocor).
                </p>

                <!-- Chips Container -->
                <div class="flex flex-wrap gap-2 pt-1 min-h-[42px] p-2.5 rounded-lg border border-[#1a3a5c] bg-[#070d1e]">
                    <template x-for="(kw, idx) in keywordsList.data" :key="'dat-'+idx">
                        <span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-[#0d2137] border border-[#00d4ff]/30 text-xs font-mono text-[#00d4ff] hover:border-[#00d4ff] transition-all">
                            <span x-text="kw"></span>
                            <button type="button" @click="removeKeyword('data', idx)" x-show="role === 'superadmin'" 
                                    class="text-[#7d8ca6] hover:text-[#ff3366] text-xs cursor-pointer font-bold ml-0.5" title="Hapus kata kunci">✕</button>
                        </span>
                    </template>
                    <span x-show="keywordsList.data.length === 0" class="text-xs text-[#7d8ca6] italic py-1 font-mono">Belum ada kata kunci data sensitif.</span>
                </div>

                <!-- Input Tambah Baru -->
                <div class="flex items-center gap-2 pt-1" x-show="role === 'superadmin'">
                    <input type="text" x-model="newKw.data" @keydown.enter.prevent="addKeyword('data')" 
                           placeholder="Ketik kata kunci objek data baru lalu tekan Enter / Tambah..." 
                           class="flex-1 text-xs font-mono p-2.5 rounded-lg border border-[#1a3a5c] bg-[#0d2137] text-[#e0f0ff] placeholder-[#7d8ca6] focus:border-[#00d4ff] outline-none">
                    <button type="button" @click="addKeyword('data')" 
                            class="px-3.5 py-2 rounded-lg bg-[#00d4ff]/20 hover:bg-[#00d4ff]/30 border border-[#00d4ff]/40 text-[#00d4ff] text-xs font-mono font-bold flex items-center gap-1 cursor-pointer">
                        <span class="material-symbols-outlined text-sm">add</span> Tambah
                    </button>
                </div>
            </div>

            <!-- Group 3: Objek Aset Digital -->
            <div class="p-4 rounded-xl border border-[#1a3a5c] bg-[#0a1628]/60 space-y-3">
                <div class="flex items-center justify-between">
                    <div class="flex items-center gap-2">
                        <span class="w-2.5 h-2.5 rounded-full bg-[#ffb703]"></span>
                        <h4 class="text-sm font-bold text-[#e0f0ff] font-mono">3. Objek Aset Digital (Butuh Indikator Aksi)</h4>
                    </div>
                    <span class="text-xs font-mono font-bold px-2 py-0.5 rounded bg-[#ffb703]/10 text-[#ffb703] border border-[#ffb703]/30" 
                          x-text="keywordsList.aset.length + ' Kata Kunci'"></span>
                </div>
                <p class="text-xs text-[#8892b0] leading-relaxed">
                    <span class="text-[#ffb703] font-bold">Fungsi:</span> Infrastruktur sistem, server, aplikasi, dan database instansi (contoh: website, server, database, pdns, rekening). Wajib berpasangan dengan kata aksi insiden (misal: server + dibobol) agar artikel peluncuran sistem publik normal tidak salah terjaring.
                </p>

                <!-- Chips Container -->
                <div class="flex flex-wrap gap-2 pt-1 min-h-[42px] p-2.5 rounded-lg border border-[#1a3a5c] bg-[#070d1e]">
                    <template x-for="(kw, idx) in keywordsList.aset" :key="'ast-'+idx">
                        <span class="inline-flex items-center gap-1.5 px-3 py-1 rounded-lg bg-[#0d2137] border border-[#ffb703]/30 text-xs font-mono text-[#ffb703] hover:border-[#ffb703] transition-all">
                            <span x-text="kw"></span>
                            <button type="button" @click="removeKeyword('aset', idx)" x-show="role === 'superadmin'" 
                                    class="text-[#7d8ca6] hover:text-[#ff3366] text-xs cursor-pointer font-bold ml-0.5" title="Hapus kata kunci">✕</button>
                        </span>
                    </template>
                    <span x-show="keywordsList.aset.length === 0" class="text-xs text-[#7d8ca6] italic py-1 font-mono">Belum ada kata kunci aset digital.</span>
                </div>

                <!-- Input Tambah Baru -->
                <div class="flex items-center gap-2 pt-1" x-show="role === 'superadmin'">
                    <input type="text" x-model="newKw.aset" @keydown.enter.prevent="addKeyword('aset')" 
                           placeholder="Ketik kata kunci objek aset baru lalu tekan Enter / Tambah..." 
                           class="flex-1 text-xs font-mono p-2.5 rounded-lg border border-[#1a3a5c] bg-[#0d2137] text-[#e0f0ff] placeholder-[#7d8ca6] focus:border-[#00d4ff] outline-none">
                    <button type="button" @click="addKeyword('aset')" 
                            class="px-3.5 py-2 rounded-lg bg-[#ffb703]/20 hover:bg-[#ffb703]/30 border border-[#ffb703]/40 text-[#ffb703] text-xs font-mono font-bold flex items-center gap-1 cursor-pointer">
                        <span class="material-symbols-outlined text-sm">add</span> Tambah
                    </button>
                </div>
            </div>
        </div>
    </div>

    <!-- TAB 3: TEMPLATE PROMPT LLM -->
    <div x-show="activeTab === 'prompts'" class="card-cyber p-5 sm:p-6 bg-[#0d2137]/80 border border-[#1a3a5c] rounded-xl space-y-5">
        <div class="border-b border-[#1a3a5c] pb-3 mb-2">
            <h3 class="text-base font-bold text-[#e0f0ff] font-['Sora'] flex items-center gap-2">
                <span class="material-symbols-outlined text-[#00d4ff]">psychology</span>
                Template Prompt Sistem CTI (Modul Aktif)
            </h3>
            <p class="text-xs text-[#8892b0] mt-1 leading-relaxed">
                Prompt disusun modular per-bagian agar hasil inferensi akurat, bebas halusinasi, dan dapat disesuaikan kebutuhan analisis intelijen Diskominfo Jawa Timur.
            </p>
        </div>

        <div class="grid grid-cols-1 md:grid-cols-12 gap-5">
            <!-- Sidebar Daftar Prompt -->
            <div class="md:col-span-4 border-r border-[#1a3a5c] pr-3 space-y-4 max-h-[600px] overflow-y-auto custom-scrollbar">
                <template x-for="kat in promptCategories" :key="kat">
                    <div>
                        <div class="text-[11px] font-mono font-bold uppercase tracking-wider text-[#00d4ff] px-2.5 py-1 bg-[#0a1628] rounded-md flex items-center justify-between mb-1.5 border border-[#1a3a5c]">
                            <span x-text="kat"></span>
                            <span class="text-[10px] text-[#00ff9d] font-bold" x-text="getPromptsByCategory(kat).length"></span>
                        </div>
                        <div class="space-y-1">
                            <template x-for="p in getPromptsByCategory(kat)" :key="p.id">
                                <button @click="selectPrompt(p)" 
                                        :class="{'bg-[#00d4ff]/20 text-[#00d4ff] border border-[#00d4ff]/40 font-bold shadow-xs': selectedPromptId === p.id, 'hover:bg-[#132c4a]/50 text-[#8892b0] hover:text-[#e0f0ff] border border-transparent': selectedPromptId !== p.id}" 
                                        class="w-full text-left px-3 py-2 rounded-lg text-xs font-mono transition-all flex flex-col gap-0.5 cursor-pointer">
                                    <span class="font-semibold text-[#e0f0ff]" x-text="p.nama"></span>
                                    <span class="text-[10px] opacity-75 truncate" x-text="p.deskripsi"></span>
                                </button>
                            </template>
                        </div>
                    </div>
                </template>
            </div>

            <!-- Editor Prompt Pane -->
            <div class="md:col-span-8 pl-1">
                <div x-show="selectedPromptMeta" class="space-y-3">
                    <div class="flex items-start justify-between gap-4 border-b border-[#1a3a5c] pb-3">
                        <div>
                            <span class="text-[10px] font-mono font-bold uppercase tracking-wider text-[#00ff9d]" x-text="selectedPromptMeta ? selectedPromptMeta.kategori : ''"></span>
                            <h4 class="text-base font-bold text-[#e0f0ff] font-['Sora']" x-text="selectedPromptMeta ? selectedPromptMeta.nama : ''"></h4>
                            <p class="text-xs text-[#8892b0] mt-0.5" x-text="selectedPromptMeta ? selectedPromptMeta.deskripsi : ''"></p>
                        </div>
                        <span class="text-[11px] font-mono bg-[#0a1628] px-2.5 py-1 rounded-md text-[#00d4ff] border border-[#1a3a5c]" x-text="'ID: ' + selectedPromptId"></span>
                    </div>

                    <div>
                        <label class="block text-xs font-mono font-semibold text-[#8892b0] mb-1.5">Isi System Instruction (Prompt):</label>
                        <textarea x-model="promptContent" rows="15" 
                                  class="w-full text-xs font-mono p-3 rounded-lg border border-[#1a3a5c] bg-[#0a1628] text-[#e0f0ff] focus:border-[#00d4ff] focus:ring-1 focus:ring-[#00d4ff] outline-none leading-relaxed transition-all custom-scrollbar" 
                                  :disabled="role === 'viewer'"></textarea>
                    </div>

                    <div class="flex items-center justify-between pt-2">
                        <span class="text-[11px] font-mono text-[#8892b0] italic" x-show="role === 'viewer'">* Mode Viewer: Prompt bersifat read-only.</span>
                        <button @click="savePrompt()" x-show="role === 'superadmin'" 
                                class="bg-[#00d4ff] hover:bg-[#00ff9d] text-[#0a1628] px-4 py-2 rounded-lg text-xs font-bold font-mono uppercase tracking-wider flex items-center gap-1.5 transition-all shadow-[0_0_15px_rgba(0,212,255,0.25)] cursor-pointer">
                            <span class="material-symbols-outlined text-sm">save</span> Simpan Perubahan Prompt
                        </button>
                    </div>
                </div>

                <div x-show="!selectedPromptMeta" class="h-64 flex flex-col items-center justify-center text-[#8892b0] text-center p-6 border-2 border-dashed border-[#1a3a5c] rounded-xl bg-[#0a1628]/40">
                    <span class="material-symbols-outlined text-3xl text-[#00d4ff] mb-2">touch_app</span>
                    <p class="text-sm font-semibold text-[#e0f0ff]">Pilih Salah Satu Template Prompt</p>
                    <p class="text-xs text-[#8892b0] mt-1 font-mono">Klik modul prompt pada daftar di sebelah kiri untuk melihat dan menyunting instruksi sistem.</p>
                </div>
            </div>
        </div>
    </div>

    <!-- TAB 4: SUMBER RSS (2 SUB-TAB: INTERNASIONAL & NASIONAL) -->
    <div x-show="activeTab === 'rss'" class="space-y-6">
        <div class="card-cyber p-5 sm:p-6 bg-[#0d2137]/80 border border-[#1a3a5c] rounded-xl space-y-5">
            <div class="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-[#1a3a5c] gap-3">
                <div>
                    <h3 class="text-base font-bold text-[#e0f0ff] font-['Sora'] flex items-center gap-2">
                        <span class="material-symbols-outlined text-[#00d4ff]">rss_feed</span>
                        Manajemen Sumber Feed RSS
                    </h3>
                    <p class="text-xs text-[#8892b0] mt-1">
                        Kelola sumber berita siber yang dipantau pipeline intelijen harian, terbagi dalam feed Internasional dan Nasional.
                    </p>
                </div>
                <div class="flex items-center gap-2 shrink-0">
                    <button type="button" @click="openAddRssModal(rssSubTab)" x-show="role === 'superadmin'" 
                            class="bg-[#00d4ff] hover:bg-[#00ff9d] text-[#0a1628] px-3.5 py-1.5 rounded-lg text-xs font-bold font-mono uppercase tracking-wider flex items-center gap-1.5 transition-all shadow-[0_0_12px_rgba(0,212,255,0.25)] cursor-pointer">
                        <span class="material-symbols-outlined text-sm">add</span> Tambah Sumber
                    </button>
                    <button type="button" @click="saveRss()" x-show="role === 'superadmin'" 
                            class="bg-[#00ff9d]/20 hover:bg-[#00ff9d]/30 border border-[#00ff9d]/40 text-[#00ff9d] px-3.5 py-1.5 rounded-lg text-xs font-mono font-bold flex items-center gap-1.5 transition-all cursor-pointer">
                        <span class="material-symbols-outlined text-sm">save</span> Simpan Perubahan RSS
                    </button>
                </div>
            </div>

            <!-- Sub-Tabs Navigation (Internasional & Nasional) -->
            <div class="flex items-center gap-2 border-b border-[#1a3a5c] pb-2">
                <button type="button" @click="rssSubTab = 'international'" 
                        :class="rssSubTab === 'international' ? 'border-[#00d4ff] text-[#00d4ff] bg-[#0a1628] font-bold shadow-[0_0_10px_rgba(0,212,255,0.15)]' : 'border-transparent text-[#8892b0] hover:text-[#e0f0ff] bg-transparent'" 
                        class="px-4 py-2 rounded-lg border text-xs font-mono transition-all flex items-center gap-2 cursor-pointer">
                    <span class="material-symbols-outlined text-sm">public</span>
                    <span>Media Cybersecurity Internasional</span>
                    <span class="text-[10px] px-2 py-0.5 rounded-full bg-[#1a3a5c] text-[#e0f0ff] font-bold" x-text="rss.international.length"></span>
                </button>
                <button type="button" @click="rssSubTab = 'indonesia'" 
                        :class="rssSubTab === 'indonesia' ? 'border-[#00d4ff] text-[#00d4ff] bg-[#0a1628] font-bold shadow-[0_0_10px_rgba(0,212,255,0.15)]' : 'border-transparent text-[#8892b0] hover:text-[#e0f0ff] bg-transparent'" 
                        class="px-4 py-2 rounded-lg border text-xs font-mono transition-all flex items-center gap-2 cursor-pointer">
                    <span class="material-symbols-outlined text-sm">flag</span>
                    <span>Media Siber &amp; Berita Nasional</span>
                    <span class="text-[10px] px-2 py-0.5 rounded-full bg-[#1a3a5c] text-[#e0f0ff] font-bold" x-text="rss.indonesia.length"></span>
                </button>
            </div>

            <!-- Tabel Feed untuk Sub-Tab Aktif -->
            <div class="overflow-x-auto border border-[#1a3a5c] rounded-xl bg-[#0a1628]/60">
                <table class="w-full text-xs text-left">
                    <thead class="bg-[#0a1628] text-[#8892b0] font-mono border-b border-[#1a3a5c]">
                        <tr>
                            <th class="px-4 py-3 font-bold">Nama Sumber Media</th>
                            <th class="px-4 py-3 font-bold">URL Feed (RSS/Atom)</th>
                            <th class="px-4 py-3 font-bold text-center">Status</th>
                            <th class="px-4 py-3 font-bold text-center" x-show="role === 'superadmin'">Aksi</th>
                        </tr>
                    </thead>
                    <tbody class="divide-y divide-[#1a3a5c]">
                        <template x-for="(s, idx) in (rssSubTab === 'international' ? rss.international : rss.indonesia)" :key="rssSubTab + '-' + idx">
                            <tr class="hover:bg-[#132c4a]/40 transition-colors">
                                <td class="px-4 py-2.5 font-semibold text-[#e0f0ff] font-mono" x-text="s.nama"></td>
                                <td class="px-4 py-2.5 font-mono text-[11px] text-[#8892b0] max-w-sm">
                                    <template x-for="(fUrl, fIdx) in s.feeds" :key="fIdx">
                                        <div class="truncate flex items-center gap-1.5" :title="fUrl">
                                            <span x-show="s.feeds.length > 1" class="text-[10px] text-[#00d4ff] font-bold shrink-0" x-text="'[' + (fIdx + 1) + ']'"></span>
                                            <span class="truncate" x-text="fUrl"></span>
                                        </div>
                                    </template>
                                </td>
                                <td class="px-4 py-2.5 text-center">
                                    <span x-show="s.active !== false" class="px-2.5 py-0.5 bg-[#00ff9d]/10 text-[#00ff9d] border border-[#00ff9d]/30 text-[10px] font-bold rounded-full font-mono">Aktif</span>
                                    <span x-show="s.active === false" class="px-2.5 py-0.5 bg-[#ff3366]/10 text-[#ff3366] border border-[#ff3366]/30 text-[10px] font-bold rounded-full font-mono">Nonaktif</span>
                                </td>
                                <td class="px-4 py-2.5 text-center" x-show="role === 'superadmin'">
                                    <div class="flex items-center justify-center gap-2.5 font-mono text-xs">
                                        <button type="button" @click="toggleRss(rssSubTab, idx)" 
                                                class="text-[#00d4ff] hover:text-[#00ff9d] hover:underline font-semibold cursor-pointer" 
                                                x-text="s.active !== false ? 'Nonaktifkan' : 'Aktifkan'"></button>
                                        <span class="text-[#1a3a5c]">|</span>
                                        <button type="button" @click="deleteRss(rssSubTab, idx)" 
                                                class="text-[#ff3366] hover:text-[#ff5588] hover:underline font-semibold cursor-pointer">Hapus</button>
                                    </div>
                                </td>
                            </tr>
                        </template>
                        <tr x-show="(rssSubTab === 'international' ? rss.international.length : rss.indonesia.length) === 0">
                            <td colspan="4" class="px-4 py-8 text-center text-[#8892b0] font-mono italic">
                                Belum ada sumber feed terdaftar pada kategori ini.
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>

            <!-- Form Tambah Sumber RSS Baru (Collapsible) -->
            <div x-show="addRssModal" x-transition class="p-4 border border-[#00d4ff]/30 rounded-xl bg-[#0a1628] shadow-[0_0_15px_rgba(0,212,255,0.1)] space-y-3">
                <div class="flex items-center justify-between pb-2 border-b border-[#1a3a5c]">
                    <h4 class="text-xs font-bold text-[#e0f0ff] font-mono flex items-center gap-1.5 uppercase tracking-wider">
                        <span class="material-symbols-outlined text-sm text-[#00ff9d]">add_circle</span> Tambah Sumber Feed RSS Baru
                    </h4>
                    <button type="button" @click="addRssModal = false" class="text-xs text-[#7d8ca6] hover:text-[#e0f0ff] cursor-pointer">✕ Batal</button>
                </div>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-3">
                    <div>
                        <label class="block text-xs font-mono font-semibold text-[#8892b0] mb-1">Kategori Wilayah Media:</label>
                        <select x-model="newRss.tipe" class="w-full p-2.5 border border-[#1a3a5c] rounded-lg text-xs bg-[#0d2137] text-[#e0f0ff] font-mono focus:border-[#00d4ff] outline-none">
                            <option value="international">Internasional (Global CTI)</option>
                            <option value="indonesia">Indonesia (Media Nasional)</option>
                        </select>
                    </div>
                    <div>
                        <label class="block text-xs font-mono font-semibold text-[#8892b0] mb-1">Nama Media Sumber:</label>
                        <input type="text" x-model="newRss.nama" class="w-full p-2.5 border border-[#1a3a5c] rounded-lg text-xs bg-[#0d2137] text-[#e0f0ff] font-mono placeholder-[#7d8ca6] focus:border-[#00d4ff] outline-none" placeholder="Contoh: BleepingComputer atau Detikinet">
                    </div>
                    <div class="md:col-span-2">
                        <label class="block text-xs font-mono font-semibold text-[#8892b0] mb-1">URL Feed (Pisahkan dengan koma jika lebih dari satu):</label>
                        <input type="text" x-model="newRss.feeds" class="w-full p-2.5 border border-[#1a3a5c] rounded-lg text-xs bg-[#0d2137] text-[#e0f0ff] font-mono placeholder-[#7d8ca6] focus:border-[#00d4ff] outline-none" placeholder="https://domain.com/feed.xml">
                    </div>
                </div>
                <div class="flex items-center gap-2 pt-1">
                    <button type="button" @click="submitNewRss()" class="bg-[#00d4ff] hover:bg-[#00ff9d] text-[#0a1628] px-4 py-2 rounded-lg text-xs font-bold font-mono uppercase tracking-wider cursor-pointer">
                        Tambahkan ke Daftar
                    </button>
                    <button type="button" @click="addRssModal = false" class="bg-[#1a3a5c] hover:bg-[#132c4a] text-[#e0f0ff] px-4 py-2 rounded-lg text-xs font-mono cursor-pointer">
                        Batal
                    </button>
                </div>
            </div>
        </div>
    </div>

    <!-- TAB 5: SUMBER REFERENSI CTI (DARK CYBER THEME + PROGRESS BAR) -->
    <div x-show="activeTab === 'referensi'" class="space-y-6">
        <div class="card-cyber p-5 sm:p-6 bg-[#0d2137]/80 border border-[#1a3a5c] rounded-xl space-y-6">
            <div class="flex flex-col sm:flex-row sm:items-center justify-between pb-4 border-b border-[#1a3a5c] gap-3">
                <div>
                    <h3 class="text-base font-bold text-[#e0f0ff] font-['Sora'] flex items-center gap-2">
                        <span class="material-symbols-outlined text-[#00d4ff]">database</span>
                        Sumber Referensi Threat Intelligence (CTI)
                    </h3>
                    <p class="text-xs text-[#8892b0] mt-1 leading-relaxed">
                        Pembaruan dan sinkronisasi 4 kerangka kerja intelijen siber: Taksonomi eCSIRT, MITRE ATT&amp;CK, MITRE D3FEND, dan NIST SP 800-53 / CSF 2.0.
                    </p>
                </div>
                <div class="flex items-center gap-2.5 shrink-0">
                    <button type="button" 
                            @click="fetchReferenceInfo()" 
                            :disabled="loadingReferences || refUpdating"
                            class="px-3.5 py-2 rounded-lg border border-[#1a3a5c] bg-[#0a1628] hover:bg-[#132c4a] text-[#00d4ff] text-xs font-mono font-semibold flex items-center gap-1.5 transition-all cursor-pointer disabled:opacity-50">
                        <span class="material-symbols-outlined text-sm" :class="loadingReferences ? 'animate-spin' : ''">refresh</span>
                        <span>Segarkan</span>
                    </button>
                    <button type="button" 
                            @click="updateReferences()" 
                            :disabled="refUpdating || role !== 'superadmin'"
                            class="bg-[#00d4ff] hover:bg-[#00ff9d] text-[#0a1628] px-4 py-2 rounded-lg text-xs font-bold font-mono uppercase tracking-wider flex items-center gap-1.5 transition-all shadow-[0_0_15px_rgba(0,212,255,0.25)] cursor-pointer disabled:opacity-50">
                        <span class="material-symbols-outlined text-sm" :class="refUpdating ? 'animate-spin' : ''" x-text="refUpdating ? 'sync' : 'cloud_sync'"></span>
                        <span x-text="refUpdating ? 'Memperbarui Referensi...' : 'Perbarui Sumber Referensi CTI'"></span>
                    </button>
                </div>
            </div>

            <!-- Live Progress Bar Card Saat Pembaruan Berjalan -->
            <div x-show="refUpdating || refProgressLogs.length > 0" x-transition 
                 class="p-4 rounded-xl border border-[#00d4ff]/40 bg-[#0a1628] shadow-[0_0_20px_rgba(0,212,255,0.15)] space-y-3">
                <div class="flex items-center justify-between">
                    <div class="flex items-center gap-2">
                        <span class="w-2.5 h-2.5 rounded-full" :class="refUpdating ? 'bg-[#00d4ff] animate-ping' : 'bg-[#00ff9d]'"></span>
                        <span class="text-xs font-bold font-mono text-[#e0f0ff] uppercase tracking-wider" 
                              x-text="refUpdating ? 'Sinkronisasi Sedang Berjalan' : 'Status Sinkronisasi Referensi'"></span>
                    </div>
                    <span class="text-xs font-bold px-2.5 py-0.5 rounded bg-[#0d2137] border border-[#00d4ff]/40 text-[#00d4ff] font-mono" 
                          x-text="refProgressPercent + '%'"></span>
                </div>

                <!-- Animated Neon Progress Bar -->
                <div class="w-full bg-[#0d2137] rounded-full h-2.5 overflow-hidden p-0.5 border border-[#1a3a5c]">
                    <div class="h-full rounded-full transition-all duration-300"
                         :class="refProgressPercent >= 100 ? 'bg-[#00ff9d] shadow-[0_0_10px_#00ff9d]' : 'bg-[#00d4ff] shadow-[0_0_10px_#00d4ff]'"
                         :style="'width: ' + refProgressPercent + '%'"></div>
                </div>

                <p class="text-xs text-[#00d4ff] font-semibold flex items-center gap-1.5 truncate font-mono">
                    <span class="material-symbols-outlined text-sm" :class="refUpdating ? 'animate-spin' : ''">terminal</span>
                    <span x-text="refProgressMessage || 'Menunggu respon server...'"></span>
                </p>

                <!-- Terminal Logs Console -->
                <div class="border border-[#1a3a5c] rounded-lg bg-[#050b14] p-3 font-mono text-[11px] text-[#8892b0] max-h-40 overflow-y-auto space-y-1 custom-scrollbar">
                    <template x-for="(logLine, logIdx) in refProgressLogs" :key="logIdx">
                        <div class="flex items-start gap-1.5">
                            <span class="text-[#00ff9d] select-none font-bold">&gt;</span>
                            <span class="break-all" :class="logIdx === refProgressLogs.length - 1 ? 'text-[#e0f0ff] font-semibold' : 'text-[#8892b0]'" x-text="logLine"></span>
                        </div>
                    </template>
                </div>
            </div>

            <!-- Grid 4 Kartu Framework Referensi (Dark Cyber Style) -->
            <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                <template x-for="ref in references" :key="ref.id">
                    <div class="p-5 rounded-xl border border-[#1a3a5c] bg-[#0a1628]/90 hover:border-[#00d4ff] transition-all flex flex-col justify-between shadow-[0_4px_20px_rgba(0,0,0,0.3)]">
                        <div>
                            <div class="flex items-start justify-between gap-2 mb-2">
                                <div class="flex items-center gap-2">
                                    <span class="material-symbols-outlined text-[#00d4ff] text-xl"
                                          x-text="ref.id === 'ecsirt' ? 'category' : (ref.id === 'mitre_attack' ? 'security' : (ref.id === 'mitre_d3fend' ? 'shield' : 'verified_user'))"></span>
                                    <h4 class="text-sm font-bold text-[#e0f0ff] font-['Sora']" x-text="ref.name"></h4>
                                </div>
                                <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-[#00ff9d]/10 text-[#00ff9d] border border-[#00ff9d]/30 shrink-0 font-mono">AKTIF</span>
                            </div>

                            <p class="text-xs text-[#8892b0] mb-3 font-mono" x-text="ref.source"></p>

                            <div class="space-y-1.5 text-xs border-t border-[#1a3a5c] pt-3 text-[#8892b0] font-mono">
                                <div class="flex items-center justify-between">
                                    <span>Versi Aktif:</span>
                                    <span class="font-semibold text-[#e0f0ff]" x-text="ref.version"></span>
                                </div>
                                <div class="flex items-center justify-between">
                                    <span>Jumlah Data:</span>
                                    <span class="font-bold text-[#00d4ff]" x-text="ref.record_count + ' Entitas'"></span>
                                </div>
                                <div class="flex items-center justify-between">
                                    <span>Pembaruan Terakhir:</span>
                                    <span class="text-[#7d8ca6]" x-text="ref.updated_at || '-'"></span>
                                </div>
                            </div>
                        </div>

                        <div class="mt-4 pt-3 border-t border-[#1a3a5c] flex items-center justify-between text-[11px] font-mono">
                            <span class="text-[#7d8ca6] truncate max-w-[200px]" x-text="ref.file_path" :title="ref.file_path"></span>
                            <a :href="ref.url" target="_blank" rel="noopener noreferrer" 
                               class="text-[#00d4ff] hover:text-[#00ff9d] hover:underline flex items-center gap-1 font-semibold">
                                <span>Sumber Resmi</span>
                                <span class="material-symbols-outlined text-xs">open_in_new</span>
                            </a>
                        </div>
                    </div>
                </template>
            </div>

            <div class="p-3.5 bg-[#0a1628] border border-[#1a3a5c] rounded-xl text-xs text-[#8892b0] leading-relaxed font-mono">
                <strong class="text-[#00d4ff]">Integritas Referensi Otomatis:</strong>
                Pembaruan mengunduh spesifikasi mutakhir langsung dari repositori resmi (MISP, MITRE STIX 2.1, D3FEND, NIST OSCAL). Jika koneksi jaringan luar terbatas, sistem otomatis menyinkronkan berkas master lokal terverifikasi tanpa gangguan operasional.
            </div>
        </div>
    </div>

    <!-- TAB 6: KEAMANAN AKUN ADMIN -->
    <div x-show="activeTab === 'akun'" class="card-cyber p-5 sm:p-6 bg-[#0d2137]/80 border border-[#1a3a5c] rounded-xl max-w-lg space-y-5">
        <div class="pb-3 border-b border-[#1a3a5c]">
            <h3 class="text-base font-bold text-[#e0f0ff] font-['Sora'] flex items-center gap-2">
                <span class="material-symbols-outlined text-[#00d4ff]">admin_panel_settings</span> Keamanan Akun Admin
            </h3>
        </div>

        <div class="space-y-4">
            <div class="p-3.5 bg-[#0a1628] rounded-xl border border-[#1a3a5c] flex items-center justify-between">
                <div>
                    <p class="text-xs font-mono text-[#8892b0]">Pengguna Masuk:</p>
                    <p class="text-sm font-bold text-[#e0f0ff] font-mono" x-text="currentUsername || 'admin'"></p>
                </div>
                <span class="px-2.5 py-1 rounded text-xs font-mono font-bold uppercase tracking-wider" 
                      :class="role === 'superadmin' ? 'bg-[#00ff9d]/10 text-[#00ff9d] border border-[#00ff9d]/30' : 'bg-[#ff8800]/10 text-[#ff8800] border border-[#ff8800]/30'" 
                      x-text="role"></span>
            </div>

            <div>
                <label class="block text-xs font-mono font-semibold text-[#8892b0] mb-1.5">Kata Sandi Baru:</label>
                <input type="password" x-model="akun.password" placeholder="Masukkan kata sandi baru" 
                       class="w-full text-xs font-mono p-3 rounded-lg border border-[#1a3a5c] bg-[#0a1628] text-[#e0f0ff] placeholder-[#7d8ca6] focus:border-[#00d4ff] focus:ring-1 focus:ring-[#00d4ff] outline-none transition-colors" />
                <p class="text-[11px] font-mono text-[#8892b0] mt-1.5 leading-relaxed">
                    Disimpan menggunakan enkripsi hash bcrypt. Setelah kata sandi berhasil diubah, Anda akan dialihkan untuk masuk kembali.
                </p>
            </div>

            <button type="button" @click="savePassword()" 
                    class="bg-[#00d4ff] hover:bg-[#00ff9d] text-[#0a1628] px-4 py-2.5 rounded-lg text-xs font-bold font-mono uppercase tracking-wider flex items-center gap-1.5 transition-all shadow-[0_0_15px_rgba(0,212,255,0.25)] cursor-pointer">
                <span class="material-symbols-outlined text-base">key</span> Perbarui Kata Sandi Saya
            </button>
        </div>
    </div>
</div>

<script>
document.addEventListener('alpine:init', () => {
    Alpine.data('settingsPanel', () => ({
        activeTab: 'umum',
        rssSubTab: 'international',
        role: 'viewer',
        currentUsername: '',
        statusApiKey: 'Belum Disetel',
        apiKeysList: [],
        testingApiKey: false,
        testResult: null,

        // CTI Reference Sources State
        references: [],
        loadingReferences: false,
        refUpdating: false,
        refProgressPercent: 0,
        refProgressStage: '',
        refProgressMessage: '',
        refProgressLogs: [],

        gemini: { api_key: '', temperature: 0.1, model_chain: '' },
        keywordsList: { mandiri: [], data: [], aset: [] },
        newKw: { mandiri: '', data: '', aset: '' },

        promptsData: [],
        promptCategories: ['Pipeline Harian', 'SITREP Tren Berita'],
        selectedPromptId: null,
        selectedPromptMeta: null,
        promptContent: '',

        rss: { international: [], indonesia: [] },
        addRssModal: false,
        newRss: { tipe: 'international', nama: '', feeds: '' },

        akun: { password: '' },

        async init() {
            window.loadSettings = this.fetchSettings.bind(this);
            await this.fetchSettings();
            await this.fetchReferenceInfo();
        },

        async fetchSettings() {
            try {
                // 1. Status autentikasi
                const authRes = await fetch('/api/auth/status');
                const authData = await authRes.json();
                if (authData.authenticated) {
                    this.role = authData.role || 'viewer';
                    this.currentUsername = authData.username || '';
                }

                // 2. Data konfigurasi sistem
                const res = await fetch('/api/settings');
                const data = await res.json();

                this.statusApiKey = data.gemini_api_key_set ? "Disetel" : "Belum Disetel";
                this.apiKeysList = data.api_keys || [];
                if (this.apiKeysList.length > 0) {
                    this.gemini.api_key = this.apiKeysList.join(', ');
                }
                this.gemini.temperature = data.temperature;
                this.gemini.model_chain = (data.model_chain || []).join(', ');

                if (data.keywords) {
                    this.keywordsList.mandiri = Array.isArray(data.keywords.indonesia_mandiri) ? [...data.keywords.indonesia_mandiri] : [];
                    this.keywordsList.data = Array.isArray(data.keywords.objek_data_sensitif) ? [...data.keywords.objek_data_sensitif] : [];
                    this.keywordsList.aset = Array.isArray(data.keywords.objek_aset_digital) ? [...data.keywords.objek_aset_digital] : [];
                }

                // Metadata prompts
                this.promptsData = Array.isArray(data.prompts) ? data.prompts : [];
                if (this.promptsData.length > 0) {
                    const dynamicCats = [...new Set(this.promptsData.map(p => p.kategori))].filter(Boolean);
                    if (dynamicCats.length > 0) {
                        this.promptCategories = dynamicCats;
                    }
                    if (!this.selectedPromptId) {
                        this.selectPrompt(this.promptsData[0]);
                    }
                }

                this.rss.international = data.rss_sources_international || [];
                this.rss.indonesia = data.rss_sources_indonesia || [];

            } catch (e) {
                console.error("Gagal load settings:", e);
            }
        },

        // --- Keyword Management ---
        addKeyword(kategori) {
            if (this.role !== 'superadmin') return alert('Hanya superadmin yang dapat menambah kata kunci.');
            const val = (this.newKw[kategori] || '').trim().toLowerCase();
            if (!val) return;
            if (this.keywordsList[kategori].includes(val)) {
                alert(`Kata kunci "${val}" sudah ada dalam daftar.`);
                return;
            }
            this.keywordsList[kategori].push(val);
            this.newKw[kategori] = '';
        },

        removeKeyword(kategori, idx) {
            if (this.role !== 'superadmin') return alert('Hanya superadmin yang dapat menghapus kata kunci.');
            const item = this.keywordsList[kategori][idx];
            if (confirm(`Hapus kata kunci "${item}" dari daftar?`)) {
                this.keywordsList[kategori].splice(idx, 1);
            }
        },

        async saveKeywords() {
            if (this.role !== 'superadmin') return alert('Hanya superadmin yang dapat menyimpan kata kunci.');
            const payload = {
                keywords: {
                    indonesia_mandiri: this.keywordsList.mandiri,
                    objek_data_sensitif: this.keywordsList.data,
                    objek_aset_digital: this.keywordsList.aset
                }
            };
            try {
                const res = await fetch('/api/settings', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                if (res.ok) {
                    alert('Seluruh kamus kata kunci scraping berhasil disimpan ke database!');
                } else {
                    alert('Gagal menyimpan kata kunci.');
                }
            } catch (e) {
                alert('Kesalahan jaringan: ' + e);
            }
        },

        // --- Prompts Management ---
        getPromptsByCategory(kat) {
            return this.promptsData.filter(p => p.kategori === kat);
        },

        async selectPrompt(p) {
            this.selectedPromptId = p.id;
            this.selectedPromptMeta = p;
            this.promptContent = 'Memuat isi prompt...';
            try {
                const res = await fetch(`/api/settings/prompts/${p.id}`);
                const data = await res.json();
                if (res.ok) {
                    this.promptContent = data.isi;
                } else {
                    this.promptContent = 'Gagal memuat isi prompt.';
                }
            } catch (e) {
                this.promptContent = 'Gagal memuat isi prompt: ' + e;
            }
        },

        async savePrompt() {
            if (this.role !== 'superadmin') return alert('Hanya superadmin yang dapat menyimpan prompt.');
            if (!this.selectedPromptId) return;

            const payload = {};
            payload[this.selectedPromptId] = this.promptContent;
            try {
                const res = await fetch('/api/settings/prompts', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                if (res.ok) {
                    alert("Template Prompt '" + this.selectedPromptMeta.nama + "' berhasil disimpan ke database!");
                } else {
                    alert("Gagal menyimpan prompt.");
                }
            } catch (e) {
                alert("Kesalahan jaringan saat menyimpan prompt.");
            }
        },

        // --- RSS Management ---
        openAddRssModal(tipe) {
            this.newRss = { tipe: tipe || 'international', nama: '', feeds: '' };
            this.addRssModal = true;
        },

        toggleRss(tipe, idx) {
            this.rss[tipe][idx].active = this.rss[tipe][idx].active === false ? true : false;
        },

        deleteRss(tipe, idx) {
            const nama = this.rss[tipe][idx].nama || 'sumber feed ini';
            if (confirm(`Yakin ingin menghapus ${nama} dari daftar pantauan?`)) {
                this.rss[tipe].splice(idx, 1);
            }
        },

        submitNewRss() {
            if (!this.newRss.nama || !this.newRss.feeds) return alert("Silakan lengkapi nama media dan URL feed!");
            const fds = this.newRss.feeds.split(',').map(s => s.trim()).filter(s => s);
            this.rss[this.newRss.tipe].push({
                nama: this.newRss.nama,
                feeds: fds,
                active: true
            });
            this.addRssModal = false;
            this.newRss = { tipe: this.rssSubTab, nama: '', feeds: '' };
        },

        async saveRss() {
            if (this.role !== 'superadmin') return alert('Hanya superadmin yang dapat menyimpan sumber RSS.');
            try {
                const res = await fetch('/api/settings/rss', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(this.rss)
                });
                if (res.ok) {
                    alert("Daftar sumber RSS berhasil diperbarui!");
                } else {
                    alert("Gagal menyimpan sumber RSS.");
                }
            } catch (e) {
                alert("Kesalahan jaringan saat menyimpan RSS.");
            }
        },

        // --- API Key & General LLM ---
        async saveApiKeysOnly() {
            if (this.role !== 'superadmin') return alert('Hanya superadmin yang dapat menyimpan API Key.');
            const keys = this.gemini.api_key.replace(/\\n/g, ',').split(',').map(s => s.trim()).filter(Boolean);
            try {
                const res = await fetch('/api/settings', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ gemini: { api_key: keys } })
                });
                if (res.ok) {
                    this.apiKeysList = keys;
                    this.statusApiKey = keys.length > 0 ? "Disetel" : "Belum Disetel";
                    alert('API Key berhasil disimpan permanen ke database!');
                } else {
                    alert('Gagal menyimpan API Key ke server.');
                }
            } catch (e) {
                alert('Gagal menyimpan API Key: ' + e);
            }
        },

        async testApiKeyConnection() {
            this.testingApiKey = true;
            this.testResult = null;
            const primaryKey = this.gemini.api_key.replace(/\\n/g, ',').split(',')[0].trim();
            try {
                const res = await fetch('/api/settings/test-key', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ api_key: primaryKey })
                });
                const data = await res.json();
                if (res.ok && data.status === 'ok') {
                    this.testResult = { ok: true, message: data.message };
                } else {
                    this.testResult = { ok: false, message: data.message || 'Koneksi gagal tersambung ke Google API.' };
                }
            } catch (e) {
                this.testResult = { ok: false, message: 'Kesalahan jaringan: ' + e };
            } finally {
                this.testingApiKey = false;
            }
        },

        async saveUmum() {
            if (this.role !== 'superadmin') return alert('Hanya superadmin yang dapat menyimpan pengaturan.');
            const payload = {
                gemini: {
                    temperature: parseFloat(this.gemini.temperature),
                    model_chain: this.gemini.model_chain.split(',').map(s => s.trim()).filter(s => s)
                }
            };
            if (this.gemini.api_key.trim()) {
                payload.gemini.api_key = this.gemini.api_key.replace(/\\n/g, ',').split(',').map(s => s.trim()).filter(Boolean);
            }

            try {
                const res = await fetch('/api/settings', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                if (res.ok) {
                    alert("Pengaturan Parameter LLM berhasil disimpan!");
                    await this.fetchSettings();
                } else {
                    alert("Gagal menyimpan pengaturan umum.");
                }
            } catch (e) {
                alert("Kesalahan jaringan saat menyimpan.");
            }
        },

        // --- CTI References ---
        async fetchReferenceInfo() {
            this.loadingReferences = true;
            try {
                const res = await fetch('/api/settings/references-info');
                if (res.ok) {
                    const data = await res.json();
                    if (data && data.references) {
                        this.references = data.references;
                    }
                }
            } catch (e) {
                console.error("Gagal mengambil info referensi CTI:", e);
            } finally {
                this.loadingReferences = false;
            }
        },

        async updateReferences() {
            if (this.role !== 'superadmin') {
                return alert('Hanya superadmin yang dapat memperbarui referensi CTI.');
            }
            if (this.refUpdating) return;

            this.refUpdating = true;
            this.refProgressPercent = 0;
            this.refProgressStage = 'init';
            this.refProgressMessage = 'Menghubungkan ke repositori resmi...';
            this.refProgressLogs = [];

            try {
                const res = await fetch('/api/settings/update-references', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });

                if (!res.ok) {
                    alert('Gagal memulai sinkronisasi sumber referensi.');
                    this.refUpdating = false;
                    return;
                }

                const reader = res.body.getReader();
                const decoder = new TextDecoder('utf-8');
                let buffer = '';

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;
                    buffer += decoder.decode(value, { stream: true });
                    const lines = buffer.split('\\n');
                    buffer = lines.pop();

                    for (const line of lines) {
                        if (!line.trim()) continue;
                        try {
                            const evt = JSON.parse(line);
                            if (typeof evt.percent === 'number') {
                                this.refProgressPercent = evt.percent;
                            }
                            if (evt.stage) {
                                this.refProgressStage = evt.stage;
                            }
                            if (evt.message) {
                                this.refProgressMessage = evt.message;
                                this.refProgressLogs.push(`[${evt.timestamp || new Date().toLocaleTimeString()}] ${evt.message}`);
                            }
                            if (evt.status === 'completed') {
                                alert('Pembaruan 4 sumber referensi CTI berhasil diselesaikan!');
                            }
                        } catch (err) {
                            console.error("Parse progress line error:", err, line);
                        }
                    }
                }

                await this.fetchReferenceInfo();
            } catch (e) {
                alert('Koneksi terputus saat memperbarui referensi: ' + e);
            } finally {
                this.refUpdating = false;
            }
        },

        // --- Account Security ---
        async savePassword() {
            if (!this.akun.password) return alert("Silakan masukkan kata sandi baru.");
            if (!confirm("Yakin ingin mengubah kata sandi akun Anda? Anda harus masuk kembali setelah ini.")) return;

            try {
                const res = await fetch('/api/settings/admin/password', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ password_baru: this.akun.password })
                });
                if (res.ok) {
                    alert("Kata sandi berhasil diperbarui. Mengalihkan ke halaman masuk...");
                    await fetch('/api/auth/logout', { method: 'POST' });
                    window.location.href = "/login";
                } else {
                    const data = await res.json();
                    alert(data.message || "Gagal mengubah kata sandi.");
                }
            } catch (e) {
                alert("Kesalahan jaringan saat memperbarui kata sandi.");
            }
        }
    }));
});
</script>
"""

with open("scratch/cyber_settings.html", "w", encoding="utf-8") as f:
    f.write(cyber_settings.strip())
print("Created scratch/cyber_settings.html")
