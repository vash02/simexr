#!/usr/bin/env python3
"""
Simulation Code Loader Helper

This module provides utilities to load simulation code for reasoning agents.
It uses the existing database infrastructure to retrieve simulation scripts.
"""

import logging
from pathlib import Path
from typing import Optional

from db.config.database import DatabaseConfig
from db.services.store import StorageService
from db.repositories.simulation import SimulationRepository

log = logging.getLogger(__name__)


def load_simulation_code(model_id: str, db_path: Optional[str] = None) -> str:
    """
    Load simulation code for a given model ID.
    
    Args:
        model_id: The ID of the model to load code for
        db_path: Optional path to the database file
        
    Returns:
        str: The simulation code as a string
        
    Raises:
        ValueError: If the model is not found or no code is available
        Exception: For other database or file system errors
    """
    try:
        # Create database configuration
        db_config = DatabaseConfig(database_path=db_path) if db_path else DatabaseConfig()
        
        # Create repository and service
        simulation_repo = SimulationRepository(db_config)
        storage_service = StorageService(simulation_repo)
        
        # Get the simulation code
        sim_code = storage_service.get_simulation_script_code(model_id)
        
        if not sim_code or not sim_code.strip():
            log.warning(f"No simulation code found for model {model_id}")
            return ""
        
        log.info(f"Loaded simulation code for model {model_id} ({len(sim_code)} characters)")
        return sim_code
        
    except Exception as e:
        log.error(f"Failed to load simulation code for model {model_id}: {e}")
        raise


def load_simulation_code_safe(model_id: str, db_path: Optional[str] = None) -> str:
    """
    Safely load simulation code for a given model ID.
    Returns empty string if any error occurs instead of raising exceptions.
    
    Args:
        model_id: The ID of the model to load code for
        db_path: Optional path to the database file
        
    Returns:
        str: The simulation code as a string, or empty string if error occurs
    """
    try:
        return load_simulation_code(model_id, db_path)
    except Exception as e:
        log.warning(f"Could not load simulation code for model {model_id}: {e}")
        return ""


def get_simulation_metadata(model_id: str, db_path: Optional[str] = None) -> dict:
    """
    Get simulation metadata for a given model ID.
    
    Args:
        model_id: The ID of the model to get metadata for
        db_path: Optional path to the database file
        
    Returns:
        dict: The simulation metadata
        
    Raises:
        ValueError: If the model is not found
        Exception: For other database errors
    """
    try:
        # Create database configuration
        db_config = DatabaseConfig(database_path=db_path) if db_path else DatabaseConfig()
        
        # Create repository and service
        simulation_repo = SimulationRepository(db_config)
        storage_service = StorageService(simulation_repo)
        
        # Get the metadata
        metadata = storage_service.get_model_metadata(model_id)
        
        log.info(f"Loaded metadata for model {model_id}")
        return metadata
        
    except Exception as e:
        log.error(f"Failed to load metadata for model {model_id}: {e}")
        raise


def get_simulation_path(model_id: str, db_path: Optional[str] = None) -> str:
    """
    Get the file path to a simulation script for a given model ID.
    
    Args:
        model_id: The ID of the model to get path for
        db_path: Optional path to the database file
        
    Returns:
        str: The path to the simulation script file
        
    Raises:
        KeyError: If the model is not found
        Exception: For other database errors
    """
    try:
        # Create database configuration
        db_config = DatabaseConfig(database_path=db_path) if db_path else DatabaseConfig()
        
        # Create repository
        simulation_repo = SimulationRepository(db_config)
        
        # Get the simulation path
        script_path = simulation_repo.get_simulation_path(model_id)
        
        log.info(f"Retrieved script path for model {model_id}: {script_path}")
        return script_path
        
    except Exception as e:
        log.error(f"Failed to get simulation path for model {model_id}: {e}")
        raise
