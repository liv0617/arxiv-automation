"""Configuration settings for the arXiv automation application."""

import os
import json
from typing import Dict, List, Any
from pathlib import Path

class Config:
    """Configuration class for the arXiv automation application."""
    
    # Default configuration
    DEFAULT_CONFIG = {
        # LLM Provider settings (anthropic or openai)
        "llm_provider": "anthropic",
        
        # Model settings
        "anthropic_model": "claude-opus-4-20250514",
        "openai_model": "gpt-4",
        
        # Email settings reserved for future use
        
        # arXiv search settings
        "search_terms": ["interpretability", "explainability", "xai"],
        "categories": ["cs.AI", "cs.LG", "cs.CL"],
        "max_results": 50,
        
        # Cache settings
        "cache_dir": "paper_cache",
        
        # Scheduler settings
        "run_time": "16:00",
    }
    
    # Path to config file
    CONFIG_FILE = "config.json"
    
    # Initialize with merged configuration
    def __init__(self, config_file=None):
        self.config_file = config_file or self.CONFIG_FILE
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file and merge with defaults."""
        config = self.DEFAULT_CONFIG.copy()
        
        # Try to load from config file
        config_path = Path(self.config_file)
        if config_path.exists():
            try:
                with open(config_path, "r") as f:
                    file_config = json.load(f)
                    config.update(file_config)
            except Exception as e:
                print(f"Error loading config file: {e}")
        
        return config
    
    def save_config(self) -> bool:
        """Save current configuration to file."""
        try:
            # Create a copy without sensitive information
            save_config = self.config.copy()
            
            with open(self.config_file, "w") as f:
                json.dump(save_config, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving config file: {e}")
            return False
    
    def get_api_config(self) -> Dict:
        """Get API configuration based on the selected provider."""
        if self.config["llm_provider"].lower() == "anthropic":
            return {
                "model": self.config["anthropic_model"],
                "api_key": os.environ.get("ANTHROPIC_API_KEY", "")
            }
        elif self.config["llm_provider"].lower() == "openai":
            return {
                "model": self.config["openai_model"],
                "api_key": os.environ.get("OPENAI_API_KEY", "")
            }
        else:
            raise ValueError(f"Unsupported LLM provider: {self.config['llm_provider']}")
    
    def get_email_config(self) -> Dict:
        """Get email configuration."""
        return {
            "sender_email": os.environ.get("SENDER_EMAIL", ""),
            "recipient_email": os.environ.get("RECIPIENT_EMAIL", "")
        }
    
    def get_arxiv_config(self) -> Dict:
        """Get arXiv search configuration."""
        return {
            "search_terms": self.config["search_terms"],
            "categories": self.config["categories"],
            "max_results": self.config["max_results"],
            "cache_dir": self.config["cache_dir"],
            "user_interests": self.config.get("user_interests", ""),
        }
    
    def get_scheduler_config(self) -> Dict:
        """Get scheduler configuration."""
        return {
            "run_time": self.config["run_time"],
        }
    
    def update(self, new_config: Dict[str, Any]) -> None:
        """Update configuration with new values."""
        self.config.update(new_config)
    
    def __getitem__(self, key: str) -> Any:
        """Get config item by key."""
        return self.config.get(key)
    
    def __setitem__(self, key: str, value: Any) -> None:
        """Set config item by key."""
        self.config[key] = value