"""Compatibility import for consumers of the original RuntimePorts adapter."""

from .kernel import KernelRuntime, UncertainEffect

StandaloneRuntime = KernelRuntime

__all__ = ["KernelRuntime", "StandaloneRuntime", "UncertainEffect"]
