import ast
import sys

def remove_functions(source_code, func_names):
    tree = ast.parse(source_code)
    new_body = [node for node in tree.body if not (isinstance(node, ast.FunctionDef) and node.name in func_names)]
    tree.body = new_body
    return ast.unparse(tree)

cti_path = "src/analytics/cti_agents.py"
with open(cti_path, "r", encoding="utf-8") as f:
    source = f.read()

funcs = [
    "_deteksi_sektor_spesifik",
    "_deteksi_penyerang_spesifik",
    "_deteksi_senjata_spesifik",
    "_deteksi_dampak_spesifik",
    "_ekstrak_alur_serangan_teknis",
    "_build_section_1_fallback",
    "_build_section_2_fallback",
    "_build_section_3_fallback",
    "_build_section_5_fallback",
    "_buat_fallback_sitrep_deterministik"
]

try:
    # First get the original untouched file from git if possible, or just fix the messy one?
    # Actually, the file is currently corrupted, let's restore it using git checkout and then use AST
    import subprocess
    subprocess.run(["git", "checkout", cti_path], cwd="D:/penting/magang/kominfo/NOTIFIKASI-BERITA")
except:
    pass
