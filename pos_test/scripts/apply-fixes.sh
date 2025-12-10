#!/bin/bash

# Apply all test fixes to pos-app
# Run this script to prepare for testing

set -e  # Exit on error

echo "🔧 Applying test fixes to pos-app..."
echo ""

# Navigate to pos-app directory
cd "$(dirname "$0")/../../pos-app"

echo "📁 Current directory: $(pwd)"
echo ""

# Create necessary directories
echo "Creating directories..."
mkdir -p src
mkdir -p __tests__/setup
mkdir -p __tests__/mocks

# Copy configuration files
echo "✅ Copying jest.config.js..."
cp ../pos_test/fixes/jest.config.js ./

echo "✅ Copying babel.config.js..."
cp ../pos_test/fixes/babel.config.js ./

echo "✅ Copying setupTests.js..."
cp ../pos_test/fixes/setupTests.js ./src/

echo "✅ Copying mockDatabase.js..."
cp ../pos_test/fixes/mockDatabase.js ./__tests__/setup/

# Create mock files
echo "✅ Creating electron mock..."
cat > __tests__/mocks/electron.js << 'EOF'
module.exports = {
  app: {
    getPath: jest.fn(() => '/tmp/test'),
    on: jest.fn()
  },
  ipcMain: {
    handle: jest.fn(),
    on: jest.fn()
  }
};
EOF

echo "✅ Creating file mock..."
cat > __tests__/mocks/fileMock.js << 'EOF'
module.exports = 'test-file-stub';
EOF

# Install dependencies
echo ""
echo "📦 Installing dependencies..."
npm install --save-dev @babel/preset-env @babel/preset-react identity-obj-proxy

echo ""
echo "✅ All fixes applied successfully!"
echo ""
echo "Next steps:"
echo "1. Run: npm test"
echo "2. Or run: npm run test:unit"
echo "3. Or run: npm run test:coverage"
echo ""
