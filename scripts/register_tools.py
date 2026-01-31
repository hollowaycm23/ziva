#!/usr/bin/env python3
"""
Register Essential Tools - Ensures core tools are available in registry.
"""

import logging
from tools.registry.tool_registry import ToolRegistry
import sys
sys.path.append("/home/holloway/ziva")


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("RegisterTools")


def main():
    """Register essential tools."""
    registry = ToolRegistry()

    logger.info("🔧 Registering essential tools...")

    # List current tools
    current_tools = registry.list_tools()
    logger.info(f"Current tools in registry: {list(current_tools.keys())}")

    # The extensions should auto-load, but let's verify
    if "get_weather" in current_tools:
        logger.info("✅ get_weather already registered")
    else:
        logger.warning(
            "❌ get_weather NOT found - extension loading may have failed")

    if "get_air_quality" in current_tools:
        logger.info("✅ get_air_quality already registered")
    else:
        logger.warning("❌ get_air_quality NOT found")

    # Print all registered tools
    logger.info("\n📋 All registered tools:")
    for name, versions in current_tools.items():
        latest = versions[-1] if versions else None
        if latest:
            logger.info(
                f"  - {name} (v{latest['version']}): {latest['description'][:60]}...")

    logger.info(f"\n✅ Total tools registered: {len(current_tools)}")


if __name__ == "__main__":
    main()
