# Installation Guide - Oracle Test Library

## Quick Install

### Option 1: Install from Source (Recommended)

```bash
# Clone or download the library files
# Navigate to the directory containing setup.py

# Install in development mode
pip install -e .

# Or install with all optional dependencies
pip install -e ".[all]"
```

### Option 2: Install Dependencies Manually

If you don't want to use setup.py:

```bash
pip install oracledb
```

That's it! The library has minimal dependencies.

---

## Detailed Installation Steps

### Step 1: Verify Python

```bash
# Check Python version (need 3.8+)
python --version
# or
python3 --version

# Should show: Python 3.8.x or higher
```

### Step 2: Create Virtual Environment (Recommended)

```bash
# Create virtual environment
python3 -m venv oracle-test-env

# Activate it
# On Linux/macOS:
source oracle-test-env/bin/activate

# On Windows:
oracle-test-env\Scripts\activate

# Your prompt should now show (oracle-test-env)
```

### Step 3: Install the Library

#### Method A: Using setup.py (Recommended)

```bash
# Navigate to library directory
cd /path/to/oracle-test-library

# Install in editable mode
pip install -e .

# Verify installation
python -c "import oracle_test_lib; print('✓ Library installed')"
```

#### Method B: Direct Installation

If setup.py doesn't work or you just have the files:

```bash
# Install dependencies
pip install oracledb

# Add library directory to Python path
export PYTHONPATH="/path/to/oracle-test-library:$PYTHONPATH"

# Or on Windows:
set PYTHONPATH=C:\path\to\oracle-test-library;%PYTHONPATH%

# Verify
python -c "import oracle_test_lib; print('✓ Library imported')"
```

#### Method C: Copy Files to Site-Packages

```bash
# Find your site-packages directory
python -c "import site; print(site.getsitepackages())"

# Copy the library file
cp oracle_test_lib.py /path/to/site-packages/

# Verify
python -c "import oracle_test_lib; print('✓ Library installed')"
```

### Step 4: Verify Installation

```bash
# Test import
python -c "from oracle_test_lib import OracleTestClient, LoadProfile; print('✓ All imports working')"

# Check version
python -c "import oracle_test_lib; print('Library loaded successfully')"

# Run discovery script (if using Docker)
python discover_oracle_services.py --help
```

---

## Installing for Different Use Cases

### For Docker Testing

```bash
# Install library
pip install -e .

# Run Docker setup
./setup_docker_tls_simple.sh

# Test
cd docker-tls-simple
python test_tls_simple.py
```

### For CI/CD Pipelines

```bash
# In your CI config (e.g., .github/workflows/test.yml)
- name: Install dependencies
  run: |
    pip install oracledb
    pip install -e .

- name: Run tests
  run: |
    python -m pytest tests/
```

### For System-Wide Installation

```bash
# Install globally (may need sudo)
sudo pip install -e .

# Or install just for your user
pip install --user -e .
```

---

## Troubleshooting Installation

### Issue: "pip: command not found"

```bash
# Install pip
# On Ubuntu/Debian:
sudo apt-get install python3-pip

# On macOS:
python3 -m ensurepip

# On Windows:
# Download get-pip.py from https://bootstrap.pypa.io/get-pip.py
python get-pip.py
```

### Issue: "No module named 'setuptools'"

```bash
pip install --upgrade setuptools wheel
```

### Issue: "Permission denied" when installing

```bash
# Option 1: Use virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate
pip install -e .

# Option 2: Install for user only
pip install --user -e .

# Option 3: Use sudo (not recommended)
sudo pip install -e .
```

### Issue: "setup.py not found"

You might be in the wrong directory:

```bash
# List files to check
ls -la

# Should see:
# - oracle_test_lib.py
# - setup.py
# - requirements.txt
# - README.md

# If not, navigate to correct directory
cd /path/to/oracle-test-library
```

### Issue: "oracledb installation fails"

```bash
# Install build dependencies first
# On Ubuntu/Debian:
sudo apt-get install build-essential python3-dev

# On macOS:
xcode-select --install

# Then try again
pip install oracledb
```

### Issue: "ModuleNotFoundError: No module named 'oracle_test_lib'"

```bash
# Check if installed
pip list | grep oracle

# If not found, reinstall
pip install -e .

# Or check PYTHONPATH
echo $PYTHONPATH

# Add current directory to path temporarily
export PYTHONPATH="$(pwd):$PYTHONPATH"
python your_script.py
```

---

## Quick Fix: Run Without Installation

If you can't install for some reason, you can run scripts directly:

```bash
# Make sure you're in the directory with oracle_test_lib.py
cd /path/to/library

# Run Python with the current directory in path
PYTHONPATH=. python your_script.py

# Or from Python:
import sys
sys.path.insert(0, '/path/to/library')
from oracle_test_lib import OracleTestClient
```

---

## Installation in Different Environments

### Docker Container

```dockerfile
FROM python:3.11-slim

# Install dependencies
RUN pip install oracledb

# Copy library
COPY oracle_test_lib.py /app/
COPY setup.py /app/
WORKDIR /app

# Install
RUN pip install -e .

# Your application
COPY your_script.py /app/
CMD ["python", "your_script.py"]
```

### Virtual Environment

```bash
# Create and activate
python3 -m venv .venv
source .venv/bin/activate

# Install
pip install -e .

# When done
deactivate
```

### Conda Environment

```bash
# Create conda environment
conda create -n oracle-test python=3.11
conda activate oracle-test

# Install
pip install -e .
```

---

## Verifying Everything Works

### Complete Test

```bash
# 1. Check Python
python --version

# 2. Check library import
python -c "import oracle_test_lib; print('✓ Library OK')"

# 3. Check dependencies
python -c "import oracledb; print('✓ oracledb OK')"

# 4. Check CLI tools
python oracle_test_cli.py --help

# 5. Check discovery tool
python discover_oracle_services.py --help

# If all pass, you're ready!
```

### Run Example

```bash
# Test connection discovery
python discover_oracle_services.py --host localhost --port 1521

# Or run an example
python -c "
from oracle_test_lib import OracleTestClient
print('✓ Library is working!')
print('Available functions:')
print('  - test_connection()')
print('  - discover_services()')
print('  - OracleTestClient()')
"
```

---

## Installation Commands Summary

```bash
# Quick install
pip install -e .

# With virtual environment
python3 -m venv venv && source venv/bin/activate && pip install -e .

# Manual dependency install
pip install oracledb

# Verify
python -c "import oracle_test_lib; print('✓ Installed')"

# Run Docker setup
./setup_docker_tls_simple.sh
```

---

## Next Steps After Installation

1. **Test Connection:**
   ```bash
   python discover_oracle_services.py --host localhost
   ```

2. **Run Docker Setup (if using Docker):**
   ```bash
   ./setup_docker_tls_simple.sh
   ```

3. **Run Examples:**
   ```bash
   python examples.py
   ```

4. **Read Documentation:**
   - README.md - Main documentation
   - QUICKSTART.md - 5-minute guide
   - DOCKER_QUICKSTART.md - Docker guide

---

## Getting Help

If installation still fails:

1. **Check Python version:** Must be 3.8+
2. **Check pip version:** `pip --version`
3. **Try virtual environment:** Isolates dependencies
4. **Check error message:** Most errors are self-explanatory
5. **Check PYTHONPATH:** Make sure it includes library location

**Still stuck?** Copy the error message and the output of:
```bash
python --version
pip --version
pip list
ls -la
pwd
```
