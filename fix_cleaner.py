import re
import os

with open("src/utils/llm_text_cleaner.py", "r", encoding="utf-8") as f:
    content = f.read()

# Add import os if not there
if "import os" not in content:
    content = content.replace("import re", "import os\nimport re")

# Replace the _panjang_prefix_sama block
block_to_remove = r"def _panjang_prefix_sama\(a: str, b: str\) -> int:.*?(?=def bersihkan_output_llm)"
content = re.sub(block_to_remove, "", content, flags=re.DOTALL)

# Replace the usage
content = content.replace(
    "panjang_sama = _panjang_prefix_sama(teks, judul_atau_id)",
    "panjang_sama = len(os.path.commonprefix([teks.lower(), judul_atau_id.lower()]))"
)

with open("src/utils/llm_text_cleaner.py", "w", encoding="utf-8") as f:
    f.write(content)
