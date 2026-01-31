#!/usr/bin/env python3
"""
Blessed Dashboard Demo
Interactive terminal UI for Strategy Optimizer monitoring and metrics
"""
import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from monitoring.blessed_dashboard import demo_blessed_dashboard

if __name__ == "__main__":
    demo_blessed_dashboard()
