#!/usr/bin/env python3
"""
Test script to verify ARM progression logic
"""

class EvaluationArm:
    SYSTEM_1 = "SYSTEM_1"
    SYSTEM_2 = "SYSTEM_2" 
    SYSTEM_2_PERSONA = "SYSTEM_2_PERSONA"
    SYSTEM_2_PERSONA_DEBIAS = "SYSTEM_2_PERSONA_DEBIAS"

def test_arm_progression():
    """Test ARM progression logic"""
    
    # Test cases
    test_cases = [
        {"completed": set(), "expected": "SYSTEM_1", "description": "No ARMs completed"},
        {"completed": {"SYSTEM_1"}, "expected": "SYSTEM_2", "description": "ARM A completed"},
        {"completed": {"SYSTEM_1", "SYSTEM_2"}, "expected": "SYSTEM_2_PERSONA", "description": "ARM A, B completed"},
        {"completed": {"SYSTEM_1", "SYSTEM_2", "SYSTEM_2_PERSONA"}, "expected": "SYSTEM_2_PERSONA_DEBIAS", "description": "ARM A, B, C completed"},
        {"completed": {"SYSTEM_1", "SYSTEM_2", "SYSTEM_2_PERSONA", "SYSTEM_2_PERSONA_DEBIAS"}, "expected": None, "description": "All ARMs completed"},
    ]
    
    for test_case in test_cases:
        completed_arms = test_case["completed"]
        expected = test_case["expected"]
        description = test_case["description"]
        
        # Logic from the app
        if EvaluationArm.SYSTEM_1 not in completed_arms:
            selected_arm = EvaluationArm.SYSTEM_1
        elif EvaluationArm.SYSTEM_2 not in completed_arms:
            selected_arm = EvaluationArm.SYSTEM_2
        elif EvaluationArm.SYSTEM_2_PERSONA not in completed_arms:
            selected_arm = EvaluationArm.SYSTEM_2_PERSONA
        elif EvaluationArm.SYSTEM_2_PERSONA_DEBIAS not in completed_arms:
            selected_arm = EvaluationArm.SYSTEM_2_PERSONA_DEBIAS
        else:
            selected_arm = None
        
        status = "✅ PASS" if selected_arm == expected else "❌ FAIL"
        print(f"{status} | {description}")
        print(f"  Expected: {expected}")
        print(f"  Got: {selected_arm}")
        print()

def test_button_text_logic():
    """Test button text logic"""
    
    test_cases = [
        {"completed": set(), "expected": "🚀 Start Fast Evaluation (ARM A)"},
        {"completed": {"SYSTEM_1"}, "expected": "📊 Run Detailed Analysis (ARM B)"},
        {"completed": {"SYSTEM_1", "SYSTEM_2"}, "expected": "⚖️ Run Compliance Check (ARM C)"},
        {"completed": {"SYSTEM_1", "SYSTEM_2", "SYSTEM_2_PERSONA"}, "expected": "🧭 Run Compliance + Debias (ARM D)"},
        {"completed": {"SYSTEM_1", "SYSTEM_2", "SYSTEM_2_PERSONA", "SYSTEM_2_PERSONA_DEBIAS"}, "expected": "📈 Show Complete Summary"},
    ]
    
    for test_case in test_cases:
        completed_arms = test_case["completed"]
        expected = test_case["expected"]
        
        # Logic from the app
        button_text = "🚀 Start Fast Evaluation (ARM A)"
        if EvaluationArm.SYSTEM_1 in completed_arms and EvaluationArm.SYSTEM_2 not in completed_arms:
            button_text = "📊 Run Detailed Analysis (ARM B)"
        elif EvaluationArm.SYSTEM_2 in completed_arms and EvaluationArm.SYSTEM_2_PERSONA not in completed_arms:
            button_text = "⚖️ Run Compliance Check (ARM C)"
        elif EvaluationArm.SYSTEM_2_PERSONA in completed_arms and EvaluationArm.SYSTEM_2_PERSONA_DEBIAS not in completed_arms:
            button_text = "🧭 Run Compliance + Debias (ARM D)"
        elif len(completed_arms) >= 4:
            button_text = "📈 Show Complete Summary"
        
        status = "✅ PASS" if button_text == expected else "❌ FAIL"
        print(f"{status} | Completed: {list(completed_arms)}")
        print(f"  Expected: {expected}")
        print(f"  Got: {button_text}")
        print()

if __name__ == "__main__":
    print("🧪 Testing ARM Progression Logic\n")
    print("=" * 50)
    print("ARM Selection Logic:")
    print("=" * 50)
    test_arm_progression()
    
    print("=" * 50) 
    print("Button Text Logic:")
    print("=" * 50)
    test_button_text_logic()
