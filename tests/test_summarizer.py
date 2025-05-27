"""Test cases for the PaperSummarizer module."""

import unittest
from unittest.mock import MagicMock, patch
from modules.summarizer import PaperSummarizer
from modules.api_clients import APIClient

class MockAPIClient(APIClient):
    """Mock API client for testing."""
    
    def __init__(self):
        """Initialize the mock client."""
        super().__init__(model="mock-model", api_key="mock-key")
        
    def initialize_client(self):
        """Mock initialization."""
        pass
        
    def send_request(self, prompt: str, **kwargs):
        """Mock sending a request."""
        mock_response = MagicMock()
        mock_response.completion = "This is a mock summary of the paper."
        return mock_response

class TestPaperSummarizer(unittest.TestCase):
    """Test cases for the PaperSummarizer class."""
    
    def setUp(self):
        """Set up the test environment."""
        self.api_client = MockAPIClient()
        self.summarizer = PaperSummarizer(self.api_client)
        
        # Sample paper data
        self.paper_data = {
            'id': '2106.09685',
            'title': 'Understanding Deep Learning Requires Rethinking Generalization',
            'summary': 'This is the abstract of the paper.',
            'published': '2021-06-17',
            'authors': ['Author One', 'Author Two'],
            'links': {
                'alternate': [{'href': 'https://arxiv.org/abs/2106.09685', 'title': 'arXiv'}]
            },
            'categories': ['cs.LG', 'cs.AI']
        }
        
    def test_generate_summary_prompt(self):
        """Test generating a summary prompt."""
        prompt = self.summarizer._generate_summary_prompt()
        
        # Check if the prompt contains expected elements
        self.assertIn("summary", prompt.lower())
        self.assertIn("interpretability", prompt.lower())
        self.assertIn("XML", prompt)
        self.assertIn("<summary>", prompt)
        self.assertIn("<methods>", prompt)
        
        
    def test_summarize_paper(self):
        """Test summarizing a paper."""
        # Create a test PDF URL
        pdf_url = "https://arxiv.org/pdf/2106.09685.pdf"
        
        # Mock the API client response
        mock_response = """
        <summary>This is a test summary</summary>
        <methods>Test methods</methods>
        <contributions>Test contributions</contributions>
        <limitations>Test limitations</limitations>
        """
        self.api_client.send_request = MagicMock(return_value=mock_response)
        
        summary = self.summarizer.summarize_paper(pdf_url)
        
        # Check if the summary is HTML string
        self.assertIsInstance(summary, str)
        self.assertIn("This is a test summary", summary)
        self.assertIn("Test methods", summary)
        self.assertIn("Test contributions", summary)
            
    def test_summarize_papers(self):
        """Test summarizing multiple papers."""
        from modules.arxiv import PaperData
        
        # Create test papers
        papers = [
            PaperData(
                id="1",
                title="Paper 1",
                url="https://arxiv.org/abs/1",
                pdf_url="https://arxiv.org/pdf/1.pdf"
            ),
            PaperData(
                id="2", 
                title="Paper 2",
                url="https://arxiv.org/abs/2",
                pdf_url="https://arxiv.org/pdf/2.pdf"
            )
        ]
        
        # Mock the summarize_paper method
        mock_summary = "<h3>Summary</h3><p>Test summary</p>"
        with patch.object(self.summarizer, 'summarize_paper', return_value=mock_summary):
            result = self.summarizer.summarize_papers(papers)
            
            # Check if we got the expected number of papers back
            self.assertEqual(len(result), 2)
            
            # Check if summaries were added to papers
            for paper in result:
                self.assertIsNotNone(paper.summary)
                self.assertEqual(paper.summary, mock_summary)

if __name__ == '__main__':
    unittest.main()