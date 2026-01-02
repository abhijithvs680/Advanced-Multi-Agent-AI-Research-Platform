#!/usr/bin/env python3
"""
Main script to run research workflow
"""
import asyncio
import argparse
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from shared.config import SystemConfig
from shared.logger import setup_logging, get_logger
from orchestration.decision_engine import DecisionEngine


async def main():
    parser = argparse.ArgumentParser(description="Run Multi-Agent Research Assistant")
    parser.add_argument("--config", type=str, default="config/config.yaml",
                       help="Path to configuration file")
    parser.add_argument("--topic", type=str, required=True,
                       help="Research topic")
    parser.add_argument("--domain", type=str, default="general",
                       help="Research domain")
    parser.add_argument("--max-iterations", type=int, default=5,
                       help="Maximum feedback iterations")
    
    args = parser.parse_args()
    
    # Load configuration
    config = SystemConfig.load_from_yaml(args.config)
    
    # Setup logging
    setup_logging(config.logging.get('level', 'INFO'))
    logger = get_logger("main")
    
    logger.info("starting_workflow", topic=args.topic, domain=args.domain)
    
    # Initialize decision engine
    engine = DecisionEngine(config.__dict__)
    
    # Execute workflow
    result = await engine.execute_workflow(
        topic=args.topic,
        domain=args.domain,
        max_iterations=args.max_iterations
    )
    
    # Print results
    logger.info("workflow_completed", 
                status=result['status'],
                iterations=result.get('iterations', 0))
    
    print("\n" + "="*80)
    print("WORKFLOW RESULTS")
    print("="*80)
    print(f"Status: {result['status']}")
    print(f"Workflow ID: {result['workflow_id']}")
    
    if result['status'] == 'COMPLETED':
        print(f"\nBest Model: {result.get('best_model', {}).get('model_type', 'N/A')}")
        print(f"Score: {result.get('best_model', {}).get('score', 0.0):.4f}")
        print(f"Iterations: {result.get('iterations', 0)}")
    
    print("="*80)


if __name__ == "__main__":
    asyncio.run(main())
