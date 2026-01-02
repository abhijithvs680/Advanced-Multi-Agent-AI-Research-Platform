"""
Enhanced Data Agent - The Experimentalist.
Intelligently sources data from multiple modalities with quality reporting.
"""
from agents.base_agent import BaseAgent
from shared.types import TaskResult
from shared.llm_client import get_default_client
from shared.knowledge_graph import get_knowledge_graph
from typing import Any, Dict, List, Optional
import pandas as pd
import numpy as np
import asyncio
import json
from datetime import datetime


class EnhancedDataAgent(BaseAgent):
    """
    AI Data Scientist Agent.
    
    Capabilities:
    - Multi-source data collection (Kaggle, UCI, synthetic)
    - Advanced preprocessing with outlier detection
    - Feature engineering based on domain knowledge
    - Comprehensive data quality reports
    - Automatic data documentation
    """
    
    def __init__(self, name: str, config: Dict[str, Any]):
        if hasattr(config, '__dict__') and not isinstance(config, dict):
            config = config.__dict__
        super().__init__(name, config if isinstance(config, dict) else {})
        
        self.knowledge_graph = get_knowledge_graph()
        self.data_cache = {}
        
    async def process_task(self, task: Dict[str, Any]) -> TaskResult:
        """Process data collection and preparation task"""
        self.logger.info("processing_data_task", task_id=task.get('id'))
        
        if not await self.validate_input(task):
            return TaskResult(
                agent_name=self.name,
                task_id=task.get('id'),
                status="failure",
                data=None,
                metrics={},
                errors=["Invalid input: data_requirements and id are required"]
            )
        
        try:
            requirements = task.get('data_requirements', {})
            job_id = task.get('job_id')
            
            # Step 1: Collect data from sources
            self.logger.info("step_collect_data")
            raw_data = await self.collect_data(requirements)
            
            # Step 2: Clean data
            self.logger.info("step_clean_data")
            clean_data = await self.clean_data(raw_data)
            
            # Step 3: Engineer features
            self.logger.info("step_engineer_features")
            features = await self.engineer_features(clean_data, requirements)
            
            # Step 4: Validate quality
            self.logger.info("step_validate_quality")
            quality_report = await self.validate_quality(features)
            
            # Step 5: Generate documentation
            self.logger.info("step_generate_documentation")
            documentation = self._generate_data_documentation(features, quality_report)
            
            # Check quality threshold
            if quality_report['quality_score'] < requirements.get('quality_threshold', 0.8):
                return TaskResult(
                    agent_name=self.name,
                    task_id=task.get('id'),
                    status="partial",
                    data={
                        "features": self._dataframe_to_serializable(features),
                        "quality_report": quality_report,
                        "documentation": documentation
                    },
                    metrics=quality_report,
                    errors=["Data quality below threshold"]
                )
            
            return TaskResult(
                agent_name=self.name,
                task_id=task.get('id'),
                status="success",
                data={
                    "features": self._dataframe_to_serializable(features),
                    "quality_report": quality_report,
                    "documentation": documentation,
                    "preprocessing_pipeline": self._get_pipeline_config()
                },
                metrics={
                    "samples": len(features),
                    "features": len(features.columns) if hasattr(features, 'columns') else 0,
                    "quality_score": quality_report['quality_score']
                }
            )
            
        except Exception as e:
            self.logger.error("data_task_failed", error=str(e))
            return TaskResult(
                agent_name=self.name,
                task_id=task.get('id'),
                status="failure",
                data=None,
                metrics={},
                errors=[str(e)]
            )
    
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate data task input"""
        return 'data_requirements' in input_data and 'id' in input_data
    
    async def collect_data(self, requirements: Dict[str, Any]) -> pd.DataFrame:
        """
        Collect data from specified sources.
        Supports: Kaggle, UCI, synthetic generation.
        """
        sources = requirements.get('data_sources', ['synthetic'])
        self.logger.info("collecting_data", sources=sources)
        
        all_data = []
        
        for source in sources:
            if source.lower() == 'synthetic':
                data = await self._generate_synthetic_data(requirements)
                all_data.append(data)
            elif source.lower() == 'kaggle':
                data = await self._fetch_kaggle_data(requirements)
                if data is not None:
                    all_data.append(data)
            elif source.lower() == 'uci':
                data = await self._fetch_uci_data(requirements)
                if data is not None:
                    all_data.append(data)
        
        if not all_data:
            # Fallback to synthetic
            all_data.append(await self._generate_synthetic_data(requirements))
        
        # Combine data sources
        combined = pd.concat(all_data, ignore_index=True) if len(all_data) > 1 else all_data[0]
        
        self.logger.info("data_collected", shape=combined.shape)
        return combined
    
    async def _generate_synthetic_data(self, requirements: Dict[str, Any]) -> pd.DataFrame:
        """Generate synthetic data based on requirements"""
        n_samples = requirements.get('min_samples', 1000)
        feature_names = requirements.get('features', ['feature_1', 'feature_2', 'feature_3'])
        
        # Create realistic synthetic data with patterns
        np.random.seed(42)
        
        data = {}
        for i, name in enumerate(feature_names):
            # Add variety: some normal, some skewed, some with structure
            if i % 3 == 0:
                data[name] = np.random.normal(0, 1, n_samples)
            elif i % 3 == 1:
                data[name] = np.random.exponential(1, n_samples)
            else:
                data[name] = np.sin(np.linspace(0, 4*np.pi, n_samples)) + np.random.normal(0, 0.3, n_samples)
        
        # Add target variable with relationship to features
        df = pd.DataFrame(data)
        
        # Add some correlations
        if len(feature_names) >= 2:
            df['target'] = (
                0.5 * df[feature_names[0]] +
                0.3 * df.get(feature_names[1], 0) +
                np.random.normal(0, 0.2, n_samples)
            )
        
        self.logger.info("synthetic_data_generated", samples=n_samples)
        return df
    
    async def _fetch_kaggle_data(self, requirements: Dict[str, Any]) -> Optional[pd.DataFrame]:
        """Fetch data from Kaggle (placeholder for API integration)"""
        # TODO: Implement Kaggle API integration
        self.logger.info("kaggle_data_fetch_placeholder")
        return None
    
    async def _fetch_uci_data(self, requirements: Dict[str, Any]) -> Optional[pd.DataFrame]:
        """Fetch data from UCI ML Repository (placeholder)"""
        # TODO: Implement UCI Repository integration
        self.logger.info("uci_data_fetch_placeholder")
        return None
    
    async def clean_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Advanced data cleaning with intelligent preprocessing.
        """
        self.logger.info("cleaning_data", shape=data.shape)
        original_shape = data.shape
        
        # 1. Remove duplicates
        data = data.drop_duplicates()
        
        # 2. Handle missing values intelligently
        for col in data.columns:
            if data[col].isnull().sum() > 0:
                if data[col].dtype in ['float64', 'int64']:
                    # Use median for numeric (more robust than mean)
                    data[col] = data[col].fillna(data[col].median())
                else:
                    # Use mode for categorical
                    data[col] = data[col].fillna(data[col].mode().iloc[0] if len(data[col].mode()) > 0 else 'unknown')
        
        # 3. Remove outliers using IQR method (more robust than z-score)
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            Q1 = data[col].quantile(0.25)
            Q3 = data[col].quantile(0.75)
            IQR = Q3 - Q1
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            data = data[(data[col] >= lower_bound) & (data[col] <= upper_bound)]
        
        self.logger.info(
            "data_cleaned",
            original=original_shape,
            cleaned=data.shape,
            removed=original_shape[0] - data.shape[0]
        )
        return data
    
    async def engineer_features(
        self,
        data: pd.DataFrame,
        requirements: Dict[str, Any]
    ) -> pd.DataFrame:
        """
        Engineer features based on domain knowledge and data characteristics.
        """
        self.logger.info("engineering_features")
        
        numeric_cols = data.select_dtypes(include=[np.number]).columns.tolist()
        
        # 1. Normalize numeric features
        for col in numeric_cols:
            mean_val = data[col].mean()
            std_val = data[col].std()
            if std_val > 0:
                data[f'{col}_normalized'] = (data[col] - mean_val) / std_val
        
        # 2. Create interaction features for top correlated pairs
        if len(numeric_cols) >= 2:
            # Compute correlations and create interaction for top pairs
            correlations = data[numeric_cols].corr().abs()
            for i, col1 in enumerate(numeric_cols[:3]):
                for col2 in numeric_cols[i+1:4]:
                    if col1 != col2:
                        data[f'{col1}_x_{col2}'] = data[col1] * data[col2]
        
        # 3. Create polynomial features for important columns
        for col in numeric_cols[:3]:
            data[f'{col}_squared'] = data[col] ** 2
        
        # 4. Create binned versions
        for col in numeric_cols[:2]:
            data[f'{col}_binned'] = pd.qcut(data[col], q=5, labels=False, duplicates='drop')
        
        self.logger.info("features_engineered", total_features=len(data.columns))
        return data
    
    async def validate_quality(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Comprehensive data quality validation with statistical summaries.
        """
        self.logger.info("validating_quality")
        
        # Basic quality metrics
        missing_ratio = data.isnull().sum().sum() / (data.shape[0] * data.shape[1])
        duplicate_ratio = data.duplicated().sum() / len(data)
        
        # Feature statistics
        numeric_cols = data.select_dtypes(include=[np.number]).columns
        feature_stats = {}
        
        for col in numeric_cols[:10]:  # Limit to first 10 for performance
            feature_stats[col] = {
                "mean": float(data[col].mean()),
                "std": float(data[col].std()),
                "min": float(data[col].min()),
                "max": float(data[col].max()),
                "skewness": float(data[col].skew()),
                "kurtosis": float(data[col].kurtosis())
            }
        
        # Correlation summary
        corr_matrix = data[numeric_cols].corr()
        high_correlations = []
        for i, col1 in enumerate(numeric_cols):
            for col2 in numeric_cols[i+1:]:
                corr_val = abs(corr_matrix.loc[col1, col2])
                if corr_val > 0.7:
                    high_correlations.append({
                        "feature_1": col1,
                        "feature_2": col2,
                        "correlation": float(corr_val)
                    })
        
        # Overall quality score
        quality_score = max(0, 1.0 - (missing_ratio + duplicate_ratio * 0.5))
        
        return {
            "quality_score": float(quality_score),
            "missing_ratio": float(missing_ratio),
            "duplicate_ratio": float(duplicate_ratio),
            "n_samples": len(data),
            "n_features": len(data.columns),
            "numeric_features": len(numeric_cols),
            "feature_statistics": feature_stats,
            "high_correlations": high_correlations[:10],
            "validation_timestamp": datetime.utcnow().isoformat()
        }
    
    def _generate_data_documentation(
        self,
        data: pd.DataFrame,
        quality_report: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate automatic data documentation"""
        return {
            "dataset_info": {
                "created_at": datetime.utcnow().isoformat(),
                "n_samples": len(data),
                "n_features": len(data.columns)
            },
            "feature_dictionary": {
                col: {
                    "dtype": str(data[col].dtype),
                    "null_count": int(data[col].isnull().sum()),
                    "unique_count": int(data[col].nunique())
                }
                for col in data.columns[:20]  # Limit for large datasets
            },
            "quality_summary": {
                "score": quality_report['quality_score'],
                "issues": self._identify_quality_issues(quality_report)
            }
        }
    
    def _identify_quality_issues(self, quality_report: Dict[str, Any]) -> List[str]:
        """Identify quality issues from report"""
        issues = []
        
        if quality_report['missing_ratio'] > 0.05:
            issues.append(f"High missing data ratio: {quality_report['missing_ratio']:.2%}")
        
        if quality_report['duplicate_ratio'] > 0.01:
            issues.append(f"Duplicate records detected: {quality_report['duplicate_ratio']:.2%}")
        
        if len(quality_report.get('high_correlations', [])) > 5:
            issues.append("Multiple highly correlated features may cause multicollinearity")
        
        return issues
    
    def _get_pipeline_config(self) -> Dict[str, Any]:
        """Get preprocessing pipeline configuration for reproducibility"""
        return {
            "steps": [
                {"name": "remove_duplicates", "params": {}},
                {"name": "handle_missing", "params": {"strategy": "median"}},
                {"name": "remove_outliers", "params": {"method": "iqr", "multiplier": 1.5}},
                {"name": "normalize", "params": {"method": "z-score"}},
                {"name": "create_interactions", "params": {"top_k": 3}},
                {"name": "create_polynomials", "params": {"degree": 2}}
            ],
            "version": "1.0.0"
        }
    
    def _dataframe_to_serializable(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Convert DataFrame to serializable format"""
        return {
            "columns": list(df.columns),
            "shape": list(df.shape),
            "sample": df.head(5).to_dict(orient='records'),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()}
        }


# Alias for backward compatibility
DataAgent = EnhancedDataAgent
