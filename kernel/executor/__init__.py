"""
QMK Executor

Circuit execution and resource management in supervisor mode.

Components:
- enhanced_executor: QVM graph executor
- resource_manager: Physical resource management
"""

from .enhanced_executor import EnhancedExecutor
from .resource_manager import ResourceManager

__all__ = ['EnhancedExecutor', 'ResourceManager']
