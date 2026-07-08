import unittest
import json
import tempfile
import time
from pathlib import Path


class TestDynamicToolValidator(unittest.TestCase):
    def setUp(self):
        from core.dynamic_tools.validator import DynamicToolValidator
        self.validator = DynamicToolValidator()

    def test_valid_function(self):
        code = '''def test_tool(input: dict) -> dict:
    """A valid test tool."""
    return {"result": input.get("value", 0) * 2}
'''
        result = self.validator.validate(code)
        self.assertTrue(result, f"Expected valid, got: {result.reason}")

    def test_no_docstring(self):
        code = '''def test_tool(input: dict) -> dict:
    return {"result": 42}
'''
        result = self.validator.validate(code)
        self.assertFalse(result)
        self.assertIn("docstring", result.reason.lower())

    def test_forbidden_import_os(self):
        code = '''def test_tool(input: dict) -> dict:
    """Test with forbidden import."""
    import os
    return {"result": os.getcwd()}
'''
        result = self.validator.validate(code)
        self.assertFalse(result)

    def test_forbidden_import_subprocess(self):
        code = '''def test_tool(input: dict) -> dict:
    """Test with forbidden import."""
    import subprocess
    return {"result": "ok"}
'''
        result = self.validator.validate(code)
        self.assertFalse(result)

    def test_allowed_import_math(self):
        code = '''def test_tool(input: dict) -> dict:
    """Test with allowed import."""
    import math
    return {"result": math.sqrt(input.get("x", 0))}
'''
        result = self.validator.validate(code)
        self.assertTrue(result, f"Expected valid, got: {result.reason}")

    def test_forbidden_exec_call(self):
        code = '''def test_tool(input: dict) -> dict:
    """Test with exec."""
    exec("x = 1")
    return {"result": 42}
'''
        result = self.validator.validate(code)
        self.assertFalse(result)

    def test_forbidden_attr_system(self):
        code = '''def test_tool(input: dict) -> dict:
    """Test forbidden attr."""
    import math
    return {"result": 42}
'''
        code_with_os = '''def test_tool(input: dict) -> dict:
    """Test."""
    import math
    x.system("ls")
    return {"result": 42}
'''
        result = self.validator.validate(code_with_os)
        self.assertFalse(result)

    def test_syntax_error(self):
        code = '''def test_tool(input: dict) -> dict:
    """Docstring
    return {
'''
        result = self.validator.validate(code)
        self.assertFalse(result)

    def test_no_function_def(self):
        code = '''x = 1
y = 2
'''
        result = self.validator.validate(code)
        self.assertFalse(result)

    def test_harmonic_oscillator_tool(self):
        code = '''def calcular_oscilador(input: dict) -> dict:
    """Calcula posicao de um oscilador harmonico amortecido.
    
    Args:
        input: dict com 'm' (massa), 'k' (constante elastica), 'b' (coeficiente amortecimento), 't' (tempo)
    Returns:
        dict com 'posicao' e 'energia'
    """
    import math
    m = input.get("m", 1.0)
    k = input.get("k", 1.0)
    b = input.get("b", 0.1)
    t = input.get("t", 1.0)
    
    omega0 = math.sqrt(k / m)
    gamma = b / (2 * m)
    if gamma < omega0:
        omega = math.sqrt(omega0**2 - gamma**2)
        x = math.exp(-gamma * t) * math.cos(omega * t)
    else:
        x = math.exp(-gamma * t) * (1 + gamma * t)
    
    energia = 0.5 * k * x**2 + 0.5 * m * 0
    return {"posicao": round(x, 6), "energia": round(energia, 6)}
'''
        result = self.validator.validate(code)
        self.assertTrue(result, f"Expected valid, got: {result.reason}")

    def test_temperature_converter(self):
        code = '''def converter_temperatura(input: dict) -> dict:
    """Converte entre Celsius, Fahrenheit e Kelvin.
    
    Args:
        input: dict com 'valor' (float) e 'de'/'para' ('c', 'f', 'k')
    Returns:
        dict com 'resultado' em float e 'unidade' string
    """
    valor = input.get("valor", 0)
    de = input.get("de", "c").lower()
    para = input.get("para", "f").lower()
    
    # Primeiro converte para Celsius
    if de == "f":
        celsius = (valor - 32) * 5/9
    elif de == "k":
        celsius = valor - 273.15
    else:
        celsius = valor
    
    # Depois converte de Celsius para destino
    if para == "f":
        resultado = celsius * 9/5 + 32
        unidade = "F"
    elif para == "k":
        resultado = celsius + 273.15
        unidade = "K"
    else:
        resultado = celsius
        unidade = "C"
    
    return {"resultado": round(resultado, 2), "unidade": unidade}
'''
        result = self.validator.validate(code)
        self.assertTrue(result, f"Expected valid, got: {result.reason}")


class TestDynamicToolRegistry(unittest.TestCase):
    def setUp(self):
        from core.dynamic_tools.registry import DynamicToolRegistry
        self.tmp = tempfile.mktemp(suffix=".json")
        self.registry = DynamicToolRegistry(Path(self.tmp))

    def tearDown(self):
        try:
            Path(self.tmp).unlink(missing_ok=True)
        except Exception:
            pass

    def test_register_and_get(self):
        version = self.registry.register("test_tool", "def test_tool(i): pass", "A test tool")
        self.assertEqual(version, 1)
        meta = self.registry.get("test_tool")
        self.assertIsNotNone(meta)
        self.assertEqual(meta.name, "test_tool")
        self.assertEqual(meta.version, 1)

    def test_update_existing(self):
        self.registry.register("test_tool", "def test_tool(i): pass", "v1")
        version = self.registry.register("test_tool", "def test_tool(i): return 2", "v2")
        self.assertEqual(version, 2)
        meta = self.registry.get("test_tool")
        self.assertEqual(meta.code, "def test_tool(i): return 2")

    def test_delete(self):
        self.registry.register("test_tool", "def test_tool(i): pass", "test")
        self.assertTrue(self.registry.delete("test_tool"))
        self.assertIsNone(self.registry.get("test_tool"))
        self.assertFalse(self.registry.delete("nonexistent"))

    def test_list_tools(self):
        self.registry.register("a", "def a(i): pass", "tool a")
        self.registry.register("b", "def b(i): pass", "tool b")
        tools = self.registry.list_tools()
        self.assertEqual(len(tools), 2)

    def test_record_usage(self):
        self.registry.register("test_tool", "def test_tool(i): pass", "test")
        self.registry.record_usage("test_tool", True)
        self.registry.record_usage("test_tool", False)
        meta = self.registry.get("test_tool")
        self.assertEqual(meta.usage_count, 2)
        self.assertEqual(meta.success_count, 1)
        self.assertEqual(meta.success_rate, 0.5)

    def test_persistence(self):
        from core.dynamic_tools.registry import DynamicToolRegistry
        self.registry.register("persist_tool", "def f(i): pass", "persist test")
        registry2 = DynamicToolRegistry(Path(self.tmp))
        meta = registry2.get("persist_tool")
        self.assertIsNotNone(meta)
        self.assertEqual(meta.name, "persist_tool")

    def test_get_all_code(self):
        self.registry.register("a", "code_a", "tool a")
        self.registry.register("b", "code_b", "tool b")
        codes = self.registry.get_all_code()
        self.assertEqual(codes["a"], "code_a")
        self.assertEqual(codes["b"], "code_b")


class TestDynamicToolRuntime(unittest.TestCase):
    def setUp(self):
        from core.dynamic_tools.registry import DynamicToolRegistry
        from core.dynamic_tools.runtime import DynamicToolRuntime
        self.tmp = tempfile.mktemp(suffix=".json")
        self.registry = DynamicToolRegistry(Path(self.tmp))
        self.runtime = DynamicToolRuntime(self.registry)

    def tearDown(self):
        try:
            Path(self.tmp).unlink(missing_ok=True)
        except Exception:
            pass

    def test_execute_simple(self):
        self.registry.register("double",
            """def double(input: dict) -> dict:
    \"\"\"Double a number.\"\"\"
    return {"result": input.get("x", 0) * 2}
""",
            "Doubles a number")
        result = self.runtime.execute("double", {"x": 5})
        self.assertIn("10", result)

    def test_execute_with_math(self):
        self.registry.register("sqrt_tool",
            """def sqrt_tool(input: dict) -> dict:
    \"\"\"Calculate square root.\"\"\"
    import math
    return {"result": math.sqrt(input.get("x", 0))}
""",
            "Square root calculator")
        result = self.runtime.execute("sqrt_tool", {"x": 16})
        self.assertIn("4.0", result)

    def test_tool_not_found(self):
        result = self.runtime.execute("nonexistent", {})
        self.assertIn("not found", result)

    def test_runtime_exception(self):
        self.registry.register("bad_tool",
            """def bad_tool(input: dict) -> dict:
    \"\"\"Will raise an error.\"\"\"
    return {"result": 1 / 0}
""",
            "Bad tool")
        result = self.runtime.execute("bad_tool", {})
        self.assertIn("division by zero", result)

    def test_timeout(self):
        self.registry.register("slow_tool",
            """def slow_tool(input: dict) -> dict:
    \"\"\"Slow tool.\"\"\"
    import time
    time.sleep(5)
    return {"result": 42}
""",
            "Slow tool")
        result = self.runtime.execute("slow_tool", {}, timeout=1)
        self.assertIn("timed out", result.lower())

    def test_temperature_converter_execution(self):
        code = '''def converter_temperatura(input: dict) -> dict:
    """Converte entre Celsius, Fahrenheit e Kelvin."""
    valor = input.get("valor", 0)
    de = input.get("de", "c").lower()
    para = input.get("para", "f").lower()
    if de == "f":
        celsius = (valor - 32) * 5/9
    elif de == "k":
        celsius = valor - 273.15
    else:
        celsius = valor
    if para == "f":
        resultado = celsius * 9/5 + 32
        unidade = "F"
    elif para == "k":
        resultado = celsius + 273.15
        unidade = "K"
    else:
        resultado = celsius
        unidade = "C"
    return {"resultado": round(resultado, 2), "unidade": unidade}
'''
        self.registry.register("converter_temperatura", code, "Temperature converter")
        result = self.runtime.execute("converter_temperatura", {"valor": 100, "de": "c", "para": "f"})
        self.assertIn("212", result)
        result2 = self.runtime.execute("converter_temperatura", {"valor": 32, "de": "f", "para": "c"})
        self.assertIn("0", result2)
        result3 = self.runtime.execute("converter_temperatura", {"valor": 0, "de": "c", "para": "k"})
        self.assertIn("273", result3)


class TestExtensionFunctions(unittest.TestCase):
    def setUp(self):
        from core.dynamic_tools.registry import DynamicToolRegistry
        import tempfile
        self.tmp = tempfile.mktemp(suffix=".json")
        self.registry = DynamicToolRegistry(Path(self.tmp))
        import extensions.dynamic_tools as dt_mod
        self._orig_get_registry = getattr(dt_mod, '_get_registry', None)
        dt_mod._get_registry = lambda: self.registry

    def tearDown(self):
        try:
            Path(self.tmp).unlink(missing_ok=True)
        except Exception:
            pass
        import extensions.dynamic_tools as dt_mod
        dt_mod._get_registry = self._orig_get_registry

    def test_create_tool_valid(self):
        from extensions.dynamic_tools import create_tool
        result = create_tool("test_extension",
            """def test_extension(input: dict) -> dict:
    \"\"\"Test extension tool.\"\"\"
    return {"result": input.get("x", 0) + 1}
""",
            "Adds one to input")
        self.assertIn("sucesso", result.lower())
        self.assertIn("v1", result)
        meta = self.registry.get("test_extension")
        self.assertIsNotNone(meta)

    def test_create_tool_invalid(self):
        from extensions.dynamic_tools import create_tool
        result = create_tool("bad_tool", "def bad_tool(i): pass", "No docstring")
        self.assertIn("erro", result.lower())

    def test_list_tools_empty(self):
        from extensions.dynamic_tools import list_dynamic_tools
        result = list_dynamic_tools()
        self.assertIn("nenhuma", result.lower())

    def test_list_tools_with_items(self):
        self.registry.register("tool_a", "def f(i): pass", "Tool A")
        self.registry.register("tool_b", "def f(i): pass", "Tool B")
        from extensions.dynamic_tools import list_dynamic_tools
        result = list_dynamic_tools()
        self.assertIn("tool_a", result)
        self.assertIn("tool_b", result)

    def test_delete_tool(self):
        self.registry.register("del_tool", "def f(i): pass", "Delete me")
        from extensions.dynamic_tools import delete_tool
        result = delete_tool("del_tool")
        self.assertIn("sucesso", result.lower())
        self.assertIsNone(self.registry.get("del_tool"))

    def test_delete_nonexistent(self):
        from extensions.dynamic_tools import delete_tool
        result = delete_tool("nonexistent")
        self.assertIn("não encontrada", result.lower())


class TestGetSafeGlobals(unittest.TestCase):
    def test_safe_globals_has_math(self):
        from core.dynamic_tools.validator import DynamicToolValidator
        safe = DynamicToolValidator.get_safe_globals()
        self.assertIn("abs", safe)
        self.assertIn("len", safe)
        self.assertIsInstance(safe["len"], type(len))

    def test_safe_globals_no_eval(self):
        from core.dynamic_tools.validator import DynamicToolValidator
        safe = DynamicToolValidator.get_safe_globals()
        self.assertNotIn("eval", safe)
        self.assertNotIn("exec", safe)
        self.assertNotIn("open", safe)


if __name__ == "__main__":
    unittest.main()
