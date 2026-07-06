#!/usr/bin/env python3
"""
Root Cause Analyzer - Deep analysis of error causes.
"""

import re
import logging
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
import ast

from core.error_detector import DetectedError, ErrorCategory


logger = logging.getLogger("RootCauseAnalyzer")


@dataclass
class CodeContext:
    """
    Code context around an error.
    """
    error_line: str
    before_lines: List[str]
    after_lines: List[str]
    function_name: Optional[str] = None
    class_name: Optional[str] = None
    variables_in_scope: List[str] = None


@dataclass
class RootCause:
    """
    Root cause analysis result.
    """
    error: DetectedError
    context: CodeContext
    probable_cause: str
    contributing_factors: List[str]
    similar_patterns: List[str]
    suggested_solutions: List[Dict]
    confidence: float


class RootCauseAnalyzer:
    """
    Analyzes errors to determine root causes.
    """

    def __init__(self):
        """Initialize root cause analyzer."""
        self.error_patterns = self._load_error_patterns()
        logger.info("RootCauseAnalyzer initialized")

    def analyze(
        self,
        error: DetectedError,
        code: str
    ) -> RootCause:
        """
        Perform root cause analysis on an error.
        """
        logger.info(f"Analyzing {error.category.value} error: {error.message}")
        context = self.extract_code_context(error, code)
        stack_info = self.parse_stack_trace(
            error.stack_trace) if error.stack_trace else {}
        similar_patterns = self.find_similar_patterns(error)
        probable_cause = self._determine_probable_cause(
            error, context, stack_info)
        contributing_factors = self._identify_contributing_factors(
            error, context)
        solutions = self._generate_solutions(error, context, probable_cause)
        confidence = self._calculate_confidence(error, context, solutions)
        root_cause = RootCause(
            error=error,
            context=context,
            probable_cause=probable_cause,
            contributing_factors=contributing_factors,
            similar_patterns=similar_patterns,
            suggested_solutions=solutions,
            confidence=confidence
        )
        logger.info(
            f"Root cause identified: {probable_cause} (confidence: "
            f"{confidence:.2f})")
        return root_cause

    def extract_code_context(
        self,
        error: DetectedError,
        code: str,
        context_lines: int = 3
    ) -> CodeContext:
        """
        Extract code context around error location.
        """
        lines = code.split("\n")
        if error.line_number is None:
            return CodeContext(
                error_line="", before_lines=[], after_lines=[])
        line_idx = error.line_number - 1
        start_idx = max(0, line_idx - context_lines)
        end_idx = min(len(lines), line_idx + context_lines + 1)
        error_line = lines[line_idx] if line_idx < len(lines) else ""
        before_lines = lines[start_idx:line_idx]
        after_lines = lines[line_idx + 1:end_idx]
        function_name, class_name = self._find_enclosing_scope(
            code, error.line_number)
        variables = self._extract_variables_in_scope(code, error.line_number)
        return CodeContext(
            error_line=error_line,
            before_lines=before_lines,
            after_lines=after_lines,
            function_name=function_name,
            class_name=class_name,
            variables_in_scope=variables
        )

    def parse_stack_trace(self, stack_trace: str) -> Dict:
        """
        Parse stack trace to extract useful information.
        """
        info = {
            "frames": [], "exception_type": None, "exception_message": None}
        try:
            lines = stack_trace.split("\n")
            if lines:
                last_line = lines[-1].strip()
                if ":" in last_line:
                    exc_type, exc_msg = last_line.split(":", 1)
                    info["exception_type"] = exc_type.strip()
                    info["exception_message"] = exc_msg.strip()
            for line in lines:
                if line.strip().startswith("File"):
                    match = re.search(
                        r'File "([^"]+)", line (\d+), in (.+)', line)
                    if match:
                        info["frames"].append({
                            "file": match.group(1),
                            "line": int(match.group(2)),
                            "function": match.group(3)
                        })
        except Exception as e:
            logger.error(f"Error parsing stack trace: {e}")
        return info

    def find_similar_patterns(self, error: DetectedError) -> List[str]:
        """
        Find similar error patterns in knowledge base.
        """
        similar = []
        for pattern in self.error_patterns.get(error.category.value, []):
            if self._matches_pattern(error, pattern):
                similar.append(pattern["description"])
        return similar

    def _determine_probable_cause(
        self,
        error: DetectedError,
        context: CodeContext,
        stack_info: Dict
    ) -> str:
        """
        Determine the most probable cause of the error.
        """
        if error.category == ErrorCategory.SYNTAX:
            return self._analyze_syntax_cause(error, context)
        elif error.category == ErrorCategory.IMPORT:
            return self._analyze_import_cause(error, context)
        elif error.category == ErrorCategory.RUNTIME:
            return self._analyze_runtime_cause(error, context, stack_info)
        elif error.category == ErrorCategory.TYPE:
            return self._analyze_type_cause(error, context)
        elif error.category == ErrorCategory.LOGIC:
            return self._analyze_logic_cause(error, context)
        else:
            return "Unknown cause"

    def _analyze_syntax_cause(self, error: DetectedError,
                              context: CodeContext) -> str:
        msg = error.message.lower()
        line = context.error_line.strip()
        if "missing" in msg and ":" in msg:
            return "Missing colon at end of statement"
        elif "unexpected eof" in msg:
            return "Unclosed bracket, parenthesis, or quote"
        elif "invalid syntax" in msg:
            if line.count("(") != line.count(")"):
                return "Unbalanced parentheses"
            elif line.count("[") != line.count("]"):
                return "Unbalanced brackets"
            elif line.count("{") != line.count("}"):
                return "Unbalanced braces"
            else:
                return "Invalid Python syntax"
        elif "indentation" in msg:
            return "Inconsistent indentation"
        else:
            return f"Syntax error: {error.message}"

    def _analyze_import_cause(self, error: DetectedError,
                              context: CodeContext) -> str:
        msg = error.message
        if "not found" in msg.lower():
            module = msg.split("'")[1] if "'" in msg else "unknown"
            return f"Module '{module}' is not installed"
        else:
            return f"Import error: {msg}"

    def _analyze_runtime_cause(
        self,
        error: DetectedError,
        context: CodeContext,
        stack_info: Dict
    ) -> str:
        exc_type = error.exception_type
        if exc_type == "NameError":
            return "Variable or function used before being defined"
        elif exc_type == "AttributeError":
            return "Attempting to access non-existent attribute"
        elif exc_type == "KeyError":
            return "Dictionary key does not exist"
        elif exc_type == "IndexError":
            return "List/array index out of bounds"
        elif exc_type == "ZeroDivisionError":
            return "Division by zero"
        elif exc_type == "TypeError":
            return "Operation on incompatible types"
        else:
            return f"Runtime error: {error.message}"

    def _analyze_type_cause(self, error: DetectedError,
                            context: CodeContext) -> str:
        return f"Type mismatch: {error.message}"

    def _analyze_logic_cause(self, error: DetectedError,
                             context: CodeContext) -> str:
        return f"Logic error in {context.function_name or 'code'}: {error.message}"

    def _identify_contributing_factors(
        self,
        error: DetectedError,
        context: CodeContext
    ) -> List[str]:
        factors = []
        if context.error_line:
            line = context.error_line.strip()
            if len(line) > 100:
                factors.append("Line is very long (>100 chars)")
            if line.count("(") > 3:
                factors.append("Deeply nested function calls")
            if "lambda" in line and len(line) > 50:
                factors.append("Complex lambda expression")
        return factors

    def _generate_solutions(
        self,
        error: DetectedError,
        context: CodeContext,
        probable_cause: str
    ) -> List[Dict]:
        solutions = []
        if error.suggested_fix:
            solutions.append({
                "rank": 1, "description": error.suggested_fix, "confidence": 0.8
            })
        if error.category == ErrorCategory.SYNTAX:
            solutions.extend(self._syntax_solutions(error, context))
        elif error.category == ErrorCategory.IMPORT:
            solutions.extend(self._import_solutions(error, context))
        elif error.category == ErrorCategory.RUNTIME:
            solutions.extend(self._runtime_solutions(error, context))
        solutions.sort(key=lambda x: x["confidence"], reverse=True)
        for i, sol in enumerate(solutions):
            sol["rank"] = i + 1
        return solutions

    def _syntax_solutions(self, error: DetectedError,
                          context: CodeContext) -> List[Dict]:
        return [
            {"rank": 2, "description": "Add missing colon", "confidence": 0.7},
            {"rank": 3, "description": "Fix indentation", "confidence": 0.6}
        ]

    def _import_solutions(self, error: DetectedError,
                          context: CodeContext) -> List[Dict]:
        module = error.message.split("'")[1] if "'" in error.message else "unknown"
        return [{"rank": 2, "description": f"pip install {module}",
                 "confidence": 0.9}]

    def _runtime_solutions(self, error: DetectedError,
                           context: CodeContext) -> List[Dict]:
        return [
            {"rank": 2, "description": "Add error handling", "confidence": 0.6},
            {"rank": 3, "description": "Add input validation", "confidence": 0.5}
        ]

    def _calculate_confidence(
        self,
        error: DetectedError,
        context: CodeContext,
        solutions: List[Dict]
    ) -> float:
        confidence = 0.5
        if context.error_line:
            confidence += 0.2
        if solutions:
            confidence += 0.2
        if error.category in [ErrorCategory.SYNTAX, ErrorCategory.IMPORT]:
            confidence += 0.1
        return min(1.0, confidence)

    def _find_enclosing_scope(
        self,
        code: str,
        line_number: int
    ) -> Tuple[Optional[str], Optional[str]]:
        try:
            tree = ast.parse(code)
            function_name = None
            class_name = None
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    if node.lineno <= line_number <= node.end_lineno:
                        function_name = node.name
                elif isinstance(node, ast.ClassDef):
                    if node.lineno <= line_number <= node.end_lineno:
                        class_name = node.name
            return function_name, class_name
        except BaseException:
            return None, None

    def _extract_variables_in_scope(
            self, code: str, line_number: int) -> List[str]:
        variables = []
        try:
            tree = ast.parse(code)
            for node in ast.walk(tree):
                if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
                    if node.lineno < line_number:
                        variables.append(node.id)
        except BaseException:
            pass
        return list(set(variables))

    def _matches_pattern(self, error: DetectedError, pattern: Dict) -> bool:
        keywords = pattern.get("keywords", [])
        msg = error.message.lower()
        return any(kw.lower() in msg for kw in keywords)

    def _load_error_patterns(self) -> Dict:
        return {
            "syntax": [
                {"description": "Missing colon",
                 "keywords": ["expected ':'", "invalid syntax"]},
                {"description": "Unclosed bracket/parenthesis",
                 "keywords": ["unexpected eof", "unmatched"]}
            ],
            "import": [
                {"description": "Module not installed",
                 "keywords": ["no module named", "not found"]}
            ]
        }
