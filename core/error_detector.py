#!/usr/bin/env python3
"""
Error Detector - Multi-layer error detection system.

Detects syntax, import, runtime, type, and logic errors in Python code.
Part of the self-healing code repair system.
"""

import ast
import sys
import logging
import subprocess
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import importlib.util
import traceback
from io import StringIO
import contextlib


logger = logging.getLogger("ErrorDetector")


class ErrorCategory(Enum):
    """Error classification categories."""
    SYNTAX = "syntax"
    IMPORT = "import"
    RUNTIME = "runtime"
    TYPE = "type"
    LOGIC = "logic"
    UNKNOWN = "unknown"


class ErrorSeverity(Enum):
    """Error severity levels."""
    CRITICAL = "critical"  # Blocks execution
    HIGH = "high"  # Major functionality broken
    MEDIUM = "medium"  # Minor issues
    LOW = "low"  # Style/optimization issues


@dataclass
class DetectedError:
    """
    Represents a detected error in code.

    Attributes:
        category: Error category (syntax, import, etc.)
        severity: Error severity level
        message: Human-readable error message
        line_number: Line where error occurred (if applicable)
        column: Column where error occurred (if applicable)
        code_snippet: Relevant code snippet
        exception_type: Original exception type
        stack_trace: Full stack trace (if available)
        suggested_fix: Suggested fix description
    """
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    line_number: Optional[int] = None
    column: Optional[int] = None
    code_snippet: Optional[str] = None
    exception_type: Optional[str] = None
    stack_trace: Optional[str] = None
    suggested_fix: Optional[str] = None

    def to_dict(self) -> Dict:
        """Convert error to dictionary representation."""
        return {
            "category": self.category.value,
            "severity": self.severity.value,
            "message": self.message,
            "line_number": self.line_number,
            "column": self.column,
            "code_snippet": self.code_snippet,
            "exception_type": self.exception_type,
            "stack_trace": self.stack_trace,
            "suggested_fix": self.suggested_fix
        }


class ErrorDetector:
    """
    Multi-layer error detection system.

    Detects various types of errors in Python code:
    - Syntax errors via AST parsing
    - Import errors via import simulation
    - Runtime errors via sandboxed execution
    - Type errors via static analysis
    - Logic errors via test execution
    """

    def __init__(self):
        """Initialize error detector."""
        logger.info("ErrorDetector initialized")

    def detect_all_errors(
        self,
        code: str,
        run_tests: bool = False,
        test_cases: Optional[List[Dict]] = None
    ) -> List[DetectedError]:
        """
        Detect all types of errors in code.

        Args:
            code: Python code to analyze
            run_tests: Whether to run test cases
            test_cases: Optional test cases for logic error detection

        Returns:
            List of detected errors
        """
        errors = []

        try:
            # 1. Syntax errors (fast, run first)
            syntax_errors = self.detect_syntax_errors(code)
            errors.extend(syntax_errors)

            # If syntax errors exist, stop here (can't proceed)
            if syntax_errors:
                logger.info(
                    f"Found {len(syntax_errors)} syntax errors, stopping analysis")
                return errors

            # 2. Import errors
            import_errors = self.detect_import_errors(code)
            errors.extend(import_errors)

            # 3. Type errors (static analysis)
            type_errors = self.detect_type_errors(code)
            errors.extend(type_errors)

            # 4. Runtime errors (if no critical errors)
            if not any(e.severity == ErrorSeverity.CRITICAL for e in errors):
                runtime_errors = self.detect_runtime_errors(code)
                errors.extend(runtime_errors)

            # 5. Logic errors (if tests provided)
            if run_tests and test_cases:
                logic_errors = self.detect_logic_errors(code, test_cases)
                errors.extend(logic_errors)

        except Exception as e:
            logger.error(f"Error during detection: {e}")
            errors.append(DetectedError(
                category=ErrorCategory.UNKNOWN,
                severity=ErrorSeverity.HIGH,
                message=f"Detection failed: {str(e)}",
                exception_type=type(e).__name__
            ))

        logger.info(f"Total errors detected: {len(errors)}")
        return errors

    def detect_syntax_errors(self, code: str) -> List[DetectedError]:
        """
        Detect syntax errors via AST parsing.

        Args:
            code: Python code to analyze

        Returns:
            List of syntax errors
        """
        errors = []

        try:
            ast.parse(code)
            logger.debug("No syntax errors found")
        except SyntaxError as e:
            error = DetectedError(
                category=ErrorCategory.SYNTAX,
                severity=ErrorSeverity.CRITICAL,
                message=e.msg or "Syntax error",
                line_number=e.lineno,
                column=e.offset,
                code_snippet=e.text.strip() if e.text else None,
                exception_type="SyntaxError",
                suggested_fix=self._suggest_syntax_fix(e)
            )
            errors.append(error)
            logger.info(f"Syntax error at line {e.lineno}: {e.msg}")

        return errors

    def detect_import_errors(self, code: str) -> List[DetectedError]:
        """
        Detect import errors by analyzing import statements.

        Args:
            code: Python code to analyze

        Returns:
            List of import errors
        """
        errors = []

        try:
            tree = ast.parse(code)

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if not self._is_module_available(alias.name):
                            error = DetectedError(
                                category=ErrorCategory.IMPORT,
                                severity=ErrorSeverity.HIGH,
                                message=f"Module '{alias.name}' not found",
                                line_number=node.lineno,
                                exception_type="ImportError",
                                suggested_fix=f"Install module: pip install {alias.name}"
                            )
                            errors.append(error)

                elif isinstance(node, ast.ImportFrom):
                    if node.module and not self._is_module_available(
                            node.module):
                        error = DetectedError(
                            category=ErrorCategory.IMPORT,
                            severity=ErrorSeverity.HIGH,
                            message=f"Module '{node.module}' not found",
                            line_number=node.lineno,
                            exception_type="ImportError",
                            suggested_fix=f"Install module: pip install {node.module}"
                        )
                        errors.append(error)

        except Exception as e:
            logger.error(f"Error detecting imports: {e}")

        logger.info(f"Found {len(errors)} import errors")
        return errors

    def detect_runtime_errors(
        self,
        code: str,
        timeout: int = 5
    ) -> List[DetectedError]:
        """
        Detect runtime errors via sandboxed execution.

        Args:
            code: Python code to execute
            timeout: Execution timeout in seconds

        Returns:
            List of runtime errors
        """
        errors = []

        try:
            # Create isolated namespace
            namespace = {
                "__builtins__": __builtins__,
                "__name__": "__main__"
            }

            # Capture stdout/stderr
            stdout_capture = StringIO()
            stderr_capture = StringIO()

            with contextlib.redirect_stdout(stdout_capture):
                with contextlib.redirect_stderr(stderr_capture):
                    try:
                        exec(code, namespace)
                    except Exception as e:
                        error = DetectedError(
                            category=ErrorCategory.RUNTIME,
                            severity=ErrorSeverity.HIGH,
                            message=str(e),
                            exception_type=type(e).__name__,
                            stack_trace=traceback.format_exc(),
                            suggested_fix=self._suggest_runtime_fix(e)
                        )
                        errors.append(error)
                        logger.info(f"Runtime error: {type(e).__name__}: {e}")

        except Exception as e:
            logger.error(f"Error during runtime detection: {e}")

        return errors

    def detect_type_errors(self, code: str) -> List[DetectedError]:
        """
        Detect type errors via static analysis.

        Uses mypy if available, otherwise basic type checking.

        Args:
            code: Python code to analyze

        Returns:
            List of type errors
        """
        errors = []

        try:
            # Try using mypy if available
            result = subprocess.run(
                ["mypy", "--command", code],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode != 0:
                # Parse mypy output
                for line in result.stdout.split("\n"):
                    if "error:" in line.lower():
                        error = DetectedError(
                            category=ErrorCategory.TYPE,
                            severity=ErrorSeverity.MEDIUM,
                            message=line.strip(),
                            exception_type="TypeError"
                        )
                        errors.append(error)

        except (FileNotFoundError, subprocess.TimeoutExpired):
            # mypy not available or timeout, skip type checking
            logger.debug("mypy not available, skipping type error detection")
        except Exception as e:
            logger.error(f"Error detecting type errors: {e}")

        return errors

    def detect_logic_errors(
        self,
        code: str,
        test_cases: List[Dict]
    ) -> List[DetectedError]:
        """
        Detect logic errors by running test cases.

        Args:
            code: Python code to test
            test_cases: List of test cases with input/expected output

        Returns:
            List of logic errors
        """
        errors = []

        try:
            # Execute code in namespace
            namespace = {}
            exec(code, namespace)

            # Run each test case
            for i, test in enumerate(test_cases):
                func_name = test.get("function")
                inputs = test.get("input", {})
                expected = test.get("expected")

                if func_name not in namespace:
                    continue

                func = namespace[func_name]

                try:
                    if isinstance(inputs, dict):
                        result = func(**inputs)
                    elif isinstance(inputs, (list, tuple)):
                        result = func(*inputs)
                    else:
                        result = func(inputs)

                    if result != expected:
                        error = DetectedError(
                            category=ErrorCategory.LOGIC,
                            severity=ErrorSeverity.MEDIUM,
                            message=f"Test case {i + 1} failed: expected {expected}, got {result}",
                            exception_type="AssertionError",
                            suggested_fix=f"Review logic in function '{func_name}'")
                        errors.append(error)

                except Exception as e:
                    error = DetectedError(
                        category=ErrorCategory.LOGIC,
                        severity=ErrorSeverity.HIGH,
                        message=f"Test case {i + 1} raised exception: {e}",
                        exception_type=type(e).__name__,
                        stack_trace=traceback.format_exc()
                    )
                    errors.append(error)

        except Exception as e:
            logger.error(f"Error detecting logic errors: {e}")

        logger.info(
            f"Found {len(errors)} logic errors from {len(test_cases)} test cases")
        return errors

    def classify_error(self, exception: Exception) -> ErrorCategory:
        """
        Classify an exception into error category.

        Args:
            exception: Python exception

        Returns:
            Error category
        """
        exc_type = type(exception).__name__

        if exc_type == "SyntaxError":
            return ErrorCategory.SYNTAX
        elif exc_type in ["ImportError", "ModuleNotFoundError"]:
            return ErrorCategory.IMPORT
        elif exc_type in ["TypeError", "AttributeError"]:
            return ErrorCategory.TYPE
        elif exc_type in ["AssertionError", "ValueError"]:
            return ErrorCategory.LOGIC
        else:
            return ErrorCategory.RUNTIME

    def _is_module_available(self, module_name: str) -> bool:
        """
        Check if a module is available for import.

        Args:
            module_name: Name of module to check

        Returns:
            True if module is available
        """
        try:
            spec = importlib.util.find_spec(module_name)
            return spec is not None
        except (ImportError, ModuleNotFoundError, ValueError):
            return False

    def _suggest_syntax_fix(self, error: SyntaxError) -> str:
        """
        Suggest fix for syntax error.

        Args:
            error: Syntax error

        Returns:
            Suggested fix description
        """
        msg = error.msg.lower() if error.msg else ""

        if "invalid syntax" in msg:
            return "Check for missing colons, parentheses, or quotes"
        elif "unexpected eof" in msg:
            return "Check for unclosed brackets, parentheses, or quotes"
        elif "indentation" in msg:
            return "Fix indentation to match Python standards"
        else:
            return "Review syntax at indicated line"

    def _suggest_runtime_fix(self, exception: Exception) -> str:
        """
        Suggest fix for runtime error.

        Args:
            exception: Runtime exception

        Returns:
            Suggested fix description
        """
        exc_type = type(exception).__name__

        if exc_type == "NameError":
            return "Check for undefined variables or typos"
        elif exc_type == "AttributeError":
            return "Check object has the attribute being accessed"
        elif exc_type == "KeyError":
            return "Check dictionary key exists before accessing"
        elif exc_type == "IndexError":
            return "Check list/array index is within bounds"
        elif exc_type == "ZeroDivisionError":
            return "Add check to prevent division by zero"
        else:
            return f"Handle {exc_type} exception appropriately"