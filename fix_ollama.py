with open("src/analytics/cti_agents.py", "r", encoding="utf-8") as f:
    content = f.read()

if "def _call_ollama_text" not in content:
    func_text = """
def _call_ollama_text(prompt: str, user_content: str, model: str = "llama3.2", num_predict: int = 400) -> str:
    import ollama
    try:
        resp = ollama.chat(
            model=model,
            messages=[
                {"role": "system", "content": prompt},
                {"role": "user", "content": user_content}
            ],
            options={"temperature": 0.1, "num_predict": num_predict}
        )
        return resp.get("message", {}).get("content", "")
    except Exception as e:
        logger.error(f"Ollama Call Error: {e}")
        return ""
"""
    content = content.replace("def _generate_section_1_makro(", func_text + "\ndef _generate_section_1_makro(")

with open("src/analytics/cti_agents.py", "w", encoding="utf-8") as f:
    f.write(content)
