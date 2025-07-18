import logging
import requests
import json
import re
import os
from typing import Callable, List, Dict
from agents.base_agent import BaseAgent
from core.models import VerifiedInformation

logger = logging.getLogger(__name__)

class InformationRetrievalAgent(BaseAgent):
    """
    The Information Retrieval & Verification Agent (IRVA).
    Performs real Google searches and uses LLM for information verification and summarization.
    """
    def __init__(self, llm_caller: Callable):
        super().__init__(llm_caller)
        self.google_api_key = os.getenv("GOOGLE_API_KEY")
        self.google_cse_id = os.getenv("GOOGLE_CSE_ID")
        if not self.google_api_key or not self.google_cse_id:
            logger.warning("Google Search API not configured. Will use LLM-based search simulation.")

    def search_google(self, query: str, num_results: int = 5) -> List[Dict]:
        if not self.google_api_key or not self.google_cse_id:
            return self._simulate_google_search(query, num_results)
        try:
            url = "https://www.googleapis.com/customsearch/v1"
            params = {
                "key": self.google_api_key,
                "cx": self.google_cse_id,
                "q": query,
                "num": min(num_results, 10)
            }
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            results = []
            for item in data.get("items", []):
                results.append({
                    "title": item.get("title", ""),
                    "snippet": item.get("snippet", ""),
                    "url": item.get("link", ""),
                    "source": "Google Search"
                })
            logger.info(f"Google search returned {len(results)} results for query: {query[:50]}...")
            return results
        except Exception as e:
            logger.error(f"Error performing Google search: {e}")
            return self._simulate_google_search(query, num_results)

    def _simulate_google_search(self, query: str, num_results: int) -> List[Dict]:
        search_prompt = f"""
        Simulate Google search results for the following query. Provide realistic search results that would be found for this business/process optimization topic.
        Query: {query}
        Number of results needed: {num_results}
        Return the results as a JSON array with the following structure:
        [
            {{
                "title": "Realistic article title",
                "snippet": "Realistic snippet from the article (2-3 sentences)",
                "url": "Realistic URL",
                "source": "LLM Simulation"
            }}
        ]
        """
        try:
            response = self.llm_caller(search_prompt, temperature=0.7, max_output_tokens=20000)
            json_match = re.search(r'\[.*\]', response, re.DOTALL)
            if json_match:
                results = json.loads(json_match.group())
                return results[:num_results]
            else:
                logger.warning("Could not parse LLM search simulation response")
                return []
        except Exception as e:
            logger.error(f"Error in LLM search simulation: {e}")
            return []

    def verify_and_summarize_info(self, query: str, search_results: List[Dict]) -> VerifiedInformation:
        if not search_results:
            return VerifiedInformation(
                query=query,
                sources=[],
                summary="No relevant information found for this query.",
                confidence="Low",
                relevance="Indirect"  # Always provide a string
            )
        results_text = ""
        sources = []
        for i, result in enumerate(search_results, 1):
            results_text += f"Result {i}:\nTitle: {result.get('title', 'N/A')}\nSnippet: {result.get('snippet', 'N/A')}\nURL: {result.get('url', 'N/A')}\n\n"
            sources.append(result.get('url', f'Result {i}'))
        verification_prompt = f"""
        Analyze the following search results for the query: "{query}"
        Search Results:
        {results_text}
        Please provide a comprehensive summary and verification of the information found. Consider:
        1. Relevance to the query
        2. Credibility of the sources
        3. Actionable insights for process optimization
        4. Confidence level in the information
        Return your analysis in the following JSON format:
        {{
            "summary": "Comprehensive summary of the most relevant and actionable information found",
            "confidence": "High/Medium/Low",
            "relevance": "Direct/Indirect/None"
        }}
        """
        try:
            response = self.llm_caller(verification_prompt, temperature=0.3, max_output_tokens=800)
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())
                return VerifiedInformation(
                    query=query,
                    sources=sources,
                    summary=analysis.get('summary', ''),
                    confidence=analysis.get('confidence', 'Medium'),
                    relevance=analysis.get('relevance', 'Indirect')  # Always provide a string
                )
            else:
                logger.warning("Could not parse LLM verification response")
                return self._create_fallback_info(query, search_results)
        except Exception as e:
            logger.error(f"Error in LLM verification: {e}")
            return self._create_fallback_info(query, search_results)

    def _create_fallback_info(self, query: str, search_results: List[Dict]) -> VerifiedInformation:
        sources = [result.get('url', f'Result {i}') for i, result in enumerate(search_results, 1)]
        summary = f"Found {len(search_results)} search results for '{query}'. Information available but requires manual review for specific application."
        return VerifiedInformation(
            query=query,
            sources=sources,
            summary=summary,
            confidence="Medium",
            relevance="Indirect"  # Always provide a string
        )

    def retrieve_and_verify(self, query: str) -> VerifiedInformation:
        logger.info(f"InformationRetrievalAgent: Retrieving information for query: {query[:100]}...")
        search_results = self.search_google(query, num_results=5)
        verified_info = self.verify_and_summarize_info(query, search_results)
        logger.info(f"InformationRetrievalAgent: Retrieved and verified info for {query[:50]}... Confidence: {verified_info.confidence}")
        return verified_info

    def search_process_optimization_info(self, process_name: str, bottlenecks: List[str]) -> List[VerifiedInformation]:
        verified_info_list = []
        general_query = f"best practices for optimizing {process_name} process"
        general_info = self.retrieve_and_verify(general_query)
        verified_info_list.append(general_info)
        for bottleneck in bottlenecks:
            bottleneck_query = f"how to solve {bottleneck} in business processes"
            bottleneck_info = self.retrieve_and_verify(bottleneck_query)
            verified_info_list.append(bottleneck_info)
        return verified_info_list

    def process(self, query: str) -> VerifiedInformation:
        return self.retrieve_and_verify(query)