#!/usr/bin/env node

import fs from 'fs';
import { JSDOM } from 'jsdom';
import mermaid from 'mermaid';
import createDOMPurify from 'dompurify';

const dom = new JSDOM('<!DOCTYPE html><body></body>');
global.window = dom.window;
global.document = dom.window.document;
global.navigator = dom.window.navigator;
const DOMPurify = createDOMPurify(dom.window);
global.DOMPurify = DOMPurify;
dom.window.DOMPurify = DOMPurify;

async function validateMermaid(filePath) {
  try {
    const content = fs.readFileSync(filePath, 'utf-8');
    mermaid.initialize({ startOnLoad: false, logLevel: 'error', securityLevel: 'loose' });
    await mermaid.parse(content);
    console.log(`✅ VALID: ${filePath}`);
    return true;
  } catch (error) {
    console.error(`❌ INVALID: ${filePath}`);
    console.error(`   Error: ${error.message}`);
    if (error.hash && error.hash.line) {
      console.error(`   Line ${error.hash.line}: ${error.hash.text || ''}`);
    }
    return false;
  }
}

const filePath = process.argv[2];

if (!filePath) {
  console.error('Usage: node validate-mermaid.js <diagram.mmd>');
  process.exit(1);
}

if (!fs.existsSync(filePath)) {
  console.error(`File not found: ${filePath}`);
  process.exit(1);
}

validateMermaid(filePath)
  .then(isValid => process.exit(isValid ? 0 : 1))
  .catch(err => {
    console.error(`Unexpected error: ${err.message}`);
    process.exit(1);
  });

