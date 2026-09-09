"""
Check current Decision Agent implementation
Run this to see what's working and what's missing
"""

import os
import sys
import inspect

print("=" * 60)
print("🔍 CHECKING DECISION AGENT")
print("=" * 60)

# ============================================================
# 1. Check if file exists
# ============================================================
agent_path = "backend/agents/decision_agent.py"
if os.path.exists(agent_path):
    print(f"✅ File exists: {agent_path}")
else:
    print(f"❌ File NOT found: {agent_path}")
    sys.exit(1)

# ============================================================
# 2. Read and show the code
# ============================================================
print("\n📄 CURRENT CODE:")
print("-" * 60)
with open(agent_path, 'r') as f:
    content = f.read()
    print(content)
print("-" * 60)

# ============================================================
# 3. Try to import and test
# ============================================================
print("\n🧪 TESTING AGENT:")
print("-" * 60)

try:
    # Add backend to path
    sys.path.insert(0, os.path.join(os.getcwd(), 'backend'))
    
    from agents.decision_agent import TFTMPIR_DecisionAgent
    
    # Create agent
    agent = TFTMPIR_DecisionAgent()
    print("✅ Agent created successfully")
    
    # Test with sample data
    test_forecast = [10, 15, 12, 18, 20, 14, 16]
    test_stock = 50
    test_days = 7
    
    print(f"\n📊 Testing with:")
    print(f"   Forecast: {test_forecast}")
    print(f"   Current Stock: {test_stock}")
    print(f"   Days: {test_days}")
    
    # Test optimal_quantity
    qty, cost = agent.optimal_quantity(test_forecast, test_stock, test_days)
    print(f"\n📈 Results:")
    print(f"   Optimal Order: {qty} units")
    print(f"   Total Cost: ${cost:.2f}")
    
    # Test compute_total_cost
    cost = agent.compute_total_cost(75, test_forecast, test_stock, test_days)
    print(f"\n💰 Cost Breakdown (Order 75 units):")
    print(f"   Total Cost: ${cost:.2f}")
    
    # Show what methods exist
    print("\n📋 Available Methods:")
    for method in dir(agent):
        if not method.startswith('_'):
            print(f"   - {method}")
    
    # Check if TFT-MPIR is actually trained
    print("\n🔍 Checking if TFT-MPIR is trained:")
    if hasattr(agent, 'model'):
        print("   ✅ Has 'model' attribute")
        if agent.model is not None:
            print("   ✅ Model is loaded")
        else:
            print("   ❌ Model is None (NOT TRAINED YET)")
    else:
        print("   ❌ No 'model' attribute (NO TRAINED MODEL)")
    
    if hasattr(agent, 'scaler'):
        print("   ✅ Has 'scaler' attribute")
    else:
        print("   ❌ No 'scaler' attribute")
    
except Exception as e:
    print(f"❌ Error: {e}")

print("\n" + "=" * 60)
print("✅ CHECK COMPLETE")
print("=" * 60)