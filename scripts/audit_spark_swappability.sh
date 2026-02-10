#!/bin/bash
# Spark Swappability Audit Script
# Enforces SPARK_SWAPPABLE_INVARIANT via grep checks
# Authority: docs/doctrine/SPARK_SWAPPABLE_INVARIANT.md (STOP-001 through STOP-005)
# Usage: ./scripts/audit_spark_swappability.sh

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_ROOT"

echo "============================================"
echo "SPARK SWAPPABILITY AUDIT"
echo "Authority: SPARK_SWAPPABLE_INVARIANT.md"
echo "Date: $(date +%Y-%m-%d)"
echo "============================================"
echo ""

VIOLATIONS=0

# STOP-001: Hard-Coded Model Selection
echo "[CHECK-001] Scanning for hard-coded model paths..."
HARDCODED_PATHS=$(grep -r 'model_path.*=.*".*\.gguf"' aidm/ --include="*.py" 2>/dev/null || true)
if [ -n "$HARDCODED_PATHS" ]; then
    echo "❌ FAIL: Hard-coded model paths detected (STOP-001 violation)"
    echo "$HARDCODED_PATHS"
    VIOLATIONS=$((VIOLATIONS + 1))
else
    echo "✅ PASS: No hard-coded model paths"
fi
echo ""

# STOP-001: Hard-Coded Provider Names
echo "[CHECK-002] Scanning for hard-coded provider names..."
HARDCODED_PROVIDERS=$(grep -r 'provider.*=.*"llamacpp"\|provider.*=.*"transformers"\|provider.*=.*"openai"' aidm/ --include="*.py" 2>/dev/null | grep -v "# " | grep -v '"""' || true)
if [ -n "$HARDCODED_PROVIDERS" ]; then
    echo "❌ FAIL: Hard-coded provider names detected (STOP-001 violation)"
    echo "$HARDCODED_PROVIDERS"
    VIOLATIONS=$((VIOLATIONS + 1))
else
    echo "✅ PASS: No hard-coded provider names"
fi
echo ""

# STOP-001: Hard-Coded Model Names
echo "[CHECK-003] Scanning for hard-coded model names in code..."
HARDCODED_MODELS=$(grep -r '"mistral-7b\|"phi-2\|"llama\|"gpt-' aidm/ --include="*.py" 2>/dev/null | grep -v "# " | grep -v '"""' | grep -v "test_" || true)
if [ -n "$HARDCODED_MODELS" ]; then
    echo "⚠️  WARNING: Model names found in source (verify they're in config, not hard-coded)"
    echo "$HARDCODED_MODELS"
    echo "   (Review manually: model names should only appear in models.yaml, not source code)"
else
    echo "✅ PASS: No model names in source code"
fi
echo ""

# STOP-002: Capability Assumption Without Validation
echo "[CHECK-004] Scanning for capability assumptions without checks..."
CAPABILITY_VIOLATIONS=$(grep -r 'json_mode=True\|streaming=True' aidm/ --include="*.py" 2>/dev/null | grep -v "if.*supports" | grep -v "test_" || true)
if [ -n "$CAPABILITY_VIOLATIONS" ]; then
    echo "❌ FAIL: Capability usage without validation (STOP-002 violation)"
    echo "$CAPABILITY_VIOLATIONS"
    VIOLATIONS=$((VIOLATIONS + 1))
else
    echo "✅ PASS: All capability usage properly validated"
fi
echo ""

# STOP-003: SPARK Bypasses Lens/Box Validation
echo "[CHECK-005] Scanning for direct SPARK output usage..."
DIRECT_SPARK_OUTPUT=$(grep -r 'return spark\.generate\|return.*spark\.generate' aidm/ --include="*.py" 2>/dev/null | grep -v "test_" || true)
if [ -n "$DIRECT_SPARK_OUTPUT" ]; then
    echo "❌ FAIL: Direct SPARK output without LENS filtering (STOP-003 violation)"
    echo "$DIRECT_SPARK_OUTPUT"
    VIOLATIONS=$((VIOLATIONS + 1))
else
    echo "✅ PASS: No direct SPARK output bypass"
fi
echo ""

# STOP-003: SPARK Mechanical Claims
echo "[CHECK-006] Scanning for SPARK mechanical claims..."
SPARK_MECHANICS=$(grep -r 'spark.*damage\|spark.*hit\|spark.*legal\|spark.*roll' aidm/ --include="*.py" 2>/dev/null | grep -v "test_" | grep -v "# " || true)
if [ -n "$SPARK_MECHANICS" ]; then
    echo "⚠️  WARNING: SPARK referenced with mechanical terms (verify BOX computes mechanics, not SPARK)"
    echo "$SPARK_MECHANICS"
    echo "   (Review manually: BOX must compute mechanics, SPARK only generates narration)"
else
    echo "✅ PASS: No SPARK mechanical claims detected"
fi
echo ""

# Summary
echo "============================================"
echo "AUDIT SUMMARY"
echo "============================================"
if [ $VIOLATIONS -eq 0 ]; then
    echo "✅ ALL CHECKS PASSED"
    echo "Spark swappability invariant preserved."
    exit 0
else
    echo "❌ $VIOLATIONS VIOLATION(S) DETECTED"
    echo "Spark swappability invariant VIOLATED."
    echo "Remediation required before PR approval."
    exit 1
fi
