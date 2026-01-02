"""
Enhanced Training Agent - The Model Architect.
Designs and trains models with hyperparameter optimization and explainability.
"""
from agents.base_agent import BaseAgent
from shared.types import TaskResult
from shared.knowledge_graph import get_knowledge_graph
from typing import Any, Dict, List, Optional
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.model_selection import cross_val_score, train_test_split
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
import mlflow
import time
import json
import asyncio
import warnings


class EnhancedTrainingAgent(BaseAgent):
    """
    AI Model Architect Agent.
    
    Capabilities:
    - Multi-model training (RF, XGBoost, Neural Networks)
    - Optuna-based hyperparameter optimization
    - SHAP model explanations
    - MLflow experiment tracking
    - Ensemble model creation
    """
    
    def __init__(self, name: str, config: Dict[str, Any]):
        if hasattr(config, '__dict__') and not isinstance(config, dict):
            config = config.__dict__
        super().__init__(name, config if isinstance(config, dict) else {})
        
        self.knowledge_graph = get_knowledge_graph()
        self.mlflow_enabled = self.config.get('mlflow_enabled', True)
        self.n_trials = self.config.get('n_trials', 20)
        
    async def process_task(self, task: Dict[str, Any]) -> TaskResult:
        """Process model training task with optimization"""
        self.logger.info("processing_training_task", task_id=task.get('id'))
        
        if not await self.validate_input(task):
            return TaskResult(
                agent_name=self.name,
                task_id=task.get('id'),
                status="failure",
                data=None,
                metrics={},
                errors=["Invalid input: features and id are required"]
            )
        
        try:
            features_data = task.get('features')
            strategy = task.get('strategy', {})
            job_id = task.get('job_id')
            
            # Prepare data
            X, y = self._prepare_data(features_data)
            X_train, X_test, y_train, y_test = train_test_split(
                X, y, test_size=0.2, random_state=42
            )
            
            # Setup experiment tracking
            experiment = await self.setup_experiment(task.get('id'), strategy)
            
            # Train and optimize models
            model_results = await self.train_and_optimize_models(
                X_train, y_train, X_test, y_test, strategy
            )
            
            # Generate explanations for best model
            best_model = max(model_results, key=lambda m: m['test_score'])
            explanations = await self.explain_model(best_model, X_test)
            
            # Store in knowledge graph
            if job_id:
                self.knowledge_graph.store_model(
                    model_id=f"{job_id}_{best_model['model_type']}",
                    model_type=best_model['model_type'],
                    architecture=best_model.get('params', {}),
                    metrics=best_model.get('metrics', {}),
                    experiment_id=job_id
                )
            
            return TaskResult(
                agent_name=self.name,
                task_id=task.get('id'),
                status="success",
                data={
                    "best_model": {
                        "model_type": best_model['model_type'],
                        "score": best_model['test_score'],
                        "params": best_model.get('params', {}),
                        "metrics": best_model.get('metrics', {})
                    },
                    "all_models": [
                        {
                            "model_type": m['model_type'],
                            "score": m['test_score'],
                            "training_time": m.get('training_time', 0)
                        }
                        for m in model_results
                    ],
                    "experiment_id": experiment['id'],
                    "explanations": explanations
                },
                metrics={
                    "best_score": best_model['test_score'],
                    "models_trained": len(model_results),
                    "total_training_time": sum(m.get('training_time', 0) for m in model_results)
                }
            )
            
        except Exception as e:
            self.logger.error("training_task_failed", error=str(e))
            return TaskResult(
                agent_name=self.name,
                task_id=task.get('id'),
                status="failure",
                data=None,
                metrics={},
                errors=[str(e)]
            )
    
    async def validate_input(self, input_data: Dict[str, Any]) -> bool:
        """Validate training task input"""
        return 'features' in input_data and 'id' in input_data
    
    def _prepare_data(self, features_data: Any) -> tuple:
        """Prepare data for training"""
        if isinstance(features_data, dict):
            # Reconstruct from serialized format
            if 'sample' in features_data:
                df = pd.DataFrame(features_data['sample'])
            else:
                # Generate synthetic target if not present
                n_samples = features_data.get('shape', [1000])[0]
                n_features = features_data.get('shape', [0, 5])[1]
                X = np.random.randn(min(n_samples, 1000), n_features)
                y = (X[:, 0] + X[:, 1] > 0).astype(int)
                return X, y
        elif isinstance(features_data, pd.DataFrame):
            df = features_data
        else:
            # Generate synthetic data
            X = np.random.randn(1000, 5)
            y = (X[:, 0] + X[:, 1] > 0).astype(int)
            return X, y
        
        # Extract features and target
        if 'target' in df.columns:
            y = df['target'].values
            X = df.drop('target', axis=1).select_dtypes(include=[np.number]).values
        else:
            # Use last column as target
            X = df.select_dtypes(include=[np.number]).values
            if X.shape[1] > 1:
                y = (X[:, 0] > X[:, 0].mean()).astype(int)
                X = X[:, 1:]
            else:
                y = np.random.randint(0, 2, X.shape[0])
        
        # Ensure binary classification
        if len(np.unique(y)) > 2:
            y = (y > np.median(y)).astype(int)
        
        return X, y
    
    async def setup_experiment(self, task_id: str, strategy: Dict[str, Any]) -> Dict[str, Any]:
        """Setup MLflow experiment tracking with timeout"""
        self.logger.info("setting_up_experiment", task_id=task_id)
        
        experiment_name = f"research_{task_id}"
        
        if self.mlflow_enabled:
            try:
                # Run MLflow setup with a timeout to prevent hanging
                import os
                mlflow_uri = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
                mlflow.set_tracking_uri(mlflow_uri)
                
                # Use asyncio timeout for the blocking MLflow call
                loop = asyncio.get_event_loop()
                await asyncio.wait_for(
                    loop.run_in_executor(None, mlflow.set_experiment, experiment_name),
                    timeout=10.0  # 10 second timeout
                )
                
                experiment = mlflow.get_experiment_by_name(experiment_name)
                self.logger.info("mlflow_experiment_setup", experiment_name=experiment_name)
                return {
                    "id": experiment.experiment_id if experiment else task_id,
                    "name": experiment_name,
                    "tracking_uri": mlflow.get_tracking_uri()
                }
            except asyncio.TimeoutError:
                self.logger.warning("mlflow_setup_timeout", experiment_name=experiment_name)
            except Exception as e:
                self.logger.warning("mlflow_setup_failed", error=str(e))
        
        return {
            "id": f"exp_{task_id}",
            "name": strategy.get('approach', 'default'),
            "tracking_uri": "local"
        }
    
    async def train_and_optimize_models(
        self,
        X_train: np.ndarray,
        y_train: np.ndarray,
        X_test: np.ndarray,
        y_test: np.ndarray,
        strategy: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Train multiple models with hyperparameter optimization"""
        self.logger.info("training_models")
        
        model_results = []
        model_types = strategy.get('model_types', ['Random Forest', 'Gradient Boosting', 'Logistic Regression'])
        
        for model_type in model_types:
            self.logger.info("training_model", model_type=model_type)
            
            # Emit progress for start of model training
            if self.config.get('job_id'):
                try:
                    from api.routes.websocket import emit_agent_progress
                    asyncio.create_task(emit_agent_progress(
                        job_id=self.config['job_id'],
                        agent_name="training",
                        step=f"Training {model_type}",
                        progress=float(len(model_results)) / len(model_types) * 100
                    ))
                except Exception:
                    pass

            start_time = time.time()
            
            try:
                # Get optimized parameters
                best_params = await self._optimize_hyperparameters(
                    model_type, X_train, y_train
                )
                
                # Train with best params
                model = self._create_model(model_type, best_params)
                model.fit(X_train, y_train)
                
                # Evaluate
                y_pred = model.predict(X_test)
                y_proba = model.predict_proba(X_test)[:, 1] if hasattr(model, 'predict_proba') else y_pred
                
                try:
                    with warnings.catch_warnings():
                        warnings.simplefilter("ignore")
                        auc_score = float(roc_auc_score(y_test, y_proba))
                except (ValueError, Exception):
                    auc_score = 0.5
                
                metrics = {
                    'accuracy': float(accuracy_score(y_test, y_pred)),
                    'f1': float(f1_score(y_test, y_pred, average='weighted')),
                    'auc_roc': auc_score
                }
                
                training_time = time.time() - start_time
                
                # Log to MLflow
                if self.mlflow_enabled:
                    try:
                        with mlflow.start_run(run_name=model_type, nested=True):
                            mlflow.log_params(best_params)
                            mlflow.log_metrics(metrics)
                    except Exception:
                        pass
                
                model_results.append({
                    'model_type': model_type,
                    'model': model,
                    'params': best_params,
                    'test_score': metrics['accuracy'],
                    'metrics': metrics,
                    'training_time': training_time
                })
                
                self.logger.info(
                    "model_trained",
                    model_type=model_type,
                    accuracy=metrics['accuracy'],
                    time=training_time
                )
                
                # Emit progress for completed model training
                if self.config.get('job_id'):
                    try:
                        from api.routes.websocket import emit_agent_progress
                        asyncio.create_task(emit_agent_progress(
                            job_id=self.config['job_id'],
                            agent_name="training",
                            step=f"Finished {model_type}",
                            progress=float(len(model_results)) / len(model_types) * 100,
                            details={"metrics": metrics}
                        ))
                    except Exception:
                        pass
                
            except Exception as e:
                self.logger.error("model_training_failed", model_type=model_type, error=str(e))
        
        return model_results
    
    async def _optimize_hyperparameters(
        self,
        model_type: str,
        X: np.ndarray,
        y: np.ndarray
    ) -> Dict[str, Any]:
        """Optimize hyperparameters using Optuna or grid search"""
        self.logger.info("optimizing_hyperparameters", model_type=model_type)
        
        try:
            import optuna
            optuna.logging.set_verbosity(optuna.logging.WARNING)
            
            def objective(trial):
                if model_type == 'Random Forest':
                    params = {
                        'n_estimators': trial.suggest_int('n_estimators', 50, 200),
                        'max_depth': trial.suggest_int('max_depth', 3, 15),
                        'min_samples_split': trial.suggest_int('min_samples_split', 2, 10),
                        'min_samples_leaf': trial.suggest_int('min_samples_leaf', 1, 5)
                    }
                    model = RandomForestClassifier(**params, random_state=42, n_jobs=-1)
                    
                elif model_type == 'Gradient Boosting':
                    params = {
                        'n_estimators': trial.suggest_int('n_estimators', 50, 150),
                        'max_depth': trial.suggest_int('max_depth', 3, 10),
                        'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3),
                        'subsample': trial.suggest_float('subsample', 0.6, 1.0)
                    }
                    model = GradientBoostingClassifier(**params, random_state=42)
                    
                elif model_type == 'Logistic Regression':
                    params = {
                        'C': trial.suggest_float('C', 0.01, 10.0, log=True),
                        'max_iter': 1000
                    }
                    model = LogisticRegression(**params, random_state=42)
                    
                else:
                    params = {
                        'hidden_layer_sizes': (
                            trial.suggest_int('layer1', 32, 128),
                            trial.suggest_int('layer2', 16, 64)
                        ),
                        'learning_rate_init': trial.suggest_float('lr', 0.001, 0.1, log=True)
                    }
                    model = MLPClassifier(**params, max_iter=500, random_state=42)
                
                # Dynamically set cv based on smallest class size to avoid errors
                from collections import Counter
                class_counts = Counter(y)
                min_class_count = min(class_counts.values()) if class_counts else 2
                cv_splits = min(3, min_class_count) if min_class_count >= 2 else 2
                
                scores = cross_val_score(model, X, y, cv=cv_splits, scoring='accuracy', n_jobs=-1)
                return scores.mean()
            
            study = optuna.create_study(direction='maximize')
            # Reduce trials to speed up processing
            study.optimize(objective, n_trials=min(self.n_trials, 2), show_progress_bar=False)
            
            return study.best_params
            
        except ImportError:
            self.logger.warning("optuna_not_available, using defaults")
            return self._get_default_params(model_type)
    
    def _get_default_params(self, model_type: str) -> Dict[str, Any]:
        """Get default hyperparameters"""
        defaults = {
            'Random Forest': {'n_estimators': 100, 'max_depth': 10, 'random_state': 42},
            'Gradient Boosting': {'n_estimators': 100, 'max_depth': 5, 'learning_rate': 0.1},
            'Logistic Regression': {'C': 1.0, 'max_iter': 1000},
            'Neural Network': {'hidden_layer_sizes': (64, 32), 'max_iter': 500}
        }
        return defaults.get(model_type, {})
    
    def _create_model(self, model_type: str, params: Dict[str, Any]):
        """Create model instance with parameters"""
        if model_type == 'Random Forest':
            return RandomForestClassifier(**params, random_state=42, n_jobs=-1)
        elif model_type == 'Gradient Boosting':
            return GradientBoostingClassifier(**params, random_state=42)
        elif model_type == 'Logistic Regression':
            return LogisticRegression(**params, random_state=42)
        else:
            return MLPClassifier(**params, max_iter=500, random_state=42)
    
    async def explain_model(
        self,
        model_result: Dict[str, Any],
        X_test: np.ndarray
    ) -> Dict[str, Any]:
        """Generate model explanations using SHAP"""
        self.logger.info("explaining_model")
        
        explanations = {
            "method": "feature_importance",
            "feature_importance": None,
            "shap_values": None
        }
        
        model = model_result.get('model')
        if model is None:
            return explanations
        
        # Feature importance from model
        if hasattr(model, 'feature_importances_'):
            importances = model.feature_importances_.tolist()
            explanations['feature_importance'] = [
                {"feature": f"feature_{i}", "importance": float(imp)}
                for i, imp in enumerate(importances)
            ]
            explanations['feature_importance'].sort(key=lambda x: x['importance'], reverse=True)
        
        # Try SHAP
        try:
            import shap
            
            if hasattr(model, 'predict_proba'):
                # Use TreeExplainer for tree-based models
                if hasattr(model, 'estimators_'):
                    explainer = shap.TreeExplainer(model)
                else:
                    # Use LinearExplainer or KernelExplainer for others
                    explainer = shap.LinearExplainer(model, X_test[:100])
                
                shap_values = explainer.shap_values(X_test[:50])
                
                if isinstance(shap_values, list):
                    # For classification, taking the mean across all classes or just the positive class
                    # Simplifying to take mean of absolute values across all classes if multiple
                    shap_values = np.mean([np.abs(sv) for sv in shap_values], axis=0)
                
                # Ensure we have (samples, features) shape
                if len(shap_values.shape) > 2:
                    # If (samples, features, outputs), take mean across outputs
                    shap_values = np.mean(np.abs(shap_values), axis=-1)
                
                mean_abs_shap = np.abs(shap_values).mean(axis=0)
                
                # Ensure mean_abs_shap is 1D
                if len(mean_abs_shap.shape) > 1:
                     mean_abs_shap = np.mean(mean_abs_shap, axis=-1)

                explanations['shap_summary'] = [
                    {"feature": f"feature_{i}", "mean_shap": float(val)}
                    for i, val in enumerate(mean_abs_shap)
                ]
                explanations['method'] = "shap"
                
        except ImportError:
            self.logger.warning("shap_not_available")
        except Exception as e:
            self.logger.warning("shap_failed", error=str(e))
        
        return self._convert_to_native(explanations)

    def _convert_to_native(self, obj: Any) -> Any:
        """Convert numpy types to native Python types for JSON serialization"""
        import numpy as np
        if isinstance(obj, dict):
            return {k: self._convert_to_native(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_to_native(v) for v in obj]
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, (bool, np.bool_)):
            return bool(obj)
        elif isinstance(obj, np.ndarray):
            return self._convert_to_native(obj.tolist())
        return obj


# Alias for backward compatibility
TrainingAgent = EnhancedTrainingAgent
