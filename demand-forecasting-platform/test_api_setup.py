"""
API Setup Verification Script
Tests if weather and economic APIs are properly configured
"""

import os
import sys
from pathlib import Path

def check_env_file():
    """Check if .env file exists"""
    print("=" * 70)
    print("STEP 1: Checking .env file")
    print("=" * 70)

    env_path = Path(".env")
    env_example_path = Path(".env.example")

    if not env_path.exists():
        print("❌ PROBLEM: .env file NOT found")
        print(f"   Looking in: {env_path.absolute()}")
        print("\n✅ FIX:")
        print("   Run this command:")
        print("   Copy-Item .env.example .env")
        return False

    print(f"✅ .env file exists: {env_path.absolute()}")
    return True


def check_api_keys():
    """Check if API keys are set in .env"""
    print("\n" + "=" * 70)
    print("STEP 2: Checking API keys in .env")
    print("=" * 70)

    env_path = Path(".env")

    try:
        with open(env_path, 'r') as f:
            content = f.read()

        # Check OpenWeather key
        openweather_set = False
        fred_set = False

        for line in content.split('\n'):
            if line.startswith('OPENWEATHER_API_KEY='):
                key = line.split('=', 1)[1].strip()
                if key and key != 'your_openweather_api_key_here':
                    print(f"✅ OpenWeather API key found: {key[:10]}...{key[-6:]}")
                    openweather_set = True
                else:
                    print("❌ OpenWeather API key NOT set (still placeholder)")
                    print("   Current value:", key)

            if line.startswith('FRED_API_KEY='):
                key = line.split('=', 1)[1].strip()
                if key and key != 'your_fred_api_key_here':
                    print(f"✅ FRED API key found: {key[:10]}...{key[-6:]}")
                    fred_set = True
                else:
                    print("❌ FRED API key NOT set (still placeholder)")
                    print("   Current value:", key)

        if not openweather_set or not fred_set:
            print("\n✅ FIX:")
            print("   1. Open .env file: notepad .env")
            print("   2. Find these lines:")
            print("      OPENWEATHER_API_KEY=your_openweather_api_key_here")
            print("      FRED_API_KEY=your_fred_api_key_here")
            print("   3. Replace with your actual API keys")
            print("   4. Save the file")
            return False

        return True
    except Exception as e:
        print(f"❌ Error reading .env: {e}")
        return False


def check_environment_variables():
    """Check if environment variables are loaded"""
    print("\n" + "=" * 70)
    print("STEP 3: Checking environment variables")
    print("=" * 70)

    # Try to load from .env manually
    from pathlib import Path
    env_path = Path(".env")

    if env_path.exists():
        with open(env_path, 'r') as f:
            for line in f:
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.strip().split('=', 1)
                    if key and value:
                        os.environ[key] = value

    openweather_key = os.getenv('OPENWEATHER_API_KEY')
    fred_key = os.getenv('FRED_API_KEY')

    if openweather_key and openweather_key != 'your_openweather_api_key_here':
        print(f"✅ OPENWEATHER_API_KEY loaded: {openweather_key[:10]}...{openweather_key[-6:]}")
    else:
        print("❌ OPENWEATHER_API_KEY not loaded or still placeholder")
        print(f"   Current value: {openweather_key}")

    if fred_key and fred_key != 'your_fred_api_key_here':
        print(f"✅ FRED_API_KEY loaded: {fred_key[:10]}...{fred_key[-6:]}")
    else:
        print("❌ FRED_API_KEY not loaded or still placeholder")
        print(f"   Current value: {fred_key}")

    return bool(openweather_key and fred_key and
                openweather_key != 'your_openweather_api_key_here' and
                fred_key != 'your_fred_api_key_here')


def check_api_connectors():
    """Check if API connector modules can be imported"""
    print("\n" + "=" * 70)
    print("STEP 4: Checking API connector modules")
    print("=" * 70)

    try:
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from services.data_connectors import get_weather_api, get_economic_api
        print("✅ API connector modules imported successfully")
        return True, get_weather_api, get_economic_api
    except ImportError as e:
        print(f"❌ Failed to import API connectors: {e}")
        print("\n✅ FIX:")
        print("   Run: git pull origin claude/ml-commodity-ordering-xnRRS")
        return False, None, None


def test_weather_api(get_weather_api):
    """Test if weather API actually works"""
    print("\n" + "=" * 70)
    print("STEP 5: Testing OpenWeather API")
    print("=" * 70)

    try:
        weather_api = get_weather_api()

        if not weather_api:
            print("❌ Weather API not initialized")
            return False

        # Test API call
        print("   Fetching current weather for Atlanta...")
        result = weather_api.get_current_weather("Atlanta")

        if result.get('_mock'):
            print("❌ Receiving MOCK data (API key not working)")
            print("   Possible issues:")
            print("   - API key is invalid")
            print("   - API key hasn't activated yet (wait 10 minutes)")
            print("   - Network/firewall blocking the request")
            return False

        print("✅ REAL weather data received!")
        print(f"   Temperature in Atlanta: {result['temperature']:.1f}°F")
        print(f"   Conditions: {result['description']}")
        print(f"   Humidity: {result['humidity']}%")
        return True

    except Exception as e:
        print(f"❌ Weather API test failed: {e}")
        return False


def test_economic_api(get_economic_api):
    """Test if economic API actually works"""
    print("\n" + "=" * 70)
    print("STEP 6: Testing FRED Economic API")
    print("=" * 70)

    try:
        economic_api = get_economic_api()

        if not economic_api:
            print("❌ Economic API not initialized")
            return False

        # Test API call
        print("   Fetching unemployment rate...")
        result = economic_api.get_unemployment_rate()

        if result.get('_mock'):
            print("❌ Receiving MOCK data (API key not working)")
            print("   Possible issues:")
            print("   - API key is invalid")
            print("   - API key not approved yet")
            print("   - Network/firewall blocking the request")
            return False

        print("✅ REAL economic data received!")
        print(f"   Unemployment Rate: {result['latest_value']:.1f}%")
        print(f"   Date: {result['latest_date']}")
        return True

    except Exception as e:
        print(f"❌ Economic API test failed: {e}")
        return False


def main():
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 15 + "API SETUP VERIFICATION TEST" + " " * 25 + "║")
    print("╚" + "=" * 68 + "╝")
    print()

    results = {}

    # Step 1: Check .env file
    results['env_file'] = check_env_file()

    if not results['env_file']:
        print("\n" + "=" * 70)
        print("STOPPING: Fix .env file issue first")
        print("=" * 70)
        return

    # Step 2: Check API keys in .env
    results['api_keys'] = check_api_keys()

    # Step 3: Check environment variables
    results['env_vars'] = check_environment_variables()

    # Step 4: Check API connectors
    results['connectors'], get_weather_api, get_economic_api = check_api_connectors()

    # Step 5 & 6: Test APIs (only if keys are set)
    if results['connectors'] and results['env_vars']:
        results['weather_api'] = test_weather_api(get_weather_api)
        results['economic_api'] = test_economic_api(get_economic_api)
    else:
        results['weather_api'] = False
        results['economic_api'] = False

    # Final summary
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 27 + "FINAL SUMMARY" + " " * 28 + "║")
    print("╚" + "=" * 68 + "╝")
    print()

    all_passed = all(results.values())

    if all_passed:
        print("🎉 " + "=" * 66)
        print("   ALL TESTS PASSED! Your APIs are properly configured!")
        print("=" * 70)
        print()
        print("Next steps:")
        print("   1. Restart your Streamlit app: streamlit run app.py")
        print("   2. Go to Settings page in the UI")
        print("   3. You should see green checkmarks for both APIs!")
    else:
        print("⚠️  " + "=" * 66)
        print("   SOME TESTS FAILED - See details above")
        print("=" * 70)
        print()
        print("Common fixes:")

        if not results.get('env_file'):
            print("   • Create .env file: Copy-Item .env.example .env")

        if not results.get('api_keys') or not results.get('env_vars'):
            print("   • Edit .env and add your real API keys")
            print("   • Make sure to edit .env (NOT .env.example)")

        if not results.get('connectors'):
            print("   • Pull latest code: git pull origin claude/ml-commodity-ordering-xnRRS")

        if not results.get('weather_api'):
            print("   • OpenWeather key: Get from https://openweathermap.org/api")
            print("   • Wait 10 minutes for new keys to activate")

        if not results.get('economic_api'):
            print("   • FRED key: Get from https://fred.stlouisfed.org/docs/api/api_key.html")

    print()


if __name__ == "__main__":
    main()
