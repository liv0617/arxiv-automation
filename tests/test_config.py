"""Test cases for the Config module."""

import unittest
import json
import os
import tempfile
from config import Config

class TestConfig(unittest.TestCase):
    """Test cases for the Config class."""
    
    def setUp(self):
        """Set up the test environment."""
        # Create a temporary config file
        self.temp_dir = tempfile.TemporaryDirectory()
        self.config_path = os.path.join(self.temp_dir.name, "test_config.json")
        
        # Sample config data
        self.config_data = {
            "llm_provider": "test_provider",
            "anthropic_model": "test_model",
            "search_terms": ["test1", "test2"],
            "max_results": 10
        }
        
        # Write the config data to the temporary file
        with open(self.config_path, "w") as f:
            json.dump(self.config_data, f)
            
        # Save original environment
        self.original_env = os.environ.copy()
            
    def tearDown(self):
        """Tear down the test environment."""
        # Clean up the temporary directory
        self.temp_dir.cleanup()
        
        # Restore original environment
        os.environ.clear()
        os.environ.update(self.original_env)
        
    def test_load_config(self):
        """Test loading configuration from a file."""
        config = Config(config_file=self.config_path)
        
        # Check if the config contains the expected values
        self.assertEqual(config["llm_provider"], "test_provider")
        self.assertEqual(config["anthropic_model"], "test_model")
        self.assertEqual(config["search_terms"], ["test1", "test2"])
        self.assertEqual(config["max_results"], 10)
        
        # Check if the config contains default values for missing keys
        self.assertEqual(config["run_time"], "16:00")
        
    def test_get_api_config(self):
        """Test getting API configuration."""
        # Override the test provider with a valid one
        with open(self.config_path, "w") as f:
            json.dump({"llm_provider": "anthropic", "anthropic_model": "test_model"}, f)
            
        # Set environment variables
        os.environ["ANTHROPIC_API_KEY"] = "test_api_key"
        
        config = Config(config_file=self.config_path)
        api_config = config.get_api_config()
        
        # Check if the API config contains the expected values
        self.assertEqual(api_config["model"], "test_model")
        self.assertEqual(api_config["api_key"], "test_api_key")
        
    def test_get_email_config(self):
        """Test getting email configuration."""
        # Set environment variables
        os.environ["SENDER_EMAIL"] = "test_sender@example.com"
        os.environ["RECIPIENT_EMAIL"] = "test_recipient@example.com"
        
        config = Config(config_file=self.config_path)
        email_config = config.get_email_config()
        
        # Check if the email config contains the expected values
        self.assertEqual(email_config["sender_email"], "test_sender@example.com")
        self.assertEqual(email_config["recipient_email"], "test_recipient@example.com")
        
    def test_update_config(self):
        """Test updating configuration."""
        config = Config(config_file=self.config_path)
        
        # Update the config
        config.update({"llm_provider": "updated_provider", "new_key": "new_value"})
        
        # Check if the config was updated
        self.assertEqual(config["llm_provider"], "updated_provider")
        self.assertEqual(config["new_key"], "new_value")
        
    def test_save_config(self):
        """Test saving configuration to a file."""
        config = Config(config_file=self.config_path)
        
        # Update the config
        config.update({"llm_provider": "saved_provider"})
        
        # Save the config
        config.save_config()
        
        # Load the config again
        new_config = Config(config_file=self.config_path)
        
        # Check if the saved config contains the updated value
        self.assertEqual(new_config["llm_provider"], "saved_provider")

if __name__ == '__main__':
    unittest.main()