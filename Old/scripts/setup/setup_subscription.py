"""Setup subscription - chạy 1 lần"""

import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT_DIR)

from src.fiware.subscription import create_subscription_for_devices, delete_all_subscriptions

if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("🔧 Setting up Orion Subscription")
    print("=" * 50)
    
    choice = input("Delete existing subscriptions? (y/n): ")
    if choice.lower() == 'y':
        delete_all_subscriptions()
    
    create_subscription_for_devices()