// websocket_test.js
// Simple test to debug WebSocket connection issues
// Run this in browser console: http://localhost:3000

function testWebSocketConnection() {
  console.log('🔍 Testing WebSocket connection to BrontoBox backend...');
  
  // Test 1: Check if backend is running
  console.log('\n1️⃣ Testing HTTP connection...');
  fetch('http://127.0.0.1:8000/health')
    .then(response => response.json())
    .then(data => {
      console.log('✅ Backend HTTP connection: OK');
      console.log('📊 Backend status:', data);
      
      // Test 2: Try WebSocket connection
      console.log('\n2️⃣ Testing WebSocket connection...');
      testWebSocket();
    })
    .catch(error => {
      console.error('❌ Backend HTTP connection: FAILED');
      console.error('💡 Solution: Start backend with: python brontobox_api.py');
      console.error('Error details:', error);
    });
}

function testWebSocket() {
  const ws = new WebSocket('ws://127.0.0.1:8000/ws');
  let connectionTimer = null;
  
  // Set a timeout for connection
  connectionTimer = setTimeout(() => {
    console.error('❌ WebSocket connection: TIMEOUT (10 seconds)');
    console.error('💡 Possible causes:');
    console.error('   - Backend not running on port 8000');
    console.error('   - Firewall blocking WebSocket connections');
    console.error('   - WebSocket endpoint not properly implemented');
    ws.close();
  }, 10000);
  
  ws.onopen = function(event) {
    clearTimeout(connectionTimer);
    console.log('✅ WebSocket connection: SUCCESSFUL');
    console.log('📡 Connection event:', event);
    
    // Test sending a message
    console.log('\n3️⃣ Testing WebSocket message...');
    ws.send(JSON.stringify({ type: 'test', message: 'Hello from frontend!' }));
  };
  
  ws.onmessage = function(event) {
    console.log('📨 WebSocket message received:', event.data);
    try {
      const data = JSON.parse(event.data);
      console.log('📋 Parsed message:', data);
    } catch (e) {
      console.log('📝 Raw message (not JSON):', event.data);
    }
  };
  
  ws.onerror = function(error) {
    clearTimeout(connectionTimer);
    console.error('❌ WebSocket error:', error);
    console.error('🔧 Debugging info:');
    console.error('   - WebSocket URL: ws://127.0.0.1:8000/ws');
    console.error('   - Ready State:', ws.readyState);
    console.error('   - Ready State meaning:');
    console.error('     0 = CONNECTING, 1 = OPEN, 2 = CLOSING, 3 = CLOSED');
  };
  
  ws.onclose = function(event) {
    clearTimeout(connectionTimer);
    console.log('🔌 WebSocket closed');
    console.log('📊 Close details:');
    console.log('   - Code:', event.code);
    console.log('   - Reason:', event.reason);
    console.log('   - Clean close:', event.wasClean);
    
    // Explain common close codes
    const closeCodes = {
      1000: 'Normal closure',
      1001: 'Going away',
      1002: 'Protocol error',
      1003: 'Unsupported data',
      1006: 'Abnormal closure (no close frame)',
      1011: 'Server error',
      1012: 'Service restart',
      1013: 'Try again later'
    };
    
    console.log('💡 Close code meaning:', closeCodes[event.code] || 'Unknown code');
    
    if (event.code !== 1000) {
      console.error('⚠️ Unexpected closure - this might cause app refresh issues');
    }
  };
  
  // Keep connection alive for testing
  setTimeout(() => {
    if (ws.readyState === WebSocket.OPEN) {
      console.log('🔌 Closing test WebSocket connection...');
      ws.close(1000, 'Test completed');
    }
  }, 5000);
}

// Auto-run test
console.log('🚀 Starting BrontoBox WebSocket diagnostics...');
testWebSocketConnection();

// Export for manual use
window.testBrontoBoxWebSocket = testWebSocketConnection;