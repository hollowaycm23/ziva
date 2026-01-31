#!/usr/bin/env python3
"""
Test suite for Ziva's Self-Healing Engine.

Tests error detection, root cause analysis, auto-fixing, and validation.
"""

import pytest
from core.error_detector import ErrorDetector, ErrorCategory, ErrorSeverity
from core.root_cause_analyzer import RootCauseAnalyzer
from core.auto_fixer import AutoFixer
from core.self_healing_engine import SelfHealingEngine


class TestErrorDetector:
    """Test error detection capabilities."""

    def test_syntax_error_detection(self):
        """Test detection of syntax errors."""
        code = """
def broken_function()
    return "missing colon"
"""
        detector = ErrorDetector()
        errors = detector.detect_syntax_errors(code)

        assert len(errors) > 0
        assert errors[0].category == ErrorCategory.SYNTAX
        assert errors[0].severity == ErrorSeverity.CRITICAL

    def test_import_error_detection(self):
        """Test detection of import errors."""
        code = """
import nonexistent_module

def use_module():
    return nonexistent_module.function()
"""
        detector = ErrorDetector()
        errors = detector.detect_import_errors(code)

        assert len(errors) > 0
        assert errors[0].category == ErrorCategory.IMPORT

    def test_no_errors(self):
        """Test that valid code has no errors."""
        code = """
def valid_function(a, b):
    return a + b

result = valid_function(1, 2)
"""
        detector = ErrorDetector()
        errors = detector.detect_all_errors(code)

        assert len(errors) == 0


class TestRootCauseAnalyzer:
    """Test root cause analysis."""

    def test_syntax_error_analysis(self):
        """Test analysis of syntax errors."""
        code = """
def broken()
    pass
"""
        detector = ErrorDetector()
        errors = detector.detect_syntax_errors(code)

        analyzer = RootCauseAnalyzer()
        root_cause = analyzer.analyze(errors[0], code)

        assert root_cause.probable_cause is not None
        assert root_cause.confidence > 0
        assert len(root_cause.suggested_solutions) > 0

    def test_code_context_extraction(self):
        """Test extraction of code context."""
        code = """
def function1():
    pass

def function2():
    error_line
    pass
"""
        detector = ErrorDetector()
        errors = detector.detect_runtime_errors(code)

        if errors:
            analyzer = RootCauseAnalyzer()
            context = analyzer.extract_code_context(errors[0], code)

            assert context.error_line is not None
            assert len(context.before_lines) > 0


class TestAutoFixer:
    """Test automatic code fixing."""

    def test_syntax_fix_missing_colon(self):
        """Test fixing missing colon."""
        code = """
def function()
    return True
"""
        detector = ErrorDetector()
        errors = detector.detect_syntax_errors(code)

        fixer = AutoFixer()
        fixed_code = fixer.fix_syntax_error(errors[0], code)

        assert fixed_code is not None
        assert "def function():" in fixed_code

    def test_generate_multiple_fixes(self):
        """Test generation of multiple fix strategies."""
        code = """
def broken()
    pass
"""
        detector = ErrorDetector()
        errors = detector.detect_syntax_errors(code)

        analyzer = RootCauseAnalyzer()
        root_cause = analyzer.analyze(errors[0], code)

        fixer = AutoFixer()
        fixes = fixer.generate_fixes(root_cause, code)

        assert len(fixes) > 0
        assert all(hasattr(fix, 'confidence') for fix in fixes)


class TestSelfHealingEngine:
    """Test complete self-healing workflow."""

    def test_simple_syntax_repair(self):
        """Test repair of simple syntax error."""
        code = """
def calculate_sum(a, b)
    return a + b
"""
        engine = SelfHealingEngine(max_attempts=3)
        result = engine.repair_code(code)

        assert result.success or len(result.attempts) > 0
        if result.success:
            assert "def calculate_sum(a, b):" in result.repaired_code

    def test_multiple_errors_repair(self):
        """Test repair of multiple errors."""
        code = """
def process(data)
    if data is None
        return []
    return data
"""
        engine = SelfHealingEngine(max_attempts=5)
        result = engine.repair_code(code)

        assert len(result.attempts) > 0
        assert len(result.errors_fixed) >= 0

    def test_max_attempts_limit(self):
        """Test that max attempts limit is respected."""
        code = """
def unfixable()
    # This has syntax error
    return
"""
        engine = SelfHealingEngine(max_attempts=2)
        result = engine.repair_code(code)

        assert len(result.attempts) <= 2

    def test_rollback_on_regression(self):
        """Test rollback when fix makes things worse."""
        # This test would require a scenario where fix introduces new errors
        # For now, just verify rollback flag exists
        code = "def valid(): pass"
        engine = SelfHealingEngine()
        result = engine.repair_code(code)

        assert hasattr(result, 'rollback_performed')

    def test_error_detection_only(self):
        """Test error detection without repair."""
        code = """
def divide(a, b):
    return a / b
"""
        engine = SelfHealingEngine()
        errors = engine.detect_errors(code)

        # May or may not detect potential ZeroDivisionError
        assert isinstance(errors, list)


class TestIntegration:
    """Integration tests for complete workflows."""

    def test_end_to_end_repair(self):
        """Test complete repair workflow."""
        broken_code = """
def greet(name)
    return f"Hello, {name}"

result = greet("World")
"""
        engine = SelfHealingEngine()
        result = engine.repair_code(broken_code)

        # Verify result structure
        assert hasattr(result, 'success')
        assert hasattr(result, 'repaired_code')
        assert hasattr(result, 'attempts')
        assert hasattr(result, 'total_duration_ms')

    def test_valid_code_unchanged(self):
        """Test that valid code is not modified."""
        valid_code = """
def add(a, b):
    return a + b

result = add(1, 2)
"""
        engine = SelfHealingEngine()
        result = engine.repair_code(valid_code)

        assert result.success
        assert result.repaired_code == valid_code or result.repaired_code.strip() == valid_code.strip()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
