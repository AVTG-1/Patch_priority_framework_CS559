"""
Game Engine Module

Implements the game-theoretic simulation engine for patch prioritization.

This module consumes exports from Developer A's data_model and performs:
- Strategy enumeration
- Nash equilibrium computation
- Multi-round simulation
- Results export back to Developer A

Developer: Developer B
API Version: 1.0.0
"""

__version__ = "1.0.0"
__api_version__ = "1.0.0"

from .game_state import GameState
from .strategy import (
    StrategySet,
    enumerate_defender_strategies,
    enumerate_attacker_strategies,
    create_strategy_set,
    filter_dominated_strategies,
    get_strategy_cost,
    get_strategy_description
)
from .nash_solver import NashSolver
from .simulator import Simulator
from .simulation_result import SimulationResult

__all__ = [
    # Version info
    "__version__",
    "__api_version__",
    
    # Core classes
    "GameState",
    "StrategySet",
    "NashSolver",
    "Simulator",
    "SimulationResult",
    
    # Strategy functions
    "enumerate_defender_strategies",
    "enumerate_attacker_strategies",
    "create_strategy_set",
    "filter_dominated_strategies",
    "get_strategy_cost",
    "get_strategy_description",
]
