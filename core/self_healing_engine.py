#!/usr/bin/env python3
"""
Self-Healing Engine - Central orchestrator for Ziva's auto-repair system.
"""

import logging
import time
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from core.error_detector import ErrorDetector, DetectedError, ErrorSeverity
from core.root_cause_analyzer import RootCauseAnalyzer, RootCause
from core.auto_fixer import AutoFixer, Fix


logger = logging.getLogger("SelfHealingEngine")


@dataclass
class RepairAttempt:
    """
    Record of a repair attempt.
    """
    attempt_number: int
    error: DetectedError
    root_cause: RootCause
    fix_applied: Optional[Fix]
    success: bool
    validation_passed: bool
    duration_ms: int
    timestamp: datetime


@dataclass
class RepairResult:
    """
    Result of complete repair workflow.
    """
    success: bool
    original_code: str
    repaired_code: str
    errors_fixed: List[DetectedError]
    attempts: List[RepairAttempt]
    total_duration_ms: int
    rollback_performed: bool


class SelfHealingEngine:
    """
    Central orchestrator for Ziva's self-healing code repair system.
    """

    def __init__(
        self,
        max_attempts: int = 5,
        timeout_seconds: int = 300
    ):
        """
        Initialize self-healing engine.
        """
        self.detector = ErrorDetector()
        self.analyzer = RootCauseAnalyzer()
        self.fixer = AutoFixer()

        self.max_attempts = max_attempts
        self.timeout_seconds = timeout_seconds

        logger.info(
            f"SelfHealingEngine initialized (max_attempts={max_attempts}, "
            f"timeout={timeout_seconds}s)")

    def repair_code(
        self,
        code: str,
        run_tests: bool = False,
        test_cases: Optional[List[Dict]] = None
    ) -> RepairResult:
        """
        Attempt to repair code automatically.
        """
        start_time = time.time()
        logger.info("Starting self-healing repair workflow")

        original_code = code
        current_code = code
        attempts = []
        errors_fixed = []
        rollback_performed = False

        try:
            for attempt_num in range(1, self.max_attempts + 1):
                if (time.time() - start_time) > self.timeout_seconds:
                    logger.warning(
                        f"Repair timeout after {self.timeout_seconds}s")
                    break
                logger.info(f"Repair attempt {attempt_num}/{self.max_attempts}")
                errors = self.detector.detect_all_errors(
                    current_code,
                    run_tests=run_tests,
                    test_cases=test_cases
                )
                if not errors:
                    logger.info("No errors detected, repair successful!")
                    break
                error = self._select_error_to_fix(errors)
                logger.info(
                    f"Fixing {error.category.value} error: {error.message}")
                attempt_start = time.time()
                root_cause = self.analyzer.analyze(error, current_code)
                fixes = self.fixer.generate_fixes(root_cause, current_code)
                if not fixes:
                    logger.warning("No fixes generated for error")
                    attempts.append(RepairAttempt(
                        attempt_number=attempt_num,
                        error=error,
                        root_cause=root_cause,
                        fix_applied=None,
                        success=False,
                        validation_passed=False,
                        duration_ms=int((time.time() - attempt_start) * 1000),
                        timestamp=datetime.now()
                    ))
                    continue
                fix_succeeded = False
                for fix in fixes:
                    logger.info(f"Trying fix: {fix.description}")
                    if fix.strategy == "pip_install":
                        if self.fixer.fix_import_error(error):
                            new_errors = self.detector.detect_all_errors(
                                current_code)
                            if len(new_errors) < len(errors):
                                fix_succeeded = True
                                errors_fixed.append(error)
                                break
                        continue
                    fixed_code = self.fixer.apply_fix(fix)
                    validation_passed, is_regression = self._validate_fix(
                        original_code,
                        current_code,
                        fixed_code,
                        error
                    )
                    if is_regression:
                        logger.warning("Fix caused regression, skipping")
                        continue
                    if validation_passed:
                        logger.info("Fix validated successfully")
                        current_code = fixed_code
                        errors_fixed.append(error)
                        fix_succeeded = True
                        attempts.append(RepairAttempt(
                            attempt_number=attempt_num,
                            error=error,
                            root_cause=root_cause,
                            fix_applied=fix,
                            success=True,
                            validation_passed=True,
                            duration_ms=int(
                                (time.time() - attempt_start) * 1000),
                            timestamp=datetime.now()
                        ))
                        break
                if not fix_succeeded:
                    logger.warning(
                        f"All fixes failed for attempt {attempt_num}")
                    attempts.append(RepairAttempt(
                        attempt_number=attempt_num,
                        error=error,
                        root_cause=root_cause,
                        fix_applied=fixes[0] if fixes else None,
                        success=False,
                        validation_passed=False,
                        duration_ms=int((time.time() - attempt_start) * 1000),
                        timestamp=datetime.now()
                    ))
            final_errors = self.detector.detect_all_errors(current_code)
            success = len(final_errors) == 0
            if not success and len(final_errors) > len(
                    self.detector.detect_all_errors(original_code)):
                logger.warning("Final state worse than original, rolling back")
                current_code = original_code
                rollback_performed = True
            total_duration = int((time.time() - start_time) * 1000)
            result = RepairResult(
                success=success,
                original_code=original_code,
                repaired_code=current_code,
                errors_fixed=errors_fixed,
                attempts=attempts,
                total_duration_ms=total_duration,
                rollback_performed=rollback_performed
            )
            logger.info(
                f"Repair completed: success={success}, errors_fixed="
                f"{len(errors_fixed)}, duration={total_duration}ms")
            return result
        except Exception as e:
            logger.error(f"Error during repair: {e}")
            return RepairResult(
                success=False,
                original_code=original_code,
                repaired_code=original_code,
                errors_fixed=[],
                attempts=attempts,
                total_duration_ms=int((time.time() - start_time) * 1000),
                rollback_performed=False
            )

    def detect_errors(
        self,
        code: str,
        run_tests: bool = False,
        test_cases: Optional[List[Dict]] = None
    ) -> List[DetectedError]:
        """
        Detect all errors in code.
        """
        return self.detector.detect_all_errors(code, run_tests, test_cases)

    def analyze_root_cause(
        self,
        error: DetectedError,
        code: str
    ) -> RootCause:
        """
        Analyze root cause of an error.
        """
        return self.analyzer.analyze(error, code)

    def generate_fixes(
        self,
        root_cause: RootCause,
        code: str
    ) -> List[Fix]:
        """
        Generate possible fixes for an error.
        """
        return self.fixer.generate_fixes(root_cause, code)

    def apply_fix(self, fix: Fix, code: str) -> str:
        """
        Apply a fix to code.
        """
        return self.fixer.apply_fix(fix)

    def validate_fix(
        self,
        original_code: str,
        fixed_code: str,
        original_error: DetectedError
    ) -> bool:
        """
        Validate that a fix resolved the error.
        """
        validation_passed, _ = self._validate_fix(
            original_code,
            original_code,
            fixed_code,
            original_error
        )
        return validation_passed

    def rollback(self, code: str, backup: str) -> str:
        """
        Rollback to backup code.
        """
        logger.info("Rolling back to backup code")
        return backup

    def _select_error_to_fix(self, errors: List[DetectedError]) -> DetectedError:
        """
        Select which error to fix first.
        """
        critical = [e for e in errors if e.severity == ErrorSeverity.CRITICAL]
        if critical:
            return critical[0]
        high = [e for e in errors if e.severity == ErrorSeverity.HIGH]
        if high:
            return high[0]
        return errors[0]

    def _validate_fix(
        self,
        original_code: str,
        before_fix_code: str,
        after_fix_code: str,
        original_error: DetectedError
    ) -> Tuple[bool, bool]:
        """
        Validate a fix.
        """
        try:
            errors_after = self.detector.detect_all_errors(after_fix_code)
            original_error_gone = not any(
                e.category == original_error.category and
                e.message == original_error.message
                for e in errors_after
            )
            errors_before = self.detector.detect_all_errors(before_fix_code)
            new_critical_errors = [
                e for e in errors_after
                if e.severity == ErrorSeverity.CRITICAL and
                not any(
                    eb.category == e.category and eb.message == e.message
                    for eb in errors_before
                )
            ]
            is_regression = len(new_critical_errors) > 0
            validation_passed = original_error_gone and not is_regression
            return validation_passed, is_regression
        except Exception as e:
            logger.error(f"Error during validation: {e}")
            return False, False