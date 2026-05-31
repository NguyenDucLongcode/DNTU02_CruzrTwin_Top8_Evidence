"""Delete all Orion subscriptions and create the device webhook subscription.
Run this from repo root.
"""

import json
import os
import sys

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, ROOT_DIR)

from src.fiware.subscription import delete_all_subscriptions, create_subscription_for_devices, get_all_subscriptions

print('Deleting existing subscriptions...')
delete_all_subscriptions()
print('Creating subscription...')
create_subscription_for_devices()
print('Current subscriptions:')
print(json.dumps(get_all_subscriptions(), indent=2))
