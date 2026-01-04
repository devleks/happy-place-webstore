/**
 * PWA Integration Test Suite
 * Tests core functionality without browser automation
 */

const axios = require('axios');

const API_URL = 'http://localhost:3003';
const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  cyan: '\x1b[36m'
};

let testResults = {
  passed: 0,
  failed: 0,
  total: 0,
  failures: []
};

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

function logTest(name, passed, error = null) {
  testResults.total++;
  if (passed) {
    testResults.passed++;
    log(`✅ ${name}`, 'green');
  } else {
    testResults.failed++;
    testResults.failures.push({ name, error });
    log(`❌ ${name}`, 'red');
    if (error) {
      log(`   Error: ${error}`, 'red');
    }
  }
}

async function testServerRunning() {
  try {
    const response = await axios.get(API_URL, { timeout: 5000 });
    logTest('Server is running and responding', response.status === 200);
    return true;
  } catch (error) {
    logTest('Server is running and responding', false, error.message);
    return false;
  }
}

async function testHTMLLoads() {
  try {
    const response = await axios.get(API_URL);
    const hasHTML = response.data.includes('<!DOCTYPE html>') || response.data.includes('<html');
    const hasRoot = response.data.includes('id="root"');
    logTest('HTML page loads with root element', hasHTML && hasRoot);
  } catch (error) {
    logTest('HTML page loads with root element', false, error.message);
  }
}

async function testManifestExists() {
  try {
    const response = await axios.get(`${API_URL}/manifest.json`);
    const manifest = response.data;
    const hasName = manifest.name || manifest.short_name;
    logTest('PWA manifest exists and is valid', hasName !== undefined);
  } catch (error) {
    logTest('PWA manifest exists and is valid', false, error.message);
  }
}

async function testStaticAssets() {
  try {
    const response = await axios.get(`${API_URL}/static/js/bundle.js`, { 
      timeout: 5000,
      validateStatus: (status) => status < 500 
    });
    logTest('Static JavaScript bundle is accessible', response.status === 200);
  } catch (error) {
    logTest('Static JavaScript bundle is accessible', false, error.message);
  }
}

async function testReactAppCompilation() {
  try {
    const response = await axios.get(API_URL);
    const html = response.data;
    
    const hasReactRoot = html.includes('id="root"');
    const hasScripts = html.includes('<script') || html.includes('src="/static/js');
    
    logTest('React app is compiled and bundled', hasReactRoot && hasScripts);
  } catch (error) {
    logTest('React app is compiled and bundled', false, error.message);
  }
}

async function testServiceWorkerFile() {
  try {
    const response = await axios.get(`${API_URL}/service-worker.js`, {
      validateStatus: (status) => status < 500
    });
    logTest('Service Worker file exists', response.status === 200);
  } catch (error) {
    logTest('Service Worker file exists', false, error.message);
  }
}

async function runTests() {
  log('\n🧪 PWA Integration Test Results\n', 'blue');
  log('═'.repeat(60), 'blue');
  
  log('\n📡 Server Tests:', 'cyan');
  const serverRunning = await testServerRunning();
  
  if (!serverRunning) {
    log('\n❌ Server is not responding. Cannot continue tests.', 'red');
    log('   Please ensure the server is running with: npm start', 'yellow');
    process.exit(1);
  }
  
  await testHTMLLoads();
  await testReactAppCompilation();
  
  log('\n📦 Asset Tests:', 'cyan');
  await testStaticAssets();
  await testManifestExists();
  await testServiceWorkerFile();
  
  log('\n═'.repeat(60), 'blue');
  log('\n📊 Test Summary:', 'blue');
  log(`   Total Tests: ${testResults.total}`, 'cyan');
  log(`   Passed: ${testResults.passed}`, 'green');
  log(`   Failed: ${testResults.failed}`, testResults.failed > 0 ? 'red' : 'green');
  
  if (testResults.failures.length > 0) {
    log('\n❌ Failed Tests:', 'red');
    testResults.failures.forEach(failure => {
      log(`   • ${failure.name}`, 'red');
      log(`     ${failure.error}`, 'yellow');
    });
  }
  
  const passRate = ((testResults.passed / testResults.total) * 100).toFixed(1);
  log(`\n📈 Pass Rate: ${passRate}%`, passRate >= 80 ? 'green' : 'red');
  
  if (testResults.failed === 0) {
    log('\n✅ All automated tests PASSED!', 'green');
    log('\n📋 Next Steps:', 'cyan');
    log('   1. Open http://localhost:3003 in browser', 'cyan');
    log('   2. Test login with: cashier1@happyplace.co.ke / cashier123', 'cyan');
    log('   3. Verify IndexedDB initialization in console', 'cyan');
    log('   4. Test transaction creation', 'cyan');
  } else {
    log('\n⚠️  Some tests failed. PWA may not be working correctly.', 'yellow');
  }
  
  log('\n═'.repeat(60), 'blue');
  
  process.exit(testResults.failed > 0 ? 1 : 0);
}

runTests().catch(error => {
  log(`\n💥 Test suite crashed: ${error.message}`, 'red');
  console.error(error);
  process.exit(1);
});
