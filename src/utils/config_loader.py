import os
import yaml
from pathlib import Path

class ConfigLoader:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigLoader, cls).__new__(cls)
            cls._instance._load_all()
        return cls._instance

    def _load_all(self):
        base_dir = Path(__file__).resolve().parent.parent.parent
        config_dir = base_dir / "config"
        
        # Load main config
        config_path = config_dir / "config.yaml"
        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

        # Load rules
        rules_dir = config_dir / "rules"
        self.rules = {}
        if rules_dir.exists():
            for rule_file in rules_dir.glob("*.yaml"):
                with open(rule_file, "r", encoding="utf-8") as f:
                    self.rules[rule_file.stem] = yaml.safe_load(f)
                    
        # Load prompts
        prompts_dir = config_dir / "prompts"
        self.prompts = {}
        if prompts_dir.exists():
            for prompt_file in prompts_dir.glob("*.txt"):
                with open(prompt_file, "r", encoding="utf-8") as f:
                    self.prompts[prompt_file.stem] = f.read()

    @classmethod
    def get_config(cls):
        return cls().config
        
    @classmethod
    def get_rules(cls, rule_name):
        return cls().rules.get(rule_name, {})
        
    @classmethod
    def get_prompt(cls, prompt_name):
        return cls().prompts.get(prompt_name, "")


    @classmethod
    def save_config(cls, new_config: dict):
        """Menyimpan perubahan config.yaml (dipanggil dari admin panel)."""
        instance = cls()
        base_dir = Path(__file__).resolve().parent.parent.parent
        config_path = base_dir / "config" / "config.yaml"
        instance.config.update(new_config)
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(instance.config, f, sort_keys=False, allow_unicode=True)
        cls._instance = None  # Force reload

