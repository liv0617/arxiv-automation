"""Tests for the paper recommender module."""

import unittest
from unittest.mock import Mock, patch
from modules.recommender import PaperRecommender
from modules.arxiv import PaperData


class TestPaperRecommender(unittest.TestCase):
    """Test cases for PaperRecommender class."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_client = Mock()
        self.user_interests = "mechanistic interpretability and circuit discovery"
        self.recommender = PaperRecommender(self.mock_client, self.user_interests)

    def test_init(self):
        """Test PaperRecommender initialization."""
        self.assertEqual(self.recommender._user_interests, self.user_interests)
        self.assertEqual(self.recommender._client, self.mock_client)

    def test_generate_recommendation_prompt(self):
        """Test prompt generation for recommendations."""
        abstracts = [
            {
                'id': '2401.01234',
                'title': 'Test Paper 1',
                'abstract': 'This paper explores circuit discovery in neural networks.'
            },
            {
                'id': '2401.01235',
                'title': 'Test Paper 2',
                'abstract': 'This paper discusses attention mechanisms in transformers.'
            }
        ]
        
        prompt = self.recommender._generate_recommendation_prompt(abstracts)
        
        # Check that prompt contains expected elements
        self.assertIn(self.user_interests, prompt)
        self.assertIn('Test Paper 1', prompt)
        self.assertIn('Test Paper 2', prompt)
        self.assertIn('2401.01234', prompt)
        self.assertIn('2401.01235', prompt)
        self.assertIn('circuit discovery', prompt)
        self.assertIn('attention mechanisms', prompt)

    def test_parse_recommendations(self):
        """Test parsing of recommendation response."""
        response = '''
        <recommendations>
        <paper id="2401.01234" score="5" recommend="true">Highly relevant to circuit discovery</paper>
        <paper id="2401.01235" score="2" recommend="false">Not very relevant</paper>
        <paper id="2401.01236" score="4" recommend="true">Good match for interpretability</paper>
        </recommendations>
        '''
        
        recommended_ids = self.recommender._parse_recommendations(response)
        
        # Should only return papers marked as recommend="true"
        self.assertIn('2401.01234', recommended_ids)
        self.assertIn('2401.01236', recommended_ids)
        self.assertNotIn('2401.01235', recommended_ids)
        self.assertEqual(len(recommended_ids), 2)

    def test_recommend_papers_empty_list(self):
        """Test recommendation with empty paper list."""
        result = self.recommender.recommend_papers([])
        self.assertEqual(result, [])

    def test_recommend_papers_no_abstracts(self):
        """Test recommendation with papers without abstracts."""
        papers = [
            PaperData(id='1', title='Paper 1', url='url1'),
            PaperData(id='2', title='Paper 2', url='url2')
        ]
        
        result = self.recommender.recommend_papers(papers)
        self.assertEqual(result, [])

    def test_recommend_papers_success(self):
        """Test successful paper recommendation."""
        papers = [
            PaperData(
                id='2401.01234',
                title='Paper 1',
                url='url1',
                abstract='This paper explores circuit discovery.'
            ),
            PaperData(
                id='2401.01235',
                title='Paper 2',
                url='url2',
                abstract='This paper discusses unrelated topics.'
            )
        ]
        
        # Mock the LLM response
        mock_response = '''
        <recommendations>
        <paper id="2401.01234" score="5" recommend="true">Highly relevant</paper>
        <paper id="2401.01235" score="2" recommend="false">Not relevant</paper>
        </recommendations>
        '''
        self.mock_client.send_request.return_value = mock_response
        
        result = self.recommender.recommend_papers(papers)
        
        # Should return only the recommended paper
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, '2401.01234')
        self.assertEqual(result[0].title, 'Paper 1')

    def test_recommend_papers_api_error(self):
        """Test recommendation when API call fails."""
        papers = [
            PaperData(
                id='2401.01234',
                title='Paper 1',
                url='url1',
                abstract='Test abstract'
            )
        ]
        
        # Mock API error
        self.mock_client.send_request.side_effect = Exception("API Error")
        
        result = self.recommender.recommend_papers(papers)
        
        # Should return all papers as fallback
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].id, '2401.01234')


class TestOptionalRecommender(unittest.TestCase):
    """Test cases for optional recommender functionality."""

    def test_empty_user_interests(self):
        """Test that empty user interests string works."""
        mock_client = Mock()
        
        # Test with empty string
        recommender = PaperRecommender(mock_client, "")
        self.assertEqual(recommender._user_interests, "")
        
        # Test with whitespace only
        recommender = PaperRecommender(mock_client, "   ")
        self.assertEqual(recommender._user_interests, "   ")

    def test_none_user_interests(self):
        """Test that None user interests can be handled."""
        mock_client = Mock()
        
        # This should work without crashing
        recommender = PaperRecommender(mock_client, None)
        self.assertIsNone(recommender._user_interests)


if __name__ == '__main__':
    unittest.main()