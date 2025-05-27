"""Test cases for the ArxivClient module."""

import unittest
from modules.arxiv import ArxivClient

class TestArxivClient(unittest.TestCase):
    """Test cases for the ArxivClient class."""
    
    def setUp(self):
        """Set up the test environment."""
        self.client = ArxivClient()
    
    def test_construct_query(self):
        """Test constructing a query string."""
        # Test with search terms
        query = self.client._construct_query(search_terms=["interpretability", "neural networks"])
        self.assertIn("interpretability", query)
        self.assertIn("neural networks", query)
        
        # Test with categories
        query = self.client._construct_query(categories=["cs.AI", "cs.LG"])
        self.assertIn("cat:cs.AI", query)
        self.assertIn("cat:cs.LG", query)
        
        # Test with both search terms and categories
        query = self.client._construct_query(
            search_terms=["interpretability"], 
            categories=["cs.AI", "cs.LG"]
        )
        self.assertIn("interpretability", query)
        self.assertIn("cat:cs.AI", query)
        self.assertIn("AND", query)
        
    def test_search(self):
        """Test searching for papers."""
        # Simple search with limited results
        papers = self.client.search(
            search_terms=["interpretability"], 
            categories=["cs.AI"], 
            max_results=3
        )
        
        # Check if we got the expected results
        self.assertLessEqual(len(papers), 3)
        
        # Check paper structure
        if papers:
            paper = papers[0]
            self.assertIsNotNone(paper.id)
            self.assertIsNotNone(paper.title)
            self.assertIsNotNone(paper.abstract)
            self.assertIsNotNone(paper.authors)
            self.assertIsNotNone(paper.url)
            
    def test_get_paper_by_id(self):
        """Test retrieving a paper by ID."""
        # Use a known paper ID
        paper_id = "2106.09685"  # Example paper ID
        
        paper = self.client.get_paper_by_id(paper_id)
        
        # Check if we got the expected paper
        self.assertIsNotNone(paper)
        # ArXiv might append a version number to the ID (like v1, v2)
        self.assertTrue(paper.id.startswith(paper_id))
        self.assertIsNotNone(paper.title)
        self.assertIsNotNone(paper.abstract)

if __name__ == '__main__':
    unittest.main()