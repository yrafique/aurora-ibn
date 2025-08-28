#!/bin/bash

echo "🚀 AURORA-IBN Container SSH Connectivity Test"
echo "============================================="

# Wait for containers to be ready
echo "⏳ Waiting for containers to initialize..."
sleep 15

echo ""
echo "🔍 Testing SSH connectivity to all containers:"
echo ""

# Test function
test_ssh() {
    local name="$1"
    local port="$2"
    local user="$3"
    local pass="$4"
    local host="${5:-localhost}"
    
    echo -n "Testing $name (${user}@${host}:${port})... "
    
    # Use sshpass if available, otherwise skip password test
    if command -v sshpass >/dev/null 2>&1; then
        if timeout 10 sshpass -p "$pass" ssh -o StrictHostKeyChecking=no -o ConnectTimeout=5 -p "$port" "$user@$host" "echo 'Connected successfully'" 2>/dev/null; then
            echo "✅ SUCCESS"
            return 0
        else
            echo "❌ FAILED"
            return 1
        fi
    else
        # Test if port is open
        if timeout 5 bash -c "</dev/tcp/$host/$port" 2>/dev/null; then
            echo "✅ PORT OPEN (install sshpass for full test)"
            return 0
        else
            echo "❌ PORT CLOSED"
            return 1
        fi
    fi
}

# Test each container
successful=0
total=0

# AURORA-IBN Controller
total=$((total + 1))
if test_ssh "AURORA Controller" "2200" "aurora" "aurora123"; then
    successful=$((successful + 1))
fi

# Tester
total=$((total + 1))
if test_ssh "AURORA Tester" "2201" "tester" "tester123"; then
    successful=$((successful + 1))
fi

# Customer devices
total=$((total + 1))
if test_ssh "CE1 Linux" "2230" "root" "ce1pass"; then
    successful=$((successful + 1))
fi

total=$((total + 1))
if test_ssh "CE2 Linux" "2231" "root" "ce2pass"; then
    successful=$((successful + 1))
fi

# Network tools
total=$((total + 1))
if test_ssh "Network Tools" "2240" "root" "nettools123"; then
    successful=$((successful + 1))
fi

# Mock devices
total=$((total + 1))
if test_ssh "Mock Nokia PE1" "2210" "admin" "admin"; then
    successful=$((successful + 1))
fi

total=$((total + 1))
if test_ssh "Mock Cisco PE2" "2211" "cisco" "cisco"; then
    successful=$((successful + 1))
fi

echo ""
echo "📊 SSH Connectivity Results:"
echo "============================"
echo "✅ Successful: $successful/$total"

if [ $successful -eq $total ]; then
    echo "🎉 All containers are accessible via SSH!"
else
    echo "⚠️  Some containers failed SSH connectivity test"
fi

echo ""
echo "🔧 SSH Access Commands:"
echo "======================="
echo "AURORA Controller:  ssh aurora@localhost -p 2200    # password: aurora123"
echo "AURORA Tester:      ssh tester@localhost -p 2201    # password: tester123"
echo "CE1 Linux:          ssh root@localhost -p 2230      # password: ce1pass"
echo "CE2 Linux:          ssh root@localhost -p 2231      # password: ce2pass"  
echo "Network Tools:      ssh root@localhost -p 2240      # password: nettools123"
echo "Mock Nokia PE1:     ssh admin@localhost -p 2210     # password: admin"
echo "Mock Cisco PE2:     ssh cisco@localhost -p 2211     # password: cisco"

echo ""
echo "🌐 Container Network Information:"
echo "================================="
echo "Management Network: 172.25.25.0/24"
echo "  - AURORA Controller: 172.25.25.100"
echo "  - AURORA Tester:     172.25.25.101"
echo "  - CE1 Linux:         172.25.25.30"
echo "  - CE2 Linux:         172.25.25.31"
echo "  - Network Tools:     172.25.25.200"
echo "  - Mock Nokia PE1:    172.25.25.10"
echo "  - Mock Cisco PE2:    172.25.25.11"

echo ""
echo "Customer Networks:"
echo "  - West (CE1): 192.168.100.0/24"
echo "  - East (CE2): 192.168.200.0/24"

echo ""
echo "🚀 Ready for AURORA-IBN testing!"