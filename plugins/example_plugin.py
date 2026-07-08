"""
Example Ziva Plugin.
To install: copy to plugins/ directory or install via pip (adds ziva_plugins entry point)
"""

__version__ = "1.0.0"
__description__ = "Example plugin providing utility tools"
__author__ = "Ziva"


def hello_plugin(input: dict) -> dict:
    """A simple tool that returns a greeting. Input: {name: str} -> Output: {greeting: str}"""
    name = input.get("name", "World")
    return {"greeting": f"Hello, {name}! From plugin."}


hello_plugin._is_ziva_tool = True


def square_number(input: dict) -> dict:
    """Squares a number. Input: {value: float} -> Output: {result: float}"""
    value = input.get("value", 0)
    return {"result": value * value}


square_number._is_ziva_tool = True


def on_startup():
    """Called when Ziva starts."""
    import logging
    logging.getLogger("PluginExample").info("Example plugin started!")


def on_shutdown():
    """Called when Ziva shuts down."""
    import logging
    logging.getLogger("PluginExample").info("Example plugin shutting down!")
