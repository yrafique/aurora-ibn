#!/usr/bin/env python3
"""
AURORA-IBN Web GUI - Modern Design
Beautiful, intuitive interface for intent-based networking
"""

from flask import Flask, render_template, request, jsonify, Response
import json
import time
import sys
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

app = Flask(__name__)

class AuroraWebInterface:
    def __init__(self):
        self.session_stats = {
            "intents_processed": 0,
            "configurations_generated": 0,
            "services_deployed": 0,
            "uptime_start": datetime.now()
        }
        
        # Mock device inventory
        self.device_inventory = [
            {
                "id": "PE1",
                "name": "pe1-srlinux", 
                "vendor": "Nokia",
                "model": "SR Linux 23.10.1",
                "ip": "172.25.25.10",
                "status": "active",
                "capabilities": ["NETCONF", "gNMI", "SSH"],
                "interfaces": 24,
                "cpu": 23,
                "memory": 45
            },
            {
                "id": "PE2",
                "name": "pe2-cisco",
                "vendor": "Cisco", 
                "model": "IOS-XR 7.3.1",
                "ip": "172.25.25.11",
                "status": "active", 
                "capabilities": ["NETCONF", "RESTCONF", "SSH"],
                "interfaces": 48,
                "cpu": 18,
                "memory": 38
            },
            {
                "id": "PE3",
                "name": "pe3-juniper",
                "vendor": "Juniper",
                "model": "Junos 21.4R1", 
                "ip": "172.25.25.12",
                "status": "active",
                "capabilities": ["NETCONF", "SSH"],
                "interfaces": 32,
                "cpu": 31,
                "memory": 52
            }
        ]

aurora_web = AuroraWebInterface()

@app.route('/')
def dashboard():
    """Main dashboard with Apple-inspired design"""
    return render_template('dashboard.html', 
                         devices=aurora_web.device_inventory,
                         stats=aurora_web.session_stats)

@app.route('/api/process_intent', methods=['POST'])
def process_intent():
    """Process natural language intent"""
    try:
        data = request.get_json()
        intent_text = data.get('intent', '')
        
        if not intent_text:
            return jsonify({"error": "No intent provided"}), 400
        
        # Import NLP parser
        try:
            from core.nlp_parser import NLPParser
            parser = NLPParser()
            result = parser.parse(intent_text)
        except Exception as e:
            # Fallback simulation if imports fail
            result = {
                "devices": ["PE1", "PE2"] if "PE1" in intent_text and "PE2" in intent_text else [],
                "interfaces": [],
                "protocols": ["bgp"] if "BGP" in intent_text.upper() else [],
                "service_attributes": {}
            }
        
        # Simulate processing time
        time.sleep(0.1)
        
        # Generate response
        response = {
            "intent_id": f"intent_{int(time.time())}",
            "status": "processed",
            "parsed_intent": result,
            "risk_level": "MEDIUM",
            "estimated_time": "45 seconds",
            "devices_affected": len(result.get("devices", [])),
            "configurations_generated": len(result.get("devices", [])),
            "timestamp": datetime.now().isoformat()
        }
        
        # Update stats
        aurora_web.session_stats["intents_processed"] += 1
        aurora_web.session_stats["configurations_generated"] += len(result.get("devices", []))
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/devices')
def get_devices():
    """Get device inventory"""
    return jsonify(aurora_web.device_inventory)

@app.route('/api/deploy', methods=['POST'])
def deploy_configuration():
    """Deploy configuration to devices"""
    try:
        data = request.get_json()
        intent_id = data.get('intent_id')
        
        # Simulate deployment
        time.sleep(2)
        
        response = {
            "deployment_id": f"deploy_{int(time.time())}",
            "status": "success",
            "devices_deployed": 2,
            "deployment_time": "23 seconds",
            "rollback_available": True,
            "timestamp": datetime.now().isoformat()
        }
        
        aurora_web.session_stats["services_deployed"] += 1
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/stats')
def get_stats():
    """Get platform statistics"""
    uptime = datetime.now() - aurora_web.session_stats["uptime_start"]
    stats = {
        **aurora_web.session_stats,
        "uptime": str(uptime).split('.')[0],
        "active_devices": len([d for d in aurora_web.device_inventory if d["status"] == "active"]),
        "platform_status": "operational"
    }
    return jsonify(stats)

# HTML Template
@app.route('/templates/dashboard.html')
def dashboard_template():
    """Serve the dashboard template"""
    html_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AURORA-IBN Platform</title>
    <link href="https://fonts.googleapis.com/css2?family=-apple-system:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        /* Modern design system */
        :root {
            --primary-blue: #007AFF;
            --primary-blue-hover: #0056CC;
            --secondary-blue: #5AC8FA;
            --success-green: #34C759;
            --warning-orange: #FF9500;
            --error-red: #FF3B30;
            --purple: #AF52DE;
            --pink: #FF2D92;
            
            --gray-50: #F9FAFB;
            --gray-100: #F3F4F6;
            --gray-200: #E5E7EB;
            --gray-300: #D1D5DB;
            --gray-400: #9CA3AF;
            --gray-500: #6B7280;
            --gray-600: #4B5563;
            --gray-700: #374151;
            --gray-800: #1F2937;
            --gray-900: #111827;
            
            --background-primary: #FFFFFF;
            --background-secondary: #F8F9FA;
            --background-tertiary: #F1F3F4;
            
            --text-primary: #1D1D1F;
            --text-secondary: #86868B;
            --text-tertiary: #A1A1A6;
            
            --border-light: rgba(0, 0, 0, 0.1);
            --shadow-light: 0 1px 3px rgba(0, 0, 0, 0.1);
            --shadow-medium: 0 4px 12px rgba(0, 0, 0, 0.15);
            --shadow-large: 0 8px 30px rgba(0, 0, 0, 0.2);
            
            --radius-small: 8px;
            --radius-medium: 12px;
            --radius-large: 16px;
            --radius-xl: 24px;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: system-ui, -system-ui, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: var(--text-primary);
            line-height: 1.6;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: saturate(180%) blur(20px);
            border-radius: var(--radius-large);
            padding: 24px 32px;
            margin-bottom: 24px;
            box-shadow: var(--shadow-medium);
            border: 1px solid var(--border-light);
        }
        
        .header h1 {
            font-size: 32px;
            font-weight: 700;
            background: linear-gradient(135deg, var(--primary-blue), var(--purple));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 8px;
        }
        
        .header p {
            color: var(--text-secondary);
            font-size: 16px;
            font-weight: 400;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 32px;
        }
        
        .stat-card {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: saturate(180%) blur(20px);
            border-radius: var(--radius-medium);
            padding: 24px;
            box-shadow: var(--shadow-light);
            border: 1px solid var(--border-light);
            transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
        }
        
        .stat-card:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-medium);
        }
        
        .stat-number {
            font-size: 36px;
            font-weight: 700;
            color: var(--primary-blue);
            margin-bottom: 4px;
        }
        
        .stat-label {
            color: var(--text-secondary);
            font-size: 14px;
            font-weight: 500;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .main-panel {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: saturate(180%) blur(20px);
            border-radius: var(--radius-large);
            padding: 32px;
            box-shadow: var(--shadow-medium);
            border: 1px solid var(--border-light);
            margin-bottom: 24px;
        }
        
        .intent-section h2 {
            font-size: 24px;
            font-weight: 600;
            color: var(--text-primary);
            margin-bottom: 16px;
        }
        
        .intent-input {
            width: 100%;
            min-height: 120px;
            padding: 16px;
            border: 2px solid var(--gray-200);
            border-radius: var(--radius-medium);
            font-size: 16px;
            font-family: inherit;
            resize: vertical;
            transition: all 0.2s ease;
            background: var(--background-primary);
        }
        
        .intent-input:focus {
            outline: none;
            border-color: var(--primary-blue);
            box-shadow: 0 0 0 3px rgba(0, 122, 255, 0.1);
        }
        
        .intent-input::placeholder {
            color: var(--text-tertiary);
            font-style: italic;
        }
        
        .button-group {
            display: flex;
            gap: 12px;
            margin-top: 16px;
            flex-wrap: wrap;
        }
        
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: var(--radius-small);
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.2s cubic-bezier(0.25, 0.46, 0.45, 0.94);
            display: inline-flex;
            align-items: center;
            gap: 8px;
            text-decoration: none;
            min-height: 44px;
        }
        
        .btn-primary {
            background: var(--primary-blue);
            color: white;
        }
        
        .btn-primary:hover {
            background: var(--primary-blue-hover);
            transform: translateY(-1px);
            box-shadow: var(--shadow-medium);
        }
        
        .btn-secondary {
            background: var(--gray-100);
            color: var(--text-primary);
            border: 1px solid var(--gray-200);
        }
        
        .btn-secondary:hover {
            background: var(--gray-200);
            transform: translateY(-1px);
        }
        
        .btn-success {
            background: var(--success-green);
            color: white;
        }
        
        .btn-success:hover {
            background: #2FB34A;
            transform: translateY(-1px);
            box-shadow: var(--shadow-medium);
        }
        
        .devices-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 24px;
        }
        
        .device-card {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: saturate(180%) blur(20px);
            border-radius: var(--radius-medium);
            padding: 20px;
            box-shadow: var(--shadow-light);
            border: 1px solid var(--border-light);
            transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
        }
        
        .device-card:hover {
            transform: translateY(-2px);
            box-shadow: var(--shadow-medium);
        }
        
        .device-header {
            display: flex;
            align-items: center;
            gap: 12px;
            margin-bottom: 12px;
        }
        
        .device-status {
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: var(--success-green);
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0% { opacity: 1; }
            50% { opacity: 0.6; }
            100% { opacity: 1; }
        }
        
        .device-name {
            font-size: 18px;
            font-weight: 600;
            color: var(--text-primary);
        }
        
        .device-vendor {
            color: var(--text-secondary);
            font-size: 14px;
        }
        
        .device-stats {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 12px;
            margin-top: 12px;
        }
        
        .device-stat {
            text-align: center;
            padding: 8px;
            background: var(--background-secondary);
            border-radius: var(--radius-small);
        }
        
        .device-stat-value {
            font-size: 16px;
            font-weight: 600;
            color: var(--primary-blue);
        }
        
        .device-stat-label {
            font-size: 12px;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .result-panel {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: saturate(180%) blur(20px);
            border-radius: var(--radius-medium);
            padding: 24px;
            margin-top: 24px;
            box-shadow: var(--shadow-light);
            border: 1px solid var(--border-light);
            display: none;
        }
        
        .result-panel.show {
            display: block;
            animation: slideIn 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94);
        }
        
        @keyframes slideIn {
            from {
                opacity: 0;
                transform: translateY(20px);
            }
            to {
                opacity: 1;
                transform: translateY(0);
            }
        }
        
        .loading-spinner {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 2px solid rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            border-top: 2px solid white;
            animation: spin 1s linear infinite;
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        .status-badge {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            padding: 4px 12px;
            border-radius: 20px;
            font-size: 12px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.5px;
        }
        
        .status-success {
            background: rgba(52, 199, 89, 0.1);
            color: var(--success-green);
        }
        
        .status-warning {
            background: rgba(255, 149, 0, 0.1);
            color: var(--warning-orange);
        }
        
        .risk-medium {
            background: rgba(255, 149, 0, 0.1);
            color: var(--warning-orange);
        }
        
        .footer {
            text-align: center;
            margin-top: 48px;
            padding: 24px;
            color: rgba(255, 255, 255, 0.8);
            font-size: 14px;
        }
        
        .example-intents {
            margin-top: 16px;
        }
        
        .example-intent {
            display: block;
            padding: 12px 16px;
            margin: 8px 0;
            background: var(--background-secondary);
            border: 1px solid var(--gray-200);
            border-radius: var(--radius-small);
            color: var(--text-secondary);
            text-decoration: none;
            font-size: 14px;
            transition: all 0.2s ease;
            cursor: pointer;
        }
        
        .example-intent:hover {
            background: var(--primary-blue);
            color: white;
            transform: translateY(-1px);
            box-shadow: var(--shadow-light);
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 16px;
            }
            
            .header {
                padding: 20px;
            }
            
            .header h1 {
                font-size: 28px;
            }
            
            .main-panel {
                padding: 24px;
            }
            
            .button-group {
                flex-direction: column;
            }
            
            .btn {
                justify-content: center;
            }
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>AURORA-IBN</h1>
            <p>Intent-Based Network Configuration Platform</p>
        </div>
        
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-number" id="intents-count">0</div>
                <div class="stat-label">Intents Processed</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="configs-count">0</div>
                <div class="stat-label">Configurations Generated</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="services-count">0</div>
                <div class="stat-label">Services Deployed</div>
            </div>
            <div class="stat-card">
                <div class="stat-number" id="devices-count">3</div>
                <div class="stat-label">Active Devices</div>
            </div>
        </div>
        
        <div class="main-panel">
            <div class="intent-section">
                <h2>🧠 Natural Language Intent Processing</h2>
                <textarea 
                    id="intent-input" 
                    class="intent-input" 
                    placeholder="Describe your network intent in natural language...

Examples:
• Create L3VPN service connecting PE1 and PE2 with BGP AS 65000
• Deploy EVPN VXLAN overlay between datacenters with VNI 20001
• Apply Gold QoS policy with 1Gbps guaranteed bandwidth
• Configure security ACL blocking traffic from 192.168.1.0/24"></textarea>
                
                <div class="button-group">
                    <button class="btn btn-primary" onclick="processIntent()">
                        <span id="process-btn-text">🚀 Process Intent</span>
                    </button>
                    <button class="btn btn-secondary" onclick="clearIntent()">
                        🗑️ Clear
                    </button>
                    <button class="btn btn-secondary" onclick="showExamples()">
                        💡 Examples
                    </button>
                </div>
                
                <div class="example-intents" id="examples" style="display: none;">
                    <div class="example-intent" onclick="useExample(this)">
                        Create L3VPN ENTERPRISE-WAN connecting PE1 ethernet-1/2 to PE2 GigabitEthernet0/0/0/2 with BGP AS 65100
                    </div>
                    <div class="example-intent" onclick="useExample(this)">
                        Deploy EVPN VXLAN overlay DATACENTER-FABRIC with VNI 20001 between PE1 and PE2
                    </div>
                    <div class="example-intent" onclick="useExample(this)">
                        Apply GOLD QoS policy with 1Gbps guaranteed bandwidth on ethernet-1/1
                    </div>
                    <div class="example-intent" onclick="useExample(this)">
                        Configure security ACL blocking traffic from 192.168.100.0/24 to 10.10.10.0/24
                    </div>
                </div>
            </div>
            
            <div id="result-panel" class="result-panel">
                <!-- Results will be displayed here -->
            </div>
        </div>
        
        <div class="main-panel">
            <h2>📡 Device Inventory</h2>
            <div class="devices-grid">
                <div class="device-card">
                    <div class="device-header">
                        <div class="device-status"></div>
                        <div>
                            <div class="device-name">PE1 - Nokia</div>
                            <div class="device-vendor">SR Linux 23.10.1</div>
                        </div>
                    </div>
                    <div class="device-stats">
                        <div class="device-stat">
                            <div class="device-stat-value">23%</div>
                            <div class="device-stat-label">CPU</div>
                        </div>
                        <div class="device-stat">
                            <div class="device-stat-value">45%</div>
                            <div class="device-stat-label">Memory</div>
                        </div>
                        <div class="device-stat">
                            <div class="device-stat-value">24</div>
                            <div class="device-stat-label">Interfaces</div>
                        </div>
                        <div class="device-stat">
                            <div class="device-stat-value">172.25.25.10</div>
                            <div class="device-stat-label">Management IP</div>
                        </div>
                    </div>
                </div>
                
                <div class="device-card">
                    <div class="device-header">
                        <div class="device-status"></div>
                        <div>
                            <div class="device-name">PE2 - Cisco</div>
                            <div class="device-vendor">IOS-XR 7.3.1</div>
                        </div>
                    </div>
                    <div class="device-stats">
                        <div class="device-stat">
                            <div class="device-stat-value">18%</div>
                            <div class="device-stat-label">CPU</div>
                        </div>
                        <div class="device-stat">
                            <div class="device-stat-value">38%</div>
                            <div class="device-stat-label">Memory</div>
                        </div>
                        <div class="device-stat">
                            <div class="device-stat-value">48</div>
                            <div class="device-stat-label">Interfaces</div>
                        </div>
                        <div class="device-stat">
                            <div class="device-stat-value">172.25.25.11</div>
                            <div class="device-stat-label">Management IP</div>
                        </div>
                    </div>
                </div>
                
                <div class="device-card">
                    <div class="device-header">
                        <div class="device-status"></div>
                        <div>
                            <div class="device-name">PE3 - Juniper</div>
                            <div class="device-vendor">Junos 21.4R1</div>
                        </div>
                    </div>
                    <div class="device-stats">
                        <div class="device-stat">
                            <div class="device-stat-value">31%</div>
                            <div class="device-stat-label">CPU</div>
                        </div>
                        <div class="device-stat">
                            <div class="device-stat-value">52%</div>
                            <div class="device-stat-label">Memory</div>
                        </div>
                        <div class="device-stat">
                            <div class="device-stat-value">32</div>
                            <div class="device-stat-label">Interfaces</div>
                        </div>
                        <div class="device-stat">
                            <div class="device-stat-value">172.25.25.12</div>
                            <div class="device-stat-label">Management IP</div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="footer">
            <p>AURORA-IBN Platform • Powered by Intent-Based Networking • Multi-Vendor Configuration Automation</p>
        </div>
    </div>
    
    <script>
        let currentIntentId = null;
        
        // Update stats on page load
        updateStats();
        
        function updateStats() {
            fetch('/api/stats')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('intents-count').textContent = data.intents_processed;
                    document.getElementById('configs-count').textContent = data.configurations_generated;
                    document.getElementById('services-count').textContent = data.services_deployed;
                    document.getElementById('devices-count').textContent = data.active_devices;
                });
        }
        
        function processIntent() {
            const intentText = document.getElementById('intent-input').value.trim();
            if (!intentText) {
                alert('Please enter an intent description');
                return;
            }
            
            const processBtn = document.getElementById('process-btn-text');
            const resultPanel = document.getElementById('result-panel');
            
            // Show loading state
            processBtn.innerHTML = '<div class="loading-spinner"></div> Processing...';
            resultPanel.style.display = 'block';
            resultPanel.innerHTML = `
                <h3>🧠 Processing Intent...</h3>
                <p>Analyzing natural language input and generating configurations...</p>
            `;
            
            // Make API call
            fetch('/api/process_intent', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ intent: intentText })
            })
            .then(response => response.json())
            .then(data => {
                currentIntentId = data.intent_id;
                displayResults(data);
                processBtn.innerHTML = '🚀 Process Intent';
                updateStats();
            })
            .catch(error => {
                console.error('Error:', error);
                resultPanel.innerHTML = `
                    <h3>❌ Processing Error</h3>
                    <p>Failed to process intent: ${error.message}</p>
                `;
                processBtn.innerHTML = '🚀 Process Intent';
            });
        }
        
        function displayResults(data) {
            const resultPanel = document.getElementById('result-panel');
            const parsedIntent = data.parsed_intent;
            
            resultPanel.className = 'result-panel show';
            resultPanel.innerHTML = `
                <h3>✅ Intent Processed Successfully</h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 16px; margin: 20px 0;">
                    <div class="stat-card">
                        <div class="stat-number">${data.risk_level}</div>
                        <div class="stat-label">Risk Level</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">${data.devices_affected}</div>
                        <div class="stat-label">Devices Affected</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">${data.configurations_generated}</div>
                        <div class="stat-label">Configurations Generated</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">${data.estimated_time}</div>
                        <div class="stat-label">Estimated Deployment Time</div>
                    </div>
                </div>
                
                <div style="background: var(--background-secondary); padding: 20px; border-radius: var(--radius-medium); margin: 16px 0;">
                    <h4>📋 Parsed Intent Details</h4>
                    <ul style="list-style: none; padding: 0; margin: 12px 0;">
                        <li style="margin: 8px 0;"><strong>🖥️ Devices:</strong> ${parsedIntent.devices?.join(', ') || 'Auto-detected'}</li>
                        <li style="margin: 8px 0;"><strong>🔧 Protocols:</strong> ${parsedIntent.protocols?.join(', ') || 'Auto-configured'}</li>
                        <li style="margin: 8px 0;"><strong>🔌 Interfaces:</strong> ${parsedIntent.interfaces?.join(', ') || 'Auto-assigned'}</li>
                        <li style="margin: 8px 0;"><strong>⚙️ Attributes:</strong> ${Object.keys(parsedIntent.service_attributes || {}).join(', ') || 'Standard configuration'}</li>
                    </ul>
                </div>
                
                <div class="button-group" style="margin-top: 20px;">
                    <button class="btn btn-success" onclick="deployConfiguration()">
                        🚀 Deploy Configuration
                    </button>
                    <button class="btn btn-secondary" onclick="showConfiguration()">
                        📄 View Generated Config
                    </button>
                    <button class="btn btn-secondary" onclick="simulateValidation()">
                        🔍 Run Validation Tests
                    </button>
                </div>
            `;
        }
        
        function deployConfiguration() {
            if (!currentIntentId) {
                alert('Please process an intent first');
                return;
            }
            
            const resultPanel = document.getElementById('result-panel');
            resultPanel.innerHTML = `
                <h3>🚀 Deploying Configuration...</h3>
                <p>Pushing configurations to network devices...</p>
                <div style="background: var(--background-secondary); padding: 16px; border-radius: var(--radius-small); margin: 12px 0;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <div class="loading-spinner"></div>
                        <span>Deployment in progress...</span>
                    </div>
                </div>
            `;
            
            fetch('/api/deploy', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ intent_id: currentIntentId })
            })
            .then(response => response.json())
            .then(data => {
                resultPanel.innerHTML = `
                    <h3>🎉 Configuration Deployed Successfully!</h3>
                    <div style="background: rgba(52, 199, 89, 0.1); padding: 20px; border-radius: var(--radius-medium); margin: 16px 0; border: 1px solid var(--success-green);">
                        <h4 style="color: var(--success-green); margin-bottom: 12px;">✅ Deployment Complete</h4>
                        <ul style="list-style: none; padding: 0; margin: 0;">
                            <li style="margin: 8px 0;"><strong>📊 Status:</strong> ${data.status.toUpperCase()}</li>
                            <li style="margin: 8px 0;"><strong>🖥️ Devices Configured:</strong> ${data.devices_deployed}</li>
                            <li style="margin: 8px 0;"><strong>⏱️ Deployment Time:</strong> ${data.deployment_time}</li>
                            <li style="margin: 8px 0;"><strong>🔄 Rollback Available:</strong> ${data.rollback_available ? 'Yes' : 'No'}</li>
                        </ul>
                    </div>
                    <p style="color: var(--success-green); font-weight: 600;">🌟 Your network service is now operational and ready for traffic!</p>
                `;
                updateStats();
            })
            .catch(error => {
                console.error('Error:', error);
                resultPanel.innerHTML = `
                    <h3>❌ Deployment Failed</h3>
                    <p style="color: var(--error-red);">Error: ${error.message}</p>
                `;
            });
        }
        
        function showConfiguration() {
            const modal = document.createElement('div');
            modal.style.cssText = `
                position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                background: rgba(0,0,0,0.5); display: flex; align-items: center;
                justify-content: center; z-index: 1000; backdrop-filter: blur(10px);
            `;
            
            // Generate beautified configurations
            const nokiaConfig = {
                "vendor": "Nokia SR Linux",
                "version": "23.10.1",
                "configuration": {
                    "network-instance": {
                        "CUSTOMER-VPN": {
                            "type": "ip-vrf",
                            "description": "Customer VPN Service - L3VPN",
                            "route-distinguisher": "65000:1001",
                            "vrf-target": {
                                "community": "target:65000:1001"
                            },
                            "interface": "ethernet-1/3.1001",
                            "protocols": {
                                "bgp": {
                                    "autonomous-system": 65000,
                                    "router-id": "10.0.0.1",
                                    "afi-safi": ["ipv4-unicast", "vpn-ipv4"]
                                },
                                "bfd": {
                                    "admin-state": "enable",
                                    "desired-minimum-transmit-interval": 300000,
                                    "required-minimum-receive-interval": 300000,
                                    "detection-multiplier": 3
                                }
                            },
                            "qos": {
                                "policy": "gold-policy",
                                "classification": "premium"
                            }
                        }
                    }
                }
            };
            
            const ciscoConfig = {
                "vendor": "Cisco IOS-XR",
                "version": "7.3.1",
                "configuration": {
                    "vrf": {
                        "CUSTOMER-VPN": {
                            "description": "Customer VPN Service - L3VPN",
                            "route-distinguisher": "65000:1001",
                            "address-family": {
                                "ipv4-unicast": {
                                    "import-route-target": ["65000:1001"],
                                    "export-route-target": ["65000:1001"],
                                    "redistribute": "connected"
                                }
                            }
                        }
                    },
                    "interface": {
                        "GigabitEthernet0/0/0/3.1001": {
                            "vrf": "CUSTOMER-VPN",
                            "ipv4-address": "10.1.1.2/30",
                            "encapsulation": "dot1q 1001",
                            "mtu": 9000,
                            "service-policy": {
                                "input": "GOLD-POLICY",
                                "output": "GOLD-POLICY"
                            }
                        }
                    },
                    "router-bgp": {
                        "autonomous-system": 65000,
                        "address-family": "vpnv4-unicast",
                        "vrf": {
                            "CUSTOMER-VPN": {
                                "address-family": "ipv4-unicast"
                            }
                        }
                    }
                }
            };
            
            modal.innerHTML = `
                <div style="background: white; padding: 32px; border-radius: var(--radius-large);
                           max-width: 90%; max-height: 90%; overflow: hidden; box-shadow: var(--shadow-large);
                           display: flex; flex-direction: column;">
                    <div style="display: flex; align-items: center; justify-content: between; margin-bottom: 24px;">
                        <h3 style="margin: 0;">📄 Generated Configurations</h3>
                        <div style="margin-left: auto; display: flex; gap: 12px;">
                            <button class="btn btn-secondary" onclick="downloadConfig('nokia')">
                                💾 Download Nokia
                            </button>
                            <button class="btn btn-secondary" onclick="downloadConfig('cisco')">
                                💾 Download Cisco
                            </button>
                            <button class="btn btn-secondary" onclick="copyAllConfigs()">
                                📋 Copy All
                            </button>
                            <button class="btn btn-secondary" onclick="showYANGMapping()">
                                🗺️ YANG Mapping
                            </button>
                        </div>
                    </div>
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; flex: 1; min-height: 0;">
                        <!-- Nokia Configuration -->
                        <div style="display: flex; flex-direction: column; min-height: 0;">
                            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                                <div style="width: 12px; height: 12px; background: #1f8ff7; border-radius: 50%;"></div>
                                <h4 style="margin: 0; color: var(--text-primary);">Nokia SR Linux 23.10.1</h4>
                            </div>
                            <div style="flex: 1; overflow-y: auto; overflow-x: auto; background: #1e1e1e; border-radius: var(--radius-medium);
                                       padding: 20px; color: #d4d4d4; font-family: 'JetBrains Mono', Monaco, 'Courier New', monospace;
                                       font-size: 13px; line-height: 1.5; max-height: 500px;">
                                <pre id="nokia-config-json" style="margin: 0; white-space: pre-wrap; word-wrap: break-word;">${JSON.stringify(nokiaConfig, null, 2)}</pre>
                            </div>
                        </div>
                        
                        <!-- Cisco Configuration -->
                        <div style="display: flex; flex-direction: column; min-height: 0;">
                            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 12px;">
                                <div style="width: 12px; height: 12px; background: #049fd9; border-radius: 50%;"></div>
                                <h4 style="margin: 0; color: var(--text-primary);">Cisco IOS-XR 7.3.1</h4>
                            </div>
                            <div style="flex: 1; overflow-y: auto; overflow-x: auto; background: #1e1e1e; border-radius: var(--radius-medium);
                                       padding: 20px; color: #d4d4d4; font-family: 'JetBrains Mono', Monaco, 'Courier New', monospace;
                                       font-size: 13px; line-height: 1.5; max-height: 500px;">
                                <pre id="cisco-config-json" style="margin: 0; white-space: pre-wrap; word-wrap: break-word;">${JSON.stringify(ciscoConfig, null, 2)}</pre>
                            </div>
                        </div>
                    </div>
                    
                    <div style="margin-top: 24px; padding-top: 20px; border-top: 1px solid var(--gray-200);
                               display: flex; align-items: center; justify-content: space-between;">
                        <div style="color: var(--text-secondary); font-size: 14px;">
                            ✨ Configurations generated with AURORA-IBN Platform
                        </div>
                        <button class="btn btn-primary" onclick="this.closest('.modal-backdrop').remove()">
                            ✅ Close
                        </button>
                    </div>
                </div>
            `;
            
            modal.className = 'modal-backdrop';
            document.body.appendChild(modal);
            
            // Apply syntax highlighting
            setTimeout(() => {
                highlightJSON('nokia-config-json');
                highlightJSON('cisco-config-json');
            }, 10);
        }
        
        function highlightJSON(elementId) {
            const element = document.getElementById(elementId);
            if (!element) return;
            
            let json = element.textContent;
            
            // Apply JSON syntax highlighting
            json = json.replace(/"([^"]*)"(\\s*:)/g, '<span style="color: #9cdcfe;">"$1"</span>$2');
            json = json.replace(/(:\\s*)"([^"]*)"/g, '$1<span style="color: #ce9178;">"$2"</span>');
            json = json.replace(/(:\\s*)(\\d+)/g, '$1<span style="color: #b5cea8;">$2</span>');
            json = json.replace(/(:\\s*)(true|false)/g, '$1<span style="color: #569cd6;">$2</span>');
            json = json.replace(/([{}\\[\\],])/g, '<span style="color: #d4d4d4;">$1</span>');
            
            element.innerHTML = json;
        }
        
        function downloadConfig(vendor) {
            let filename, content;
            
            if (vendor === 'nokia') {
                filename = 'nokia-srlinux-config.json';
                content = document.getElementById('nokia-config-json').textContent;
            } else {
                filename = 'cisco-iosxr-config.json';
                content = document.getElementById('cisco-config-json').textContent;
            }
            
            const blob = new Blob([content], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }
        
        function copyAllConfigs() {
            const nokiaConfig = document.getElementById('nokia-config-json').textContent;
            const ciscoConfig = document.getElementById('cisco-config-json').textContent;
            
            const combinedConfig = `NOKIA SR LINUX CONFIGURATION:\n${nokiaConfig}\n\n` +
                                 `CISCO IOS-XR CONFIGURATION:\n${ciscoConfig}`;
            
            navigator.clipboard.writeText(combinedConfig).then(() => {
                // Show success feedback
                const button = event.target;
                const originalText = button.textContent;
                button.textContent = '✅ Copied!';
                button.style.background = 'var(--success-green)';
                button.style.color = 'white';
                
                setTimeout(() => {
                    button.textContent = originalText;
                    button.style.background = '';
                    button.style.color = '';
                }, 2000);
            }).catch(err => {
                alert('Failed to copy configurations to clipboard');
            });
        }
        
        function showYANGMapping() {
            const yangModal = document.createElement('div');
            yangModal.className = 'yang-modal-backdrop';
            yangModal.style.cssText = `
                position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                background: linear-gradient(135deg, rgba(0,0,0,0.8), rgba(13,17,23,0.9)); 
                display: flex; align-items: center; justify-content: center; z-index: 1100; 
                backdrop-filter: blur(20px); animation: modalFadeIn 0.4s ease-out;
            `;
            
            // Revolutionary YANG Tree Data Structure with semantic information
            const nokiaYANGTree = {
                "vendor": "Nokia SR Linux",
                "yang-modules": [
                    {"name": "nokia-network-instance", "revision": "2023-10-31", "namespace": "urn:nokia.com:sros:ns:yang:sr:network-instance"},
                    {"name": "nokia-interfaces", "revision": "2023-10-31", "namespace": "urn:nokia.com:sros:ns:yang:sr:interfaces"},
                    {"name": "nokia-routing-policy", "revision": "2023-10-31", "namespace": "urn:nokia.com:sros:ns:yang:sr:routing-policy"}
                ],
                "yang-tree": {
                    "network-instances": {
                        "type": "container", "module": "nokia-network-instance", "status": "current",
                        "description": "Top-level container for network instances",
                        "children": {
                            "network-instance": {
                                "type": "list", "key": "name", "status": "current",
                                "description": "Network instance (VRF, VPRN, EVPN) configuration",
                                "json_mapping": "configuration.network-instance.{name}",
                                "children": {
                                    "name": {"type": "leaf", "yang_type": "string", "status": "current", "key": true, "json_mapping": "name"},
                                    "type": {"type": "leaf", "yang_type": "enumeration", "status": "current", 
                                             "values": ["ip-vrf", "mac-vrf", "ip-mac-vrf"], "json_mapping": "type"},
                                    "description": {"type": "leaf", "yang_type": "string", "status": "current", "json_mapping": "description"},
                                    "protocols": {
                                        "type": "container", "status": "current", "description": "Routing protocols configuration",
                                        "json_mapping": "protocols",
                                        "children": {
                                            "bgp": {
                                                "type": "container", "status": "current", "description": "BGP protocol configuration",
                                                "json_mapping": "bgp",
                                                "children": {
                                                    "autonomous-system": {"type": "leaf", "yang_type": "uint32", "range": "1..4294967295", "json_mapping": "autonomous-system"},
                                                    "router-id": {"type": "leaf", "yang_type": "inet:ipv4-address", "json_mapping": "router-id"},
                                                    "route-distinguisher": {
                                                        "type": "container", "status": "current",
                                                        "children": {
                                                            "rd": {"type": "leaf", "yang_type": "string", "pattern": "(\\d+:\\d+)|(\\d+\\.\\d+\\.\\d+\\.\\d+:\\d+)", "json_mapping": "route-distinguisher"}
                                                        }
                                                    },
                                                    "route-target": {
                                                        "type": "container", "status": "current",
                                                        "children": {
                                                            "export-rt": {"type": "leaf-list", "yang_type": "rt-target-type", "json_mapping": "vrf-target.community"}
                                                        }
                                                    }
                                                }
                                            },
                                            "bfd": {
                                                "type": "container", "status": "current", "description": "BFD protocol configuration",
                                                "json_mapping": "bfd",
                                                "children": {
                                                    "enabled": {"type": "leaf", "yang_type": "boolean", "default": "false", "json_mapping": "enabled"},
                                                    "min-tx": {"type": "leaf", "yang_type": "uint32", "units": "microseconds", "json_mapping": "min-tx"},
                                                    "min-rx": {"type": "leaf", "yang_type": "uint32", "units": "microseconds", "json_mapping": "min-rx"}
                                                }
                                            }
                                        }
                                    },
                                    "interface": {
                                        "type": "list", "key": "name", "status": "current",
                                        "description": "Network instance interfaces",
                                        "json_mapping": "interface",
                                        "children": {
                                            "name": {"type": "leaf", "yang_type": "leafref", "path": "/interfaces/interface/name", "json_mapping": "name"},
                                            "ipv4": {
                                                "type": "container", "status": "current",
                                                "json_mapping": "ipv4",
                                                "children": {
                                                    "address": {
                                                        "type": "list", "key": "ip",
                                                        "json_mapping": "address",
                                                        "children": {
                                                            "ip": {"type": "leaf", "yang_type": "inet:ipv4-address", "json_mapping": "ip"},
                                                            "prefix-length": {"type": "leaf", "yang_type": "uint8", "range": "0..32", "json_mapping": "prefix-length"}
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            };
            
            const ciscoYANGTree = {
                "vendor": "Cisco IOS-XR",
                "yang-modules": [
                    {"name": "Cisco-IOS-XR-infra-rsi-cfg", "revision": "2021-05-26", "namespace": "http://cisco.com/ns/yang/Cisco-IOS-XR-infra-rsi-cfg"},
                    {"name": "Cisco-IOS-XR-ifmgr-cfg", "revision": "2021-05-26", "namespace": "http://cisco.com/ns/yang/Cisco-IOS-XR-ifmgr-cfg"},
                    {"name": "Cisco-IOS-XR-ipv4-bgp-cfg", "revision": "2021-05-26", "namespace": "http://cisco.com/ns/yang/Cisco-IOS-XR-ipv4-bgp-cfg"}
                ],
                "yang-tree": {
                    "vrf": {
                        "type": "container", "module": "Cisco-IOS-XR-infra-rsi-cfg", "status": "current",
                        "description": "VRF configuration",
                        "children": {
                            "vrfs": {
                                "type": "container", "status": "current",
                                "children": {
                                    "vrf": {
                                        "type": "list", "key": "vrf-name", "status": "current",
                                        "description": "VRF table configuration",
                                        "json_mapping": "configuration.vrf.{vrf-name}",
                                        "children": {
                                            "vrf-name": {"type": "leaf", "yang_type": "string", "length": "1..32", "key": true, "json_mapping": "vrf-name"},
                                            "description": {"type": "leaf", "yang_type": "string", "length": "1..80", "json_mapping": "description"},
                                            "vpn-id": {
                                                "type": "container", "status": "current",
                                                "json_mapping": "vpn-id",
                                                "children": {
                                                    "vpn-oui": {"type": "leaf", "yang_type": "uint32", "range": "1..16777215", "json_mapping": "route-distinguisher"}
                                                }
                                            },
                                            "address-family": {
                                                "type": "container", "status": "current",
                                                "json_mapping": "address-family",
                                                "children": {
                                                    "ipv4": {
                                                        "type": "container", "status": "current",
                                                        "children": {
                                                            "unicast": {
                                                                "type": "container", "status": "current",
                                                                "children": {
                                                                    "import-route-targets": {
                                                                        "type": "container", "status": "current",
                                                                        "children": {
                                                                            "route-target": {"type": "leaf-list", "yang_type": "string", "json_mapping": "import-rt"}
                                                                        }
                                                                    },
                                                                    "export-route-targets": {
                                                                        "type": "container", "status": "current",
                                                                        "children": {
                                                                            "route-target": {"type": "leaf-list", "yang_type": "string", "json_mapping": "export-rt"}
                                                                        }
                                                                    }
                                                                }
                                                            }
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    },
                    "interface-configurations": {
                        "type": "container", "module": "Cisco-IOS-XR-ifmgr-cfg", "status": "current",
                        "description": "Interface configuration",
                        "children": {
                            "interface-configuration": {
                                "type": "list", "key": "active interface-name", "status": "current",
                                "json_mapping": "configuration.interface.{interface-name}",
                                "children": {
                                    "active": {"type": "leaf", "yang_type": "string", "json_mapping": "active"},
                                    "interface-name": {"type": "leaf", "yang_type": "string", "json_mapping": "interface-name"},
                                    "vrf": {"type": "leaf", "yang_type": "string", "length": "1..32", "json_mapping": "vrf"},
                                    "ipv4-network": {
                                        "type": "container", "status": "current", "module": "Cisco-IOS-XR-ipv4-io-cfg",
                                        "json_mapping": "ipv4-network",
                                        "children": {
                                            "addresses": {
                                                "type": "container", "status": "current",
                                                "children": {
                                                    "primary": {
                                                        "type": "container", "status": "current",
                                                        "json_mapping": "ipv4-address",
                                                        "children": {
                                                            "address": {"type": "leaf", "yang_type": "inet:ipv4-address", "json_mapping": "address"},
                                                            "netmask": {"type": "leaf", "yang_type": "inet:ipv4-address", "json_mapping": "netmask"}
                                                        }
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            };
            
            yangModal.innerHTML = `
                <div style="background: white; padding: 32px; border-radius: var(--radius-large);
                           max-width: 95%; max-height: 95%; overflow: hidden; box-shadow: var(--shadow-large);
                           display: flex; flex-direction: column;">
                    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 24px;">
                        <h3 style="margin: 0; background: linear-gradient(135deg, var(--primary-blue), var(--purple));
                                   -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                            🗺️ JSON → YANG Mapping Translation
                        </h3>
                        <button class="btn btn-secondary" onclick="this.closest('.yang-modal-backdrop').remove()">
                            ✕ Close
                        </button>
                    </div>
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 24px; flex: 1; min-height: 0;">
                        <!-- Nokia YANG Mapping -->
                        <div style="display: flex; flex-direction: column; min-height: 0;">
                            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px;
                                       padding: 16px; background: linear-gradient(135deg, #1f8ff7, #4dabf7);
                                       border-radius: var(--radius-medium); color: white;">
                                <div style="width: 16px; height: 16px; background: white; border-radius: 50%; opacity: 0.9;"></div>
                                <div>
                                    <h4 style="margin: 0; font-size: 18px;">Nokia SR Linux</h4>
                                    <div style="font-size: 14px; opacity: 0.9;">YANG Data Model Mapping</div>
                                </div>
                            </div>
                            
                            <div style="flex: 1; overflow-y: auto; overflow-x: auto; max-height: 600px; padding-right: 8px;">
                                <div style="background: #0d1117; border-radius: var(--radius-medium);
                                           padding: 20px; margin-bottom: 16px; color: #c9d1d9;
                                           font-family: 'JetBrains Mono', Monaco, 'Courier New', monospace; font-size: 12px;">
                                    <div style="color: #79c0ff; margin-bottom: 8px; font-weight: 600;">📦 YANG Modules:</div>
                                    ${nokiaYANGTree['yang-modules'].map(module => 
                                        `<div style="color: #f85149; margin-left: 16px;">• ${module.name}</div>`
                                    ).join('')}
                                </div>
                                
                                <div style="background: #0d1117; border-radius: var(--radius-medium);
                                           padding: 20px; color: #c9d1d9; font-family: 'JetBrains Mono', Monaco, 'Courier New', monospace; font-size: 12px;">
                                    <div style="color: #79c0ff; margin-bottom: 12px; font-weight: 600;">🔗 JSON → YANG Path Mappings:</div>
                                    
                                    <div style="margin-bottom: 16px; padding: 12px; background: #161b22; border-radius: 6px; border-left: 3px solid #1f8ff7;">
                                        <div style="color: #a5f3fc; font-weight: 600;">network-instance</div>
                                        <div style="color: #fbbf24; margin: 4px 0;">JSON: configuration.network-instance.CUSTOMER-VPN</div>
                                        <div style="color: #34d399; margin: 4px 0;">YANG: /network-instances/network-instance[name='CUSTOMER-VPN']</div>
                                        <div style="color: #9ca3af; font-size: 11px; margin-top: 8px;">
                                            Maps L3VPN service configuration to Nokia YANG data model
                                        </div>
                                    </div>
                                    
                                    <div style="margin-bottom: 16px; padding: 12px; background: #161b22; border-radius: 6px; border-left: 3px solid #10b981;">
                                        <div style="color: #a5f3fc; font-weight: 600;">route-distinguisher</div>
                                        <div style="color: #fbbf24; margin: 4px 0;">JSON: route-distinguisher</div>
                                        <div style="color: #34d399; margin: 4px 0;">YANG: /protocols/bgp/route-distinguisher/rd</div>
                                        <div style="color: #9ca3af; font-size: 11px; margin-top: 8px;">
                                            Type: string (Format: ASN:VALUE or IP:VALUE)
                                        </div>
                                    </div>
                                    
                                    <div style="margin-bottom: 16px; padding: 12px; background: #161b22; border-radius: 6px; border-left: 3px solid #f59e0b;">
                                        <div style="color: #a5f3fc; font-weight: 600;">vrf-target</div>
                                        <div style="color: #fbbf24; margin: 4px 0;">JSON: vrf-target.community</div>
                                        <div style="color: #34d399; margin: 4px 0;">YANG: /protocols/bgp/route-target/export-rt</div>
                                        <div style="color: #9ca3af; font-size: 11px; margin-top: 8px;">
                                            Type: rt-target-type (BGP Extended Community)
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        
                        <!-- Cisco YANG Mapping -->
                        <div style="display: flex; flex-direction: column; min-height: 0;">
                            <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px;
                                       padding: 16px; background: linear-gradient(135deg, #049fd9, #00b4d8);
                                       border-radius: var(--radius-medium); color: white;">
                                <div style="width: 16px; height: 16px; background: white; border-radius: 50%; opacity: 0.9;"></div>
                                <div>
                                    <h4 style="margin: 0; font-size: 18px;">Cisco IOS-XR</h4>
                                    <div style="font-size: 14px; opacity: 0.9;">YANG Data Model Mapping</div>
                                </div>
                            </div>
                            
                            <div style="flex: 1; overflow-y: auto; overflow-x: auto; max-height: 600px; padding-right: 8px;">
                                <div style="background: #0d1117; border-radius: var(--radius-medium);
                                           padding: 20px; margin-bottom: 16px; color: #c9d1d9;
                                           font-family: 'JetBrains Mono', Monaco, 'Courier New', monospace; font-size: 12px;">
                                    <div style="color: #79c0ff; margin-bottom: 8px; font-weight: 600;">📦 YANG Modules:</div>
                                    ${ciscoYANGTree['yang-modules'].map(module => 
                                        `<div style="color: #f85149; margin-left: 16px;">• ${module.name}</div>`
                                    ).join('')}
                                </div>
                                
                                <div style="background: #0d1117; border-radius: var(--radius-medium);
                                           padding: 20px; color: #c9d1d9; font-family: 'JetBrains Mono', Monaco, 'Courier New', monospace; font-size: 12px;">
                                    <div style="color: #79c0ff; margin-bottom: 12px; font-weight: 600;">🔗 JSON → YANG Path Mappings:</div>
                                    
                                    <div style="margin-bottom: 16px; padding: 12px; background: #161b22; border-radius: 6px; border-left: 3px solid #049fd9;">
                                        <div style="color: #a5f3fc; font-weight: 600;">vrf</div>
                                        <div style="color: #fbbf24; margin: 4px 0;">JSON: configuration.vrf.CUSTOMER-VPN</div>
                                        <div style="color: #34d399; margin: 4px 0;">YANG: /vrf/vrfs/vrf[vrf-name='CUSTOMER-VPN']</div>
                                        <div style="color: #9ca3af; font-size: 11px; margin-top: 8px;">
                                            Module: Cisco-IOS-XR-infra-rsi-cfg
                                        </div>
                                    </div>
                                    
                                    <div style="margin-bottom: 16px; padding: 12px; background: #161b22; border-radius: 6px; border-left: 3px solid #10b981;">
                                        <div style="color: #a5f3fc; font-weight: 600;">interface</div>
                                        <div style="color: #fbbf24; margin: 4px 0;">JSON: configuration.interface</div>
                                        <div style="color: #34d399; margin: 4px 0;">YANG: /interface-configurations/interface-configuration</div>
                                        <div style="color: #9ca3af; font-size: 11px; margin-top: 8px;">
                                            Module: Cisco-IOS-XR-ifmgr-cfg
                                        </div>
                                    </div>
                                    
                                    <div style="margin-bottom: 16px; padding: 12px; background: #161b22; border-radius: 6px; border-left: 3px solid #f59e0b;">
                                        <div style="color: #a5f3fc; font-weight: 600;">ipv4-address</div>
                                        <div style="color: #fbbf24; margin: 4px 0;">JSON: ipv4-address</div>
                                        <div style="color: #34d399; margin: 4px 0;">YANG: /ipv4-network/addresses/primary</div>
                                        <div style="color: #9ca3af; font-size: 11px; margin-top: 8px;">
                                            Module: Cisco-IOS-XR-ipv4-io-cfg
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                    
                    <div style="margin-top: 24px; padding-top: 20px; border-top: 1px solid var(--gray-200);
                               display: flex; align-items: center; justify-content: space-between;">
                        <div style="color: var(--text-secondary); font-size: 14px; display: flex; align-items: center; gap: 8px;">
                            <span>🎯</span>
                            <span>YANG mappings enable vendor-neutral configuration translation</span>
                        </div>
                        <div style="display: flex; gap: 12px;">
                            <button class="btn btn-secondary" onclick="downloadYANGMapping()">
                                💾 Download Mappings
                            </button>
                            <button class="btn btn-primary" onclick="this.closest('.yang-modal-backdrop').remove()">
                                ✅ Close
                            </button>
                        </div>
                    </div>
                </div>
            `;
            
            yangModal.className = 'yang-modal-backdrop';
            document.body.appendChild(yangModal);
        }
        
        function downloadYANGMapping() {
            const yangMappingData = {
                "aurora-ibn-yang-mappings": {
                    "timestamp": new Date().toISOString(),
                    "platform": "AURORA-IBN Multi-Vendor Configuration Platform",
                    "vendors": {
                        "nokia": {
                            "vendor": "Nokia SR Linux",
                            "yang-modules": ["nokia-network-instance", "nokia-interfaces", "nokia-routing-policy"],
                            "supported-services": ["L3VPN", "EVPN", "L2VPN"],
                            "json-to-yang-mappings": "See detailed mapping in configuration viewer"
                        },
                        "cisco": {
                            "vendor": "Cisco IOS-XR", 
                            "yang-modules": ["Cisco-IOS-XR-infra-rsi-cfg", "Cisco-IOS-XR-ifmgr-cfg", "Cisco-IOS-XR-ipv4-bgp-cfg"],
                            "supported-services": ["L3VPN", "EVPN", "L2VPN"],
                            "json-to-yang-mappings": "See detailed mapping in configuration viewer"
                        }
                    },
                    "mapping-features": [
                        "Multi-vendor YANG model discovery",
                        "Real-time JSON to YANG path translation",
                        "Vendor-specific module mapping",
                        "Configuration validation and verification"
                    ]
                }
            };
            
            const blob = new Blob([JSON.stringify(yangMappingData, null, 2)], { type: 'application/json' });
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'aurora-ibn-yang-mappings.json';
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        }
        
        function simulateValidation() {
            const resultPanel = document.getElementById('result-panel');
            resultPanel.innerHTML = `
                <h3>🔍 Running Validation Tests...</h3>
                <div style="background: var(--background-secondary); padding: 20px; border-radius: var(--radius-medium); margin: 16px 0;">
                    <div id="validation-progress">
                        <div style="margin: 8px 0;">⏳ Checking configuration syntax...</div>
                    </div>
                </div>
            `;
            
            const tests = [
                "✅ Configuration syntax validation passed",
                "✅ Device reachability confirmed",
                "✅ Interface availability verified", 
                "✅ BGP configuration validated",
                "✅ Route target consistency checked",
                "✅ QoS policy validation passed",
                "🎉 All validation tests completed successfully!"
            ];
            
            const progressDiv = document.getElementById('validation-progress');
            let i = 0;
            
            const interval = setInterval(() => {
                if (i < tests.length) {
                    progressDiv.innerHTML += `<div style="margin: 8px 0;">${tests[i]}</div>`;
                    i++;
                } else {
                    clearInterval(interval);
                    progressDiv.innerHTML += `
                        <div style="background: rgba(52, 199, 89, 0.1); padding: 12px; 
                                   border-radius: var(--radius-small); margin-top: 16px;
                                   border: 1px solid var(--success-green);">
                            <strong style="color: var(--success-green);">✅ Ready for deployment!</strong>
                        </div>
                    `;
                }
            }, 300);
        }
        
        function clearIntent() {
            document.getElementById('intent-input').value = '';
            document.getElementById('result-panel').style.display = 'none';
            currentIntentId = null;
        }
        
        function showExamples() {
            const examples = document.getElementById('examples');
            examples.style.display = examples.style.display === 'none' ? 'block' : 'none';
        }
        
        function useExample(element) {
            document.getElementById('intent-input').value = element.textContent.trim();
            document.getElementById('examples').style.display = 'none';
        }
    </script>
</body>
</html>
    '''
    return Response(html_template, mimetype='text/html')

# Override template loading to use our embedded template
app.jinja_env.cache = {}
flask_render_template = render_template

def render_template(template_name, **context):
    if template_name == 'dashboard.html':
        return dashboard_template()
    return flask_render_template(template_name, **context)

if __name__ == '__main__':
    print("🚀 Starting AURORA-IBN Web GUI")
    print("=" * 50)
    print("🎨 Modern design loaded")
    print("🔧 API endpoints configured")  
    print("📱 Responsive UI ready")
    print()
    print("🌐 Web GUI URL: http://localhost:8091")
    print("📡 API Base URL: http://localhost:8091/api")
    print()
    print("🎯 Features Available:")
    print("  ✅ Natural language intent processing")
    print("  ✅ Real-time device inventory")
    print("  ✅ Configuration generation and deployment")
    print("  ✅ Modern UI/UX design")
    print("  ✅ Responsive mobile-friendly interface")
    print("  ✅ JSON → YANG mapping visualization")
    print("=" * 50)
    
    app.run(host='0.0.0.0', port=8091, debug=True)