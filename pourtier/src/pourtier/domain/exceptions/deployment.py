"""
Deployment domain exceptions.
"""

from pourtier.domain.exceptions.base import PourtierException


class DeploymentError(PourtierException):
    """Base exception for strategy deployment errors."""


class StrategyNotFoundError(DeploymentError):
    """Raised when strategy does not exist in architect_db."""

    def __init__(self, strategy_id: str):
        super().__init__(
            f"Strategy {strategy_id} not found in architect database",
            code="STRATEGY_NOT_FOUND",
        )


class DeploymentAlreadyActiveError(DeploymentError):
    """Raised when trying to activate already active strategy."""

    def __init__(self, deployed_strategy_id: str):
        super().__init__(
            f"Strategy {deployed_strategy_id} is already active",
            code="DEPLOYMENT_ALREADY_ACTIVE",
        )


class InvalidDeploymentStateError(DeploymentError):
    """Raised when deployment state transition is invalid."""

    def __init__(self, current_state: str, attempted_action: str):
        super().__init__(
            f"Cannot {attempted_action} in {current_state} state",
            code="INVALID_DEPLOYMENT_STATE",
        )
