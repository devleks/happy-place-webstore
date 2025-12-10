#!/bin/bash

# Run all POS tests and document results
# Captures output and generates report

set -e

echo "🧪 Running POS Test Suite..."
echo ""

# Navigate to pos-app
cd "$(dirname "$0")/../../pos-app"

# Create results directory
mkdir -p ../pos_test/results

# Generate timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
RESULT_FILE="../pos_test/results/test-run-$TIMESTAMP.md"

echo "📝 Results will be saved to: $RESULT_FILE"
echo ""

# Start result file
cat > "$RESULT_FILE" << EOF
# Test Execution Report

**Date:** $(date)  
**Timestamp:** $TIMESTAMP  
**Environment:** $(uname -s)

---

## Test Execution

EOF

# Run tests and capture output
echo "Running tests..."
npm test -- --coverage --verbose 2>&1 | tee -a "$RESULT_FILE"

# Add summary
cat >> "$RESULT_FILE" << EOF

---

## Summary

Test execution completed at $(date)

EOF

echo ""
echo "✅ Test execution complete!"
echo "📄 Results saved to: $RESULT_FILE"
echo ""
