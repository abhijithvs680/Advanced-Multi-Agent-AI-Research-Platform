from dataclasses import dataclass, field
from typing import Optional, Dict, Any
import yaml
from pathlib import Path


@dataclass
class AgentConfig:
    """Configuration for individual agents"""
    name: str
    type: str
    max_retries: int = 3
    timeout: int = 300
    llm_model: str = "gpt-4"
    temperature: float = 0.7
    # Optional agent-specific settings
    cache_enabled: bool = False
    gpu_enabled: bool = False
    extra: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        # Handle any extra kwargs that weren't explicitly defined
        pass


@dataclass
class SystemConfig:
    """Main system configuration"""
    agents: Dict[str, AgentConfig]
    orchestration: Dict[str, Any]
    storage: Dict[str, Any]
    logging: Dict[str, Any]
    
    @classmethod
    def load_from_yaml(cls, config_path: str) -> 'SystemConfig':
        """Load configuration from YAML file"""
        with open(config_path, 'r') as f:
            config_dict = yaml.safe_load(f)
        
        # Parse agent configs - filter known fields and put rest in extra
        agents = {}
        known_fields = {'name', 'type', 'max_retries', 'timeout', 'llm_model', 
                       'temperature', 'cache_enabled', 'gpu_enabled'}
        
        for name, agent_config in config_dict.get('agents', {}).items():
            # Separate known and extra fields
            known = {k: v for k, v in agent_config.items() if k in known_fields}
            extra = {k: v for k, v in agent_config.items() if k not in known_fields}
            known['extra'] = extra
            agents[name] = AgentConfig(**known)
        
        return cls(
            agents=agents,
            orchestration=config_dict.get('orchestration', {}),
            storage=config_dict.get('storage', {}),
            logging=config_dict.get('logging', {})
        )
