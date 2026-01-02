"""
Plugin System - Extensible architecture for custom agents and tools.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Type
from dataclasses import dataclass
from pathlib import Path
import importlib.util
import inspect

from shared.logger import get_logger
from shared.types import TaskResult

logger = get_logger(__name__)


@dataclass
class PluginInfo:
    """Plugin metadata"""
    name: str
    version: str
    description: str
    author: str
    plugin_type: str  # "agent", "tool", "exporter"


class PluginInterface(ABC):
    """Base interface for all plugins"""
    
    @classmethod
    @abstractmethod
    def get_info(cls) -> PluginInfo:
        """Return plugin metadata"""
        pass
    
    @abstractmethod
    async def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize plugin with configuration"""
        pass
    
    @abstractmethod
    async def shutdown(self) -> None:
        """Cleanup when plugin is unloaded"""
        pass


class AgentPlugin(PluginInterface):
    """Base class for agent plugins"""
    
    @abstractmethod
    async def process_task(self, task: Dict[str, Any]) -> TaskResult:
        """Process a task"""
        pass


class ToolPlugin(PluginInterface):
    """Base class for tool plugins"""
    
    @abstractmethod
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the tool"""
        pass
    
    @classmethod
    @abstractmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Return JSON schema for tool parameters"""
        pass


class ExporterPlugin(PluginInterface):
    """Base class for export format plugins"""
    
    @abstractmethod
    async def export(self, data: Dict[str, Any]) -> bytes:
        """Export data to format"""
        pass
    
    @classmethod
    @abstractmethod
    def get_format(cls) -> str:
        """Return export format name"""
        pass
    
    @classmethod
    @abstractmethod
    def get_mime_type(cls) -> str:
        """Return MIME type"""
        pass


class PluginManager:
    """
    Manages plugin lifecycle and discovery.
    
    Features:
    - Dynamic plugin loading
    - Plugin registration
    - Type-safe plugin access
    - Configuration injection
    """
    
    def __init__(self, plugins_dir: str = "plugins"):
        self.plugins_dir = Path(plugins_dir)
        self._agents: Dict[str, Type[AgentPlugin]] = {}
        self._tools: Dict[str, Type[ToolPlugin]] = {}
        self._exporters: Dict[str, Type[ExporterPlugin]] = {}
        self._instances: Dict[str, PluginInterface] = {}
    
    async def discover_plugins(self) -> Dict[str, List[PluginInfo]]:
        """Discover all plugins in plugins directory"""
        discovered = {
            "agents": [],
            "tools": [],
            "exporters": []
        }
        
        if not self.plugins_dir.exists():
            self.plugins_dir.mkdir(parents=True, exist_ok=True)
            logger.info("plugins_dir_created", path=str(self.plugins_dir))
            return discovered
        
        # Scan for Python files
        for py_file in self.plugins_dir.glob("**/*.py"):
            if py_file.name.startswith("_"):
                continue
            
            try:
                plugins = self._load_plugins_from_file(py_file)
                for plugin_type, plugin_class in plugins:
                    info = plugin_class.get_info()
                    discovered[f"{plugin_type}s"].append(info)
                    
                    if plugin_type == "agent":
                        self._agents[info.name] = plugin_class
                    elif plugin_type == "tool":
                        self._tools[info.name] = plugin_class
                    elif plugin_type == "exporter":
                        self._exporters[info.name] = plugin_class
                    
                    logger.info("plugin_discovered", name=info.name, type=plugin_type)
                    
            except Exception as e:
                logger.error("plugin_load_failed", file=str(py_file), error=str(e))
        
        return discovered
    
    def _load_plugins_from_file(self, file_path: Path) -> List[tuple]:
        """Load plugin classes from a Python file"""
        plugins = []
        
        spec = importlib.util.spec_from_file_location(file_path.stem, file_path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if obj.__module__ != module.__name__:
                continue  # Skip imported classes
            
            if issubclass(obj, AgentPlugin) and obj != AgentPlugin:
                plugins.append(("agent", obj))
            elif issubclass(obj, ToolPlugin) and obj != ToolPlugin:
                plugins.append(("tool", obj))
            elif issubclass(obj, ExporterPlugin) and obj != ExporterPlugin:
                plugins.append(("exporter", obj))
        
        return plugins
    
    def register_agent(self, name: str, agent_class: Type[AgentPlugin]) -> None:
        """Manually register an agent plugin"""
        self._agents[name] = agent_class
        logger.info("agent_registered", name=name)
    
    def register_tool(self, name: str, tool_class: Type[ToolPlugin]) -> None:
        """Manually register a tool plugin"""
        self._tools[name] = tool_class
        logger.info("tool_registered", name=name)
    
    def register_exporter(self, name: str, exporter_class: Type[ExporterPlugin]) -> None:
        """Manually register an exporter plugin"""
        self._exporters[name] = exporter_class
        logger.info("exporter_registered", name=name)
    
    async def get_agent(self, name: str, config: Optional[Dict[str, Any]] = None) -> Optional[AgentPlugin]:
        """Get an initialized agent plugin instance"""
        if name not in self._agents:
            return None
        
        instance_key = f"agent_{name}"
        if instance_key not in self._instances:
            instance = self._agents[name]()
            await instance.initialize(config or {})
            self._instances[instance_key] = instance
        
        return self._instances[instance_key]
    
    async def get_tool(self, name: str, config: Optional[Dict[str, Any]] = None) -> Optional[ToolPlugin]:
        """Get an initialized tool plugin instance"""
        if name not in self._tools:
            return None
        
        instance_key = f"tool_{name}"
        if instance_key not in self._instances:
            instance = self._tools[name]()
            await instance.initialize(config or {})
            self._instances[instance_key] = instance
        
        return self._instances[instance_key]
    
    async def get_exporter(self, format_name: str) -> Optional[ExporterPlugin]:
        """Get an exporter by format name"""
        for name, cls in self._exporters.items():
            if cls.get_format() == format_name:
                instance_key = f"exporter_{name}"
                if instance_key not in self._instances:
                    instance = cls()
                    await instance.initialize({})
                    self._instances[instance_key] = instance
                return self._instances[instance_key]
        return None
    
    def list_agents(self) -> List[PluginInfo]:
        """List all registered agent plugins"""
        return [cls.get_info() for cls in self._agents.values()]
    
    def list_tools(self) -> List[PluginInfo]:
        """List all registered tool plugins"""
        return [cls.get_info() for cls in self._tools.values()]
    
    def list_exporters(self) -> List[PluginInfo]:
        """List all registered exporter plugins"""
        return [cls.get_info() for cls in self._exporters.values()]
    
    async def shutdown_all(self) -> None:
        """Shutdown all plugin instances"""
        for name, instance in self._instances.items():
            try:
                await instance.shutdown()
                logger.info("plugin_shutdown", name=name)
            except Exception as e:
                logger.error("plugin_shutdown_failed", name=name, error=str(e))
        self._instances.clear()


# Global plugin manager
_plugin_manager: Optional[PluginManager] = None


def get_plugin_manager() -> PluginManager:
    """Get or create plugin manager"""
    global _plugin_manager
    if _plugin_manager is None:
        _plugin_manager = PluginManager()
    return _plugin_manager
