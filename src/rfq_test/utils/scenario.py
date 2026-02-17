"""YAML scenario loading with variable substitution."""

import re
import time
from pathlib import Path
from typing import Any, Optional

import yaml


def get_scenario_id(scenario: dict) -> str:
    """Return test ID for a scenario (for pytest parametrization)."""
    return scenario.get("name", "unknown")


def substitute_scenario_input(
    input_data: dict,
    address_map: dict[str, Any],
) -> dict:
    """Return a copy of input_data with template keys replaced from address_map.

    Replaces values that exactly match a key in address_map (e.g. "${address:admin}" -> address).
    Walks dicts and lists recursively. Use for scenario input only (not private keys).
    """
    def _sub(t: Any) -> Any:
        if isinstance(t, dict):
            return {k: _sub(v) for k, v in t.items()}
        if isinstance(t, list):
            return [_sub(x) for x in t]
        if isinstance(t, str) and t in address_map:
            return address_map[t]
        return t

    return _sub(input_data)


def load_contract_scenarios(
    file_path: str,
    flatten_operations: Optional[list[str]] = None,
    result_key: str = "accept_quote",
    scenarios_dir: Optional[Path] = None,
) -> list[dict]:
    """Load contract validation scenarios from YAML.

    Args:
        file_path: Relative path from scenarios directory (e.g. "contract/admin_validations.yaml").
        flatten_operations: If set (e.g. ["register_maker", "revoke_maker"]), flatten those
            top-level keys into a single list, each scenario with an "operation" field.
        result_key: When flatten_operations is None, return data.get(result_key, []).
        scenarios_dir: Override scenarios directory (default: repo scenarios/).

    Returns:
        List of scenario dicts.
    """
    if scenarios_dir is None:
        scenarios_dir = Path(__file__).parent.parent.parent.parent / "scenarios"
    full_path = scenarios_dir / file_path
    if not full_path.exists():
        raise FileNotFoundError(f"Scenario file not found: {full_path}")
    with open(full_path) as f:
        data = yaml.safe_load(f) or {}

    if flatten_operations:
        scenarios = []
        for op in flatten_operations:
            for scenario in data.get(op, []):
                scenarios.append({**scenario, "operation": op})
        return scenarios
    return data.get(result_key, [])


class ScenarioLoader:
    """Load test scenarios from YAML files with variable substitution.
    
    Supports placeholders like:
    - ${timestamp} - Current timestamp
    - ${address:taker} - Reference to a named address
    - ${market_id} - Reference to configured market
    """
    
    def __init__(
        self,
        scenarios_dir: Optional[Path] = None,
        variables: Optional[dict[str, Any]] = None,
    ):
        """Initialize scenario loader.
        
        Args:
            scenarios_dir: Path to scenarios directory
            variables: Initial variables for substitution
        """
        if scenarios_dir is None:
            scenarios_dir = Path(__file__).parent.parent.parent.parent / "scenarios"
        
        self.scenarios_dir = scenarios_dir
        self.variables = variables or {}
    
    def set_variable(self, name: str, value: Any) -> None:
        """Set a variable for substitution.
        
        Args:
            name: Variable name
            value: Variable value
        """
        self.variables[name] = value
    
    def _substitute(self, value: Any) -> Any:
        """Recursively substitute variables in value.
        
        Args:
            value: Value to process
            
        Returns:
            Value with substitutions applied
        """
        if isinstance(value, str):
            # Find all ${...} placeholders
            pattern = r'\$\{([^}]+)\}'
            
            def replace(match):
                key = match.group(1)
                
                # Special built-in variables
                if key == "timestamp":
                    return str(int(time.time() * 1000))
                if key == "timestamp_s":
                    return str(int(time.time()))
                
                # Check for prefixed variables (e.g., address:taker)
                if ":" in key:
                    prefix, name = key.split(":", 1)
                    nested = self.variables.get(prefix, {})
                    if isinstance(nested, dict):
                        return str(nested.get(name, match.group(0)))
                
                # Simple variable lookup
                if key in self.variables:
                    return str(self.variables[key])
                
                # Return original if not found
                return match.group(0)
            
            return re.sub(pattern, replace, value)
        
        elif isinstance(value, dict):
            return {k: self._substitute(v) for k, v in value.items()}
        
        elif isinstance(value, list):
            return [self._substitute(item) for item in value]
        
        return value
    
    def load(self, file_path: str) -> dict:
        """Load scenarios from YAML file.
        
        Args:
            file_path: Relative path from scenarios directory
            
        Returns:
            Loaded and processed scenarios
        """
        full_path = self.scenarios_dir / file_path
        
        if not full_path.exists():
            raise FileNotFoundError(f"Scenario file not found: {full_path}")
        
        with open(full_path) as f:
            data = yaml.safe_load(f)
        
        # Apply variable substitution
        return self._substitute(data)
    
    def load_test_cases(self, file_path: str) -> list[dict]:
        """Load test cases from YAML file.
        
        Expects YAML format:
        ```yaml
        test_cases:
          - name: "Test case 1"
            input: {...}
            expected: {...}
        ```
        
        Args:
            file_path: Relative path from scenarios directory
            
        Returns:
            List of test cases
        """
        data = self.load(file_path)
        return data.get("test_cases", [])


def load_scenarios(
    file_path: str,
    scenarios_dir: Optional[Path] = None,
    **variables,
) -> list[dict]:
    """Convenience function to load scenarios.
    
    Args:
        file_path: Relative path to scenario file
        scenarios_dir: Optional scenarios directory
        **variables: Variables for substitution
        
    Returns:
        List of test cases
    """
    loader = ScenarioLoader(scenarios_dir=scenarios_dir, variables=variables)
    return loader.load_test_cases(file_path)
