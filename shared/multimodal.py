"""
Multi-Modal Support - Handle images, time-series, and cross-modal data.
Provides unified interface for multi-modal research data.
"""
import os
import base64
from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass
from enum import Enum
import asyncio
import aiohttp
from pathlib import Path

from shared.logger import get_logger
from shared.llm_client import LLMClient, LLMProvider, get_default_client

logger = get_logger(__name__)


class ModalityType(Enum):
    """Supported data modalities"""
    TEXT = "text"
    IMAGE = "image"
    TABULAR = "tabular"
    TIME_SERIES = "time_series"
    AUDIO = "audio"


@dataclass
class MultiModalData:
    """Container for multi-modal data"""
    modality: ModalityType
    content: Any
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "modality": self.modality.value,
            "metadata": self.metadata
        }


class ImageAnalyzer:
    """
    Analyze images using Vision APIs.
    Supports OpenAI GPT-4 Vision and Anthropic Claude Vision.
    """
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client
    
    def _get_client(self) -> LLMClient:
        """Get or create LLM client"""
        if self.llm_client is None:
            try:
                self.llm_client = get_default_client()
            except Exception as e:
                logger.error("llm_client_init_failed", error=str(e))
                raise
        return self.llm_client
    
    async def analyze_image(
        self,
        image_path: Optional[str] = None,
        image_url: Optional[str] = None,
        image_base64: Optional[str] = None,
        prompt: str = "Describe this image in detail."
    ) -> Dict[str, Any]:
        """
        Analyze an image using Vision API.
        
        Args:
            image_path: Local path to image
            image_url: URL of image
            image_base64: Base64 encoded image
            prompt: Analysis prompt
            
        Returns:
            Analysis result with description and metadata
        """
        # Encode image to base64 if path provided
        if image_path:
            image_base64 = self._encode_image(image_path)
        
        if not image_base64 and not image_url:
            raise ValueError("Must provide image_path, image_url, or image_base64")
        
        try:
            client = self._get_client()
            
            if client.provider == LLMProvider.OPENAI:
                return await self._analyze_with_openai(image_base64, image_url, prompt)
            else:
                return await self._analyze_with_anthropic(image_base64, image_url, prompt)
                
        except Exception as e:
            logger.error("image_analysis_failed", error=str(e))
            return {
                "description": "Unable to analyze image",
                "error": str(e),
                "success": False
            }
    
    def _encode_image(self, image_path: str) -> str:
        """Encode image file to base64"""
        path = Path(image_path)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {image_path}")
        
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode("utf-8")
    
    async def _analyze_with_openai(
        self,
        image_base64: Optional[str],
        image_url: Optional[str],
        prompt: str
    ) -> Dict[str, Any]:
        """Analyze with OpenAI GPT-4 Vision"""
        from openai import AsyncOpenAI
        
        client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Build image content
        if image_url:
            image_content = {"type": "image_url", "image_url": {"url": image_url}}
        else:
            image_content = {
                "type": "image_url",
                "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}
            }
        
        response = await client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        image_content
                    ]
                }
            ],
            max_tokens=1000
        )
        
        return {
            "description": response.choices[0].message.content,
            "model": "gpt-4-vision-preview",
            "success": True,
            "usage": {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens
            }
        }
    
    async def _analyze_with_anthropic(
        self,
        image_base64: Optional[str],
        image_url: Optional[str],
        prompt: str
    ) -> Dict[str, Any]:
        """Analyze with Anthropic Claude Vision"""
        from anthropic import AsyncAnthropic
        
        client = AsyncAnthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        
        # Fetch image if URL provided
        if image_url and not image_base64:
            async with aiohttp.ClientSession() as session:
                async with session.get(image_url) as resp:
                    image_base64 = base64.b64encode(await resp.read()).decode()
        
        response = await client.messages.create(
            model="claude-3-sonnet-20240229",
            max_tokens=1000,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/jpeg",
                                "data": image_base64
                            }
                        },
                        {"type": "text", "text": prompt}
                    ]
                }
            ]
        )
        
        return {
            "description": response.content[0].text,
            "model": "claude-3-sonnet",
            "success": True,
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens
            }
        }
    
    async def extract_data_from_chart(
        self,
        image_path: Optional[str] = None,
        image_url: Optional[str] = None,
        image_base64: Optional[str] = None
    ) -> Dict[str, Any]:
        """Extract data points from a chart/graph image"""
        prompt = """Analyze this chart/graph and extract:
1. Chart type (bar, line, scatter, pie, etc.)
2. Title and axis labels
3. Data series and their approximate values
4. Key trends or insights

Respond in JSON format:
{
    "chart_type": "...",
    "title": "...",
    "x_axis_label": "...",
    "y_axis_label": "...",
    "data_series": [...],
    "insights": [...]
}"""
        
        result = await self.analyze_image(
            image_path=image_path,
            image_url=image_url,
            image_base64=image_base64,
            prompt=prompt
        )
        
        return result


class TimeSeriesProcessor:
    """
    Process time-series data with specialized handling.
    """
    
    def __init__(self):
        self.supported_formats = ['.csv', '.parquet', '.json']
    
    async def analyze_time_series(
        self,
        data: Any,
        time_column: str = "timestamp",
        value_columns: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Analyze time-series data.
        
        Returns statistics, trends, and anomalies.
        """
        import pandas as pd
        import numpy as np
        
        if isinstance(data, dict):
            df = pd.DataFrame(data)
        elif isinstance(data, pd.DataFrame):
            df = data
        else:
            raise ValueError("Data must be DataFrame or dict")
        
        # Ensure datetime index
        if time_column in df.columns:
            df[time_column] = pd.to_datetime(df[time_column])
            df = df.set_index(time_column)
        
        # Select value columns
        if value_columns:
            df = df[value_columns]
        else:
            df = df.select_dtypes(include=[np.number])
        
        analysis = {
            "statistics": {},
            "trends": {},
            "seasonality": {},
            "anomalies": []
        }
        
        for col in df.columns:
            series = df[col].dropna()
            
            # Basic statistics
            analysis["statistics"][col] = {
                "mean": float(series.mean()),
                "std": float(series.std()),
                "min": float(series.min()),
                "max": float(series.max()),
                "trend": self._detect_trend(series)
            }
            
            # Detect anomalies (simple z-score method)
            z_scores = np.abs((series - series.mean()) / series.std())
            anomaly_indices = z_scores[z_scores > 3].index.tolist()
            
            if anomaly_indices:
                analysis["anomalies"].extend([
                    {"column": col, "timestamp": str(idx), "value": float(series[idx])}
                    for idx in anomaly_indices[:5]  # Limit to 5
                ])
        
        return analysis
    
    def _detect_trend(self, series) -> str:
        """Simple trend detection"""
        import numpy as np
        
        if len(series) < 2:
            return "insufficient_data"
        
        x = np.arange(len(series))
        slope, _ = np.polyfit(x, series.values, 1)
        
        if slope > 0.01 * series.mean():
            return "increasing"
        elif slope < -0.01 * series.mean():
            return "decreasing"
        else:
            return "stable"


class CrossModalFusion:
    """
    Combine insights from multiple modalities.
    """
    
    def __init__(self):
        self.image_analyzer = ImageAnalyzer()
        self.time_series_processor = TimeSeriesProcessor()
    
    async def fuse_modalities(
        self,
        data: List[MultiModalData],
        research_context: str
    ) -> Dict[str, Any]:
        """
        Fuse insights from multiple modalities.
        
        Args:
            data: List of MultiModalData objects
            research_context: Research topic for context
            
        Returns:
            Unified analysis combining all modalities
        """
        results = {
            "modalities_processed": [],
            "individual_analyses": {},
            "unified_insights": [],
            "cross_modal_correlations": []
        }
        
        for item in data:
            results["modalities_processed"].append(item.modality.value)
            
            if item.modality == ModalityType.IMAGE:
                analysis = await self.image_analyzer.analyze_image(
                    image_base64=item.content if isinstance(item.content, str) else None,
                    prompt=f"Analyze this image in the context of: {research_context}"
                )
                results["individual_analyses"]["image"] = analysis
                
            elif item.modality == ModalityType.TIME_SERIES:
                analysis = await self.time_series_processor.analyze_time_series(item.content)
                results["individual_analyses"]["time_series"] = analysis
                
            elif item.modality == ModalityType.TABULAR:
                # Basic tabular analysis
                results["individual_analyses"]["tabular"] = {
                    "shape": item.content.shape if hasattr(item.content, 'shape') else None,
                    "columns": list(item.content.columns) if hasattr(item.content, 'columns') else None
                }
        
        # Generate unified insights
        results["unified_insights"] = self._generate_unified_insights(
            results["individual_analyses"],
            research_context
        )
        
        return results
    
    def _generate_unified_insights(
        self,
        analyses: Dict[str, Any],
        context: str
    ) -> List[str]:
        """Generate insights from combined analyses"""
        insights = []
        
        if "image" in analyses and analyses["image"].get("success"):
            insights.append(f"Visual analysis: {analyses['image'].get('description', '')[:200]}")
        
        if "time_series" in analyses:
            ts = analyses["time_series"]
            if ts.get("statistics"):
                for col, stats in ts["statistics"].items():
                    insights.append(f"Time series '{col}' shows {stats.get('trend', 'unknown')} trend")
            if ts.get("anomalies"):
                insights.append(f"Detected {len(ts['anomalies'])} anomalies in time series data")
        
        return insights


# Convenience functions
async def analyze_research_image(image_path: str, context: str = "") -> Dict[str, Any]:
    """Quick helper to analyze research-related images"""
    analyzer = ImageAnalyzer()
    prompt = f"Analyze this research image. Context: {context}" if context else "Analyze this research image in detail."
    return await analyzer.analyze_image(image_path=image_path, prompt=prompt)


async def process_multimodal_research(
    data: List[MultiModalData],
    topic: str
) -> Dict[str, Any]:
    """Process multi-modal research data"""
    fusion = CrossModalFusion()
    return await fusion.fuse_modalities(data, topic)
