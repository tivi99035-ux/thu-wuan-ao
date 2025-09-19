#!/bin/bash

echo "📊 Seed-VC Complete Status Check"
echo "================================"

# Check processes
echo "🔍 Process Status:"
if pgrep -f "working_backend.py" > /dev/null; then
    BACKEND_PID=$(pgrep -f "working_backend.py")
    echo "✅ Backend: RUNNING (PID: $BACKEND_PID)"
else
    echo "❌ Backend: STOPPED"
fi

if pgrep -f "next dev" > /dev/null; then
    FRONTEND_PID=$(pgrep -f "next dev")
    echo "✅ Frontend: RUNNING (PID: $FRONTEND_PID)"
else
    echo "❌ Frontend: STOPPED"
fi

# Check ports
echo ""
echo "🌐 Port Status:"
netstat -tlnp 2>/dev/null | grep -E ":(3000|3001|8000|6379)" | while read line; do
    echo "📡 $line"
done

# Test endpoints
echo ""
echo "🧪 Endpoint Tests:"

# Test backend health
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ Backend health: OK"
    curl -s http://localhost:8000/health | python3 -m json.tool 2>/dev/null || echo "Backend responded"
else
    echo "❌ Backend health: FAILED"
fi

# Test voice cloning
echo ""
echo "🎭 Voice Cloning Test:"
CLONING_RESULT=$(curl -s http://localhost:8000/test/voice-cloning)
if echo "$CLONING_RESULT" | grep -q "success.*true"; then
    echo "✅ Voice cloning: WORKING"
    echo "$CLONING_RESULT" | python3 -m json.tool 2>/dev/null | head -10
else
    echo "❌ Voice cloning: FAILED"
    echo "$CLONING_RESULT"
fi

# System resources
echo ""
echo "💻 System Resources:"
echo "CPU: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)%"
echo "Memory: $(free -m | awk 'NR==2{printf "%d/%dMB (%.1f%%)", $3,$2,$3*100/$2}')"
echo "Disk: $(df -h / | awk 'NR==2{print $3"/"$2" ("$5")"}')"

echo ""
echo "🎯 Quick Access:"
echo "Frontend: http://$(hostname -I | awk '{print $1}'):3001"
echo "Backend: http://$(hostname -I | awk '{print $1}'):8000"
echo "Voice Clone Test: curl http://localhost:8000/test/voice-cloning"