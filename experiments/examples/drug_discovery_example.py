#!/usr/bin/env python3
"""
Example: Drug discovery workflow using the multi-agent system.
"""
import asyncio
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from orchestration.decision_engine import DecisionEngine
from shared.config import SystemConfig
from shared.logger import setup_logging, get_logger


async def run_drug_discovery():
    """Run a drug discovery research workflow"""
    
    # Setup logging
    setup_logging("INFO")
    logger = get_logger("drug_discovery_example")
    
    # Load config or use defaults
    try:
        config = SystemConfig.load_from_yaml("config/config.yaml")
    except Exception:
        # Use default config
        config_dict = {
            "agents": {
                "research": {},
                "data": {},
                "training": {},
                "evaluation": {}
            },
            "orchestration": {"max_iterations": 3},
            "storage": {},
            "logging": {"level": "INFO"}
        }
        from dataclasses import dataclass
        
        @dataclass
        class MockConfig:
            agents: dict
            orchestration: dict
            storage: dict
            logging: dict
        
        config = MockConfig(**config_dict)
    
    logger.info("Starting drug discovery workflow")
    
    # Initialize engine
    engine = DecisionEngine(config.__dict__)
    
    # Execute workflow
    result = await engine.execute_workflow(
        topic="novel antibiotics for MRSA",
        domain="pharmaceutical",
        max_iterations=3
    )
    
    # Print results
    print("\n" + "="*80)
    print("DRUG DISCOVERY WORKFLOW RESULTS")
    print("="*80)
    print(f"\nWorkflow ID: {result['workflow_id']}")
    print(f"Status: {result['status']}")
    
    if result['status'] == 'completed':
        print(f"\n📊 Results Summary:")
        print(f"  - Iterations: {result.get('iterations', 0)}")
        
        best_model = result.get('best_model')
        if best_model:
            print(f"  - Best Model: {best_model.get('model_type', 'N/A')}")
            print(f"  - Score: {best_model.get('score', 0.0):.4f}")
        
        print(f"\n📈 State Transitions:")
        for transition in result.get('state_history', []):
            print(f"  - {transition['from']} → {transition['to']}")
        
        print(f"\n✅ Drug discovery analysis complete!")
    
    elif result['status'] == 'escalated':
        print(f"\n⚠️ Workflow requires human review")
        print(f"Reason: {result.get('reason', 'Unknown')}")
    
    else:
        print(f"\n❌ Workflow failed")
        print(f"Reason: {result.get('reason', 'Unknown')}")
    
    print("="*80)
    
    return result


if __name__ == "__main__":
    asyncio.run(run_drug_discovery())
