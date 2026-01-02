"""
Academic Paper Search - Integration with Semantic Scholar and arXiv.
Provides unified interface for literature search and citation analysis.
"""
import os
import asyncio
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime
import aiohttp

from shared.logger import get_logger

logger = get_logger(__name__)


@dataclass
class Paper:
    """Represents an academic paper"""
    paper_id: str
    title: str
    abstract: str
    authors: List[str]
    year: int
    venue: Optional[str] = None
    citation_count: int = 0
    url: Optional[str] = None
    pdf_url: Optional[str] = None
    doi: Optional[str] = None
    arxiv_id: Optional[str] = None
    source: str = "unknown"
    categories: List[str] = field(default_factory=list)
    references: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "paper_id": self.paper_id,
            "title": self.title,
            "abstract": self.abstract,
            "authors": self.authors,
            "year": self.year,
            "venue": self.venue,
            "citation_count": self.citation_count,
            "url": self.url,
            "pdf_url": self.pdf_url,
            "doi": self.doi,
            "arxiv_id": self.arxiv_id,
            "source": self.source,
            "categories": self.categories
        }


class SemanticScholarClient:
    """Client for Semantic Scholar API"""
    
    BASE_URL = "https://api.semanticscholar.org/graph/v1"
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("SEMANTIC_SCHOLAR_API_KEY")
        self.headers = {}
        if self.api_key:
            self.headers["x-api-key"] = self.api_key
    
    async def search(
        self,
        query: str,
        limit: int = 20,
        year_from: Optional[int] = None,
        fields_of_study: Optional[List[str]] = None
    ) -> List[Paper]:
        """
        Search for papers on Semantic Scholar.
        
        Args:
            query: Search query
            limit: Maximum number of results
            year_from: Filter papers from this year onwards
            fields_of_study: Filter by fields (e.g., ["Computer Science"])
            
        Returns:
            List of Paper objects
        """
        params = {
            "query": query,
            "limit": min(limit, 100),
            "fields": "paperId,title,abstract,authors,year,venue,citationCount,url,openAccessPdf,externalIds,s2FieldsOfStudy"
        }
        
        if year_from:
            params["year"] = f"{year_from}-"
        
        if fields_of_study:
            params["fieldsOfStudy"] = ",".join(fields_of_study)
        
        retries = 3
        for attempt in range(retries):
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{self.BASE_URL}/paper/search",
                        params=params,
                        headers=self.headers
                    ) as response:
                        if response.status == 429:
                            if attempt < retries - 1:
                                wait_time = (2 ** attempt) * 1
                                logger.warning("semantic_scholar_rate_limit", attempt=attempt+1, wait=wait_time)
                                await asyncio.sleep(wait_time)
                                continue
                            else:
                                logger.error("semantic_scholar_rate_limit_exceeded")
                                return []

                        if response.status != 200:
                            logger.error("semantic_scholar_error", status=response.status)
                            return []
                        
                        data = await response.json()
                        papers = []
                        
                        for item in data.get("data", []):
                            paper = Paper(
                                paper_id=item.get("paperId", ""),
                                title=item.get("title", ""),
                                abstract=item.get("abstract") or "",
                                authors=[a.get("name", "") for a in item.get("authors", [])],
                                year=item.get("year") or 0,
                                venue=item.get("venue"),
                                citation_count=item.get("citationCount", 0),
                                url=item.get("url"),
                                pdf_url=item.get("openAccessPdf", {}).get("url") if item.get("openAccessPdf") else None,
                                doi=item.get("externalIds", {}).get("DOI"),
                                arxiv_id=item.get("externalIds", {}).get("ArXiv"),
                                source="semantic_scholar",
                                categories=[f.get("category", "") for f in item.get("s2FieldsOfStudy", [])]
                            )
                            papers.append(paper)
                        
                        logger.info("semantic_scholar_search", query=query, results=len(papers))
                        return papers
                        
            except Exception as e:
                logger.error("semantic_scholar_search_failed", error=str(e))
                return []
        return []
    
    async def get_paper(self, paper_id: str) -> Optional[Paper]:
        """Get detailed paper information by ID"""
        fields = "paperId,title,abstract,authors,year,venue,citationCount,url,openAccessPdf,externalIds,references"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.BASE_URL}/paper/{paper_id}",
                    params={"fields": fields},
                    headers=self.headers
                ) as response:
                    if response.status != 200:
                        return None
                    
                    item = await response.json()
                    
                    return Paper(
                        paper_id=item.get("paperId", ""),
                        title=item.get("title", ""),
                        abstract=item.get("abstract") or "",
                        authors=[a.get("name", "") for a in item.get("authors", [])],
                        year=item.get("year") or 0,
                        venue=item.get("venue"),
                        citation_count=item.get("citationCount", 0),
                        url=item.get("url"),
                        pdf_url=item.get("openAccessPdf", {}).get("url") if item.get("openAccessPdf") else None,
                        doi=item.get("externalIds", {}).get("DOI"),
                        arxiv_id=item.get("externalIds", {}).get("ArXiv"),
                        source="semantic_scholar",
                        references=[r.get("paperId", "") for r in item.get("references", []) if r.get("paperId")]
                    )
        except Exception as e:
            logger.error("get_paper_failed", paper_id=paper_id, error=str(e))
            return None
    
    async def get_citations(self, paper_id: str, limit: int = 50) -> List[Paper]:
        """Get papers that cite this paper"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.BASE_URL}/paper/{paper_id}/citations",
                    params={"fields": "paperId,title,authors,year,citationCount", "limit": limit},
                    headers=self.headers
                ) as response:
                    if response.status != 200:
                        return []
                    
                    data = await response.json()
                    papers = []
                    
                    for item in data.get("data", []):
                        citing = item.get("citingPaper", {})
                        paper = Paper(
                            paper_id=citing.get("paperId", ""),
                            title=citing.get("title", ""),
                            abstract="",
                            authors=[a.get("name", "") for a in citing.get("authors", [])],
                            year=citing.get("year") or 0,
                            citation_count=citing.get("citationCount", 0),
                            source="semantic_scholar"
                        )
                        papers.append(paper)
                    
                    return papers
        except Exception as e:
            logger.error("get_citations_failed", paper_id=paper_id, error=str(e))
            return []


class ArxivClient:
    """Client for arXiv API"""
    
    BASE_URL = "http://export.arxiv.org/api/query"
    
    async def search(
        self,
        query: str,
        limit: int = 20,
        categories: Optional[List[str]] = None
    ) -> List[Paper]:
        """
        Search for papers on arXiv.
        
        Args:
            query: Search query
            limit: Maximum number of results
            categories: Filter by arXiv categories (e.g., ["cs.LG", "cs.AI"])
            
        Returns:
            List of Paper objects
        """
        # Build search query
        search_query = f"all:{query}"
        if categories:
            cat_query = " OR ".join([f"cat:{c}" for c in categories])
            search_query = f"({search_query}) AND ({cat_query})"
        
        params = {
            "search_query": search_query,
            "start": 0,
            "max_results": limit,
            "sortBy": "relevance",
            "sortOrder": "descending"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.BASE_URL, params=params) as response:
                    if response.status != 200:
                        logger.error("arxiv_error", status=response.status)
                        return []
                    
                    text = await response.text()
                    papers = self._parse_arxiv_response(text)
                    
                    logger.info("arxiv_search", query=query, results=len(papers))
                    return papers
                    
        except Exception as e:
            logger.error("arxiv_search_failed", error=str(e))
            return []
    
    def _parse_arxiv_response(self, xml_text: str) -> List[Paper]:
        """Parse arXiv XML response"""
        import xml.etree.ElementTree as ET
        
        papers = []
        
        try:
            root = ET.fromstring(xml_text)
            ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}
            
            for entry in root.findall("atom:entry", ns):
                # Extract arXiv ID
                id_elem = entry.find("atom:id", ns)
                arxiv_id = id_elem.text.split("/abs/")[-1] if id_elem is not None else ""
                
                # Extract other fields
                title = entry.find("atom:title", ns)
                abstract = entry.find("atom:summary", ns)
                published = entry.find("atom:published", ns)
                
                authors = []
                for author in entry.findall("atom:author", ns):
                    name = author.find("atom:name", ns)
                    if name is not None:
                        authors.append(name.text)
                
                categories = []
                for cat in entry.findall("arxiv:primary_category", ns):
                    if cat.get("term"):
                        categories.append(cat.get("term"))
                for cat in entry.findall("atom:category", ns):
                    if cat.get("term") and cat.get("term") not in categories:
                        categories.append(cat.get("term"))
                
                # Parse year from published date
                year = 0
                if published is not None and published.text:
                    try:
                        year = int(published.text[:4])
                    except ValueError:
                        pass
                
                paper = Paper(
                    paper_id=f"arxiv:{arxiv_id}",
                    title=title.text.strip().replace("\n", " ") if title is not None else "",
                    abstract=abstract.text.strip().replace("\n", " ") if abstract is not None else "",
                    authors=authors,
                    year=year,
                    arxiv_id=arxiv_id,
                    url=f"https://arxiv.org/abs/{arxiv_id}",
                    pdf_url=f"https://arxiv.org/pdf/{arxiv_id}.pdf",
                    source="arxiv",
                    categories=categories
                )
                papers.append(paper)
                
        except ET.ParseError as e:
            logger.error("arxiv_parse_error", error=str(e))
        
        return papers


class PaperSearchClient:
    """
    Unified client for searching academic papers across multiple sources.
    """
    
    def __init__(self):
        self.semantic_scholar = SemanticScholarClient()
        self.arxiv = ArxivClient()
    
    async def search(
        self,
        query: str,
        limit: int = 20,
        sources: Optional[List[str]] = None
    ) -> List[Paper]:
        """
        Search for papers across multiple sources.
        
        Args:
            query: Search query
            limit: Maximum results per source
            sources: List of sources to search ("semantic_scholar", "arxiv")
            
        Returns:
            Combined list of papers, deduplicated
        """
        sources = sources or ["semantic_scholar", "arxiv"]
        all_papers = []
        
        tasks = []
        if "semantic_scholar" in sources:
            tasks.append(self.semantic_scholar.search(query, limit))
        if "arxiv" in sources:
            tasks.append(self.arxiv.search(query, limit))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for result in results:
            if isinstance(result, list):
                all_papers.extend(result)
            elif isinstance(result, Exception):
                logger.error("search_source_failed", error=str(result))
        
        # Deduplicate by title similarity
        seen_titles = set()
        unique_papers = []
        for paper in all_papers:
            title_key = paper.title.lower()[:100]
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                unique_papers.append(paper)
        
        # Sort by citation count
        unique_papers.sort(key=lambda p: p.citation_count, reverse=True)
        
        return unique_papers
    
    async def get_paper_with_citations(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """Get paper details with citation network"""
        paper = await self.semantic_scholar.get_paper(paper_id)
        if not paper:
            return None
        
        citations = await self.semantic_scholar.get_citations(paper_id, limit=20)
        
        return {
            "paper": paper.to_dict(),
            "citations": [c.to_dict() for c in citations],
            "citation_count": len(citations)
        }
