#!/usr/bin/env python3
"""
Auto Fixer - Automatic code correction engine.

Applies fixes for detected errors using multiple strategies.
Part of Ziva's self-healing code repair system.
"""

import re
import subprocess
import logging
from typing import Optional, List
from dataclasses import dataclass

from core.error_detector import DetectedError, ErrorCategory
from core.root_cause_analyzer import RootCause


logger = logging.getLogger("AutoFixer")


@dataclass
class Fix:
    """
    Represents a code fix.

    Attributes:
        strategy: Fix strategy used
        description: Human-readable description
        original_code: Code before fix
        fixed_code: Code after fix
        confidence: Confidence in fix (0-1)
        applied: Whether fix was applied
        validated: Whether fix was validated
    """
    strategy: str
    description: str
    original_code: str
    fixed_code: str
    confidence: float
    applied: bool = False
    validated: bool = False


class AutoFixer:
    """
    Automatic code correction engine for Ziva.
    """

    def __init__(self):
        """Initialize auto-fixer."""
        logger.info("AutoFixer initialized for Ziva")

    def generate_fixes(
        self,
        root_cause: RootCause,
        code: str
    ) -> List[Fix]:
        """
        Generate possible fixes for an error.
        """
        error = root_cause.error
        fixes = []

        logger.info(f"Generating fixes for {error.category.value} error")

        if error.category == ErrorCategory.SYNTAX:
            fixes.extend(self._generate_syntax_fixes(error, code, root_cause))
        elif error.category == ErrorCategory.IMPORT:
            fixes.extend(self._generate_import_fixes(error, code, root_cause))
        elif error.category == ErrorCategory.TYPE:
            fixes.extend(self._generate_type_fixes(error, code, root_cause))
        elif error.category == ErrorCategory.RUNTIME:
            fixes.extend(self._generate_runtime_fixes(
                error, code, root_cause))
        elif error.category == ErrorCategory.LOGIC:
            fixes.extend(self._generate_logic_fixes(error, code, root_cause))

        fixes.sort(key=lambda f: f.confidence, reverse=True)
        logger.info(f"Generated {len(fixes)} possible fixes")
        return fixes

    def apply_fix(self, fix: Fix) -> str:
        """
        Apply a fix to code.
        """
        logger.info(f"Applying fix: {fix.description}")
        fix.applied = True
        return fix.fixed_code

    def _generate_syntax_fixes(
        self,
        error: DetectedError,
        code: str,
        root_cause: RootCause
    ) -> List[Fix]:
        """Generate fixes for syntax errors."""
        fixes = []
        lines = code.split("\n")

        if error.line_number is None:
            return fixes

        line_idx = error.line_number - 1
        if line_idx < len(lines):
            error_line = lines[line_idx]

        if "expected ':'" in error.message.lower(
        ) or "invalid syntax" in error.message.lower():
            if not error_line.rstrip().endswith(":"):
                fixed_line = error_line.rstrip() + ":"
                fixed_code = "\n".join(
                    lines[:line_idx] + [fixed_line] + lines[line_idx + 1:])

                fixes.append(Fix(
                    strategy="add_colon",
                    description="Add missing colon at end of line",
                    original_code=code,
                    fixed_code=fixed_code,
                    confidence=0.9
                ))

        if error_line.count("(") > error_line.count(")"):
            fixed_line = error_line + ")"
            fixed_code = "\n".join(
                lines[:line_idx] + [fixed_line] + lines[line_idx + 1:])

            fixes.append(Fix(
                strategy="close_parenthesis",
                description="Close unbalanced parenthesis",
                original_code=code,
                fixed_code=fixed_code,
                confidence=0.8
            ))

        if "indentation" in error.message.lower():
            if line_idx > 0:
                prev_line = lines[line_idx - 1]
                prev_indent = len(prev_line) - len(prev_line.lstrip())
                fixed_line = " " * prev_indent + error_line.lstrip()
                fixed_code = "\n".join(
                    lines[:line_idx] + [fixed_line] + lines[line_idx + 1:])
                fixes.append(Fix(
                    strategy="fix_indentation",
                    description="Fix indentation to match previous line",
                    original_code=code,
                    fixed_code=fixed_code,
                    confidence=0.7
                ))
        return fixes

    def _generate_import_fixes(
        self,
        error: DetectedError,
        code: str,
        root_cause: RootCause
    ) -> List[Fix]:
        """Generate fixes for import errors."""
        fixes = []
        module_match = re.search(r"Module '([^']+)' not found", error.message)
        if not module_match:
            module_match = re.search(
                r"No module named '([^']+)'", error.message)

        if module_match:
            module_name = module_match.group(1)
            fixes.append(Fix(
                strategy="pip_install",
                description=f"Install missing module: pip install {module_name}",
                original_code=code,
                fixed_code=code,
                confidence=0.95
            ))
            alternatives = self._get_alternative_module_names(module_name)
            for alt in alternatives:
                fixes.append(Fix(
                    strategy="alternative_import",
                    description=f"Try alternative module: {alt}",
                    original_code=code,
                    fixed_code=code.replace(module_name, alt),
                    confidence=0.5
                ))
        return fixes

    def _generate_type_fixes(
        self,
        error: DetectedError,
        code: str,
        root_cause: RootCause
    ) -> List[Fix]:
        """Generate fixes for type errors."""
        fixes = []
        if error.line_number:
            if "int" in error.message.lower() and "str" in error.message.lower():
                fixes.append(Fix(
                    strategy="type_conversion",
                    description="Add type conversion (str/int)",
                    original_code=code,
                    fixed_code=code,
                    confidence=0.6
                ))
        return fixes

    def _generate_runtime_fixes(
        self,
        error: DetectedError,
        code: str,
        root_cause: RootCause
    ) -> List[Fix]:
        """Generate fixes for runtime errors."""
        fixes = []
        exc_type = error.exception_type
        if error.line_number:
            lines = code.split("\n")
            line_idx = error.line_number - 1
            indent = self._get_line_indent(lines[line_idx])
            error_line = lines[line_idx]
            try_block = [
                " " * indent + "try:",
                " " * (indent + 4) + error_line.lstrip(),
                " " * indent + f"except {exc_type or 'Exception'} as e:",
                " " * (indent + 4) + "logger.error(f'Error: {e}')",
                " " * (indent + 4) + "pass"
            ]
            fixed_lines = lines[:line_idx] + try_block + lines[line_idx + 1:]
            fixed_code = "\n".join(fixed_lines)
            fixes.append(Fix(
                strategy="add_error_handling",
                description=f"Add try/except for {exc_type}",
                original_code=code,
                fixed_code=fixed_code,
                confidence=0.7
            ))
        if exc_type in ["ValueError", "TypeError", "KeyError", "IndexError"]:
            fixes.append(Fix(
                strategy="add_validation",
                description="Add input validation",
                original_code=code,
                fixed_code=code,
                confidence=0.6
            ))
        return fixes

    def _generate_logic_fixes(
        self,
        error: DetectedError,
        code: str,
        root_cause: RootCause
    ) -> List[Fix]:
        """Generate fixes for logic errors."""
        fixes = [Fix(
            strategy="llm_guided_fix",
            description="Use LLM to fix logic error",
            original_code=code,
            fixed_code=code,
            confidence=0.5
        )]
        return fixes

    def fix_syntax_error(self, error: DetectedError,
                         code: str) -> Optional[str]:
        """
        Quick syntax error fix.
        """
        from core.root_cause_analyzer import RootCauseAnalyzer

        analyzer = RootCauseAnalyzer()
        context = analyzer.extract_code_context(error, code)
        root_cause = type('RootCause', (), {
            'error': error,
            'context': context,
            'probable_cause': '',
            'suggested_solutions': []
        })()
        fixes = self._generate_syntax_fixes(error, code, root_cause)
        if fixes:
            return fixes[0].fixed_code
        return None

    def fix_import_error(self, error: DetectedError) -> bool:
        """
        Fix import error by installing module.
        """
        module_match = re.search(r"Module '([^']+)' not found", error.message)
        if not module_match:
            module_match = re.search(r"'([^']+)'", error.message)
        if module_match:
            module_name = module_match.group(1)
            try:
                logger.info(f"Installing module: {module_name}")
                result = subprocess.run(
                    ["pip", "install", module_name],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                if result.returncode == 0:
                    logger.info(f"Successfully installed {module_name}")
                    return True
                else:
                    logger.error(
                        f"Failed to install {module_name}: {result.stderr}")
                    return False
            except Exception as e:
                logger.error(f"Error installing module: {e}")
                return False
        return False

    def _get_alternative_module_names(self, module: str) -> List[str]:
        """Get alternative module names."""
        alternatives = {
            "cv2": ["opencv-python"],
            "PIL": ["Pillow"],
            "sklearn": ["scikit-learn"],
            "yaml": ["pyyaml"]
        }
        return alternatives.get(module, [])

    def _get_line_indent(self, line: str) -> int:
        """Get indentation level of a line."""
        return len(line) - len(line.lstrip())