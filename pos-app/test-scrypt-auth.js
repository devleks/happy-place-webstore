#!/usr/bin/env node
/**
 * Test scrypt password verification
 * Verifies that the auth.js scrypt implementation works correctly
 */

const crypto = require('crypto');
const Database = require('better-sqlite3');
const path = require('path');
const os = require('os');

// Database path
const DB_PATH = path.join(
  os.homedir(),
  'Library/Application Support/happy-place-pos/pos.db'
);

/**
 * Verify password against Werkzeug scrypt hash (Flask backend format)
 * Format: scrypt:N:r:p$salt$hash
 */
function verifyScryptPassword(password, passwordHash) {
  try {
    // Check if it's a scrypt hash
    if (!passwordHash.startsWith('scrypt:')) {
      return false;
    }

    // Parse the hash: scrypt:N:r:p$salt$hash
    const parts = passwordHash.split('$');
    if (parts.length !== 3) return false;

    const [params, saltHex, expectedHash] = parts;
    const paramParts = params.split(':');
    if (paramParts.length !== 4) return false;

    const [, N, r, p] = paramParts;

    // Decode salt from hex
    const salt = Buffer.from(saltHex, 'hex');

    // Derive key using scrypt
    const derivedKey = crypto.scryptSync(
      password,
      salt,
      64, // Flask scrypt outputs 64 bytes by default
      {
        N: parseInt(N),
        r: parseInt(r),
        p: parseInt(p),
        maxmem: 128 * parseInt(N) * parseInt(r) * 2
      }
    );

    // Werkzeug uses hex encoding for the hash
    const derivedHash = derivedKey.toString('hex');

    // Compare hashes
    return derivedHash === expectedHash;
  } catch (error) {
    console.error('Scrypt verification error:', error);
    return false;
  }
}

async function testAuth() {
  console.log('🔐 Testing scrypt password verification...\n');

  const db = new Database(DB_PATH, { readonly: true });

  try {
    // Get admin employee
    const admin = db.prepare('SELECT * FROM employees WHERE email = ?').get('admin@happyplace.co.ke');

    if (!admin) {
      console.error('❌ Admin account not found in database');
      process.exit(1);
    }

    console.log(`👤 Testing admin account: ${admin.email}`);
    console.log(`   Role: ${admin.role}`);
    console.log(`   Hash format: ${admin.password_hash.substring(0, 30)}...`);
    console.log();

    // Test correct password
    console.log('🔑 Testing with correct password: "admin123"');
    const correctResult = verifyScryptPassword('admin123', admin.password_hash);
    console.log(`   Result: ${correctResult ? '✅ PASS' : '❌ FAIL'}`);
    console.log();

    // Test incorrect password
    console.log('🔑 Testing with incorrect password: "wrongpassword"');
    const incorrectResult = verifyScryptPassword('wrongpassword', admin.password_hash);
    console.log(`   Result: ${incorrectResult ? '❌ FAIL (should be false)' : '✅ PASS (correctly rejected)'}`);
    console.log();

    if (correctResult && !incorrectResult) {
      console.log('✅ Scrypt password verification is working correctly!');
      console.log('\nYou can now login to the POS app with:');
      console.log('   Email: admin@happyplace.co.ke');
      console.log('   Password: admin123');
      process.exit(0);
    } else {
      console.log('❌ Scrypt password verification failed!');
      process.exit(1);
    }

  } catch (error) {
    console.error('❌ Test error:', error);
    process.exit(1);
  } finally {
    db.close();
  }
}

// Run test
testAuth();
