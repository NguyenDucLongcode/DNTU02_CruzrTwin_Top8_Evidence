@echo off
chcp 65001 > nul
echo ============================================================
echo  RUNNING: Create Entities + Setup Subscription
echo ============================================================
echo.

echo [1/2] Creating entities...
echo ------------------------------------------------------------
python src\fiware\entities\create_entities_required.py
python \src\fimat\register.py

if %errorlevel% neq 0 (
    echo ❌ Failed to create entities!
    pause
    exit /b 1
)
echo ✅ Entities created successfully!
echo.

echo [2/2] Setting up subscription...
echo ------------------------------------------------------------
python scripts\setup\setup_subscription.py

if %errorlevel% neq 0 (
    echo ❌ Failed to setup subscription!
    pause
    exit /b 1
)
echo ✅ Subscription setup successfully!
echo.

echo ============================================================
echo  ✅ ALL DONE!
echo ============================================================
pause
