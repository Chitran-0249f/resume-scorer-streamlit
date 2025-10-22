#!/usr/bin/env python3
"""
Simple test script to validate chart functionality
"""

import pandas as pd
import streamlit as st

def test_chart_generation():
    """Test chart generation with sample data"""
    
    # Test data similar to what the app uses
    arm_labels = ['ARM A', 'ARM B', 'ARM C', 'ARM D']
    scores = [4.2, 3.8, 4.1, 3.9]
    
    # Create DataFrame
    chart_data = pd.DataFrame({
        'Score': scores
    }, index=arm_labels)
    
    print("Chart data structure:")
    print(chart_data)
    print("\nData types:")
    print(chart_data.dtypes)
    print("\nIndex:")
    print(chart_data.index)
    
    return chart_data

if __name__ == "__main__":
    test_chart_generation()
