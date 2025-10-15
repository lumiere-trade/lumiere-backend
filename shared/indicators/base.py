"""
Abstract base indicator interface for shared indicators.

Defines the contract that all shared indicators must implement.
This is a pure calculation layer with zero dependencies on logging,
config management, or event systems.
"""

from abc import ABC, abstractmethod
from typing import Dict, Union

import pandas as pd


class BaseIndicator(ABC):
    """
    Abstract base class for pure indicator calculations.

    Shared indicators are stateless calculation engines that:
    - Accept parameters via **kwargs
    - Validate parameters
    - Compute indicator values from DataFrame
    - Return pandas Series or Dict of Series

    NO side effects, NO logging, NO external dependencies.
    Wrappers (Forger/Rebalancer) add additional functionality.

    Attributes:
        params: Dictionary of indicator parameters
    """

    def __init__(self, **params):
        """
        Initialize indicator with parameters.

        Args:
            **params: Indicator-specific parameters (e.g., period=14)

        Raises:
            ValueError: If parameters are invalid
        """
        self.params = params
        self.validate_params()

    @abstractmethod
    def validate_params(self) -> None:
        """
        Validate indicator parameters.

        Should raise ValueError if parameters are invalid.
        Called during initialization.

        Raises:
            ValueError: If parameters are invalid

        Example:
            def validate_params(self) -> None:
                period = self.params.get('period', 14)
                if not isinstance(period, int) or period < 2:
                    raise ValueError(f"Period must be int >= 2, got: {period}")
        """

    @abstractmethod
    def calculate(self, df: pd.DataFrame) -> Union[pd.Series, Dict[str, pd.Series]]:
        """
        Calculate indicator values for entire DataFrame.

        This is the main computation method. Must be implemented
        by all concrete indicators.

        Args:
            df: DataFrame with OHLCV columns (open, high, low, close, volume)

        Returns:
            pd.Series: Single-value indicators (e.g., RSI, EMA)
            Dict[str, pd.Series]: Multi-value indicators (e.g., SMA with distance)

        Raises:
            ValueError: If DataFrame is invalid or insufficient data
            KeyError: If required columns are missing

        Example:
            # Single-value indicator
            return pd.Series([14.5, 15.2, ...], index=df.index)

            # Multi-value indicator
            return {
                'sma': pd.Series([...]),
                'distance': pd.Series([...])
            }
        """

    def __repr__(self) -> str:
        """String representation."""
        return f"{self.__class__.__name__}(params={self.params})"
