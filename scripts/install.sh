#!/bin/bash
#
# Quick Install Script for Oracle Test Library
#
# Usage:
#   ./install.sh
#   ./install.sh --user      # Install for current user only
#   ./install.sh --system    # Install system-wide (requires sudo)
#

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

print_status() { echo -e "${BLUE}==>${NC} $1"; }
print_success() { echo -e "${GREEN}✓${NC} $1"; }
print_error() { echo -e "${RED}✗${NC} $1"; }
print_warning() { echo -e "${YELLOW}⚠${NC} $1"; }

echo "================================================================"
echo "  Oracle Test Library - Quick Install"
echo "================================================================"
echo ""

# Check Python
print_status "Checking Python..."
if ! command -v python3 >/dev/null 2>&1; then
    print_error "Python 3 not found"
    echo "Please install Python 3.8 or higher"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
print_success "Python $PYTHON_VERSION found"

# Check pip
print_status "Checking pip..."
if ! python3 -m pip --version >/dev/null 2>&1; then
    print_error "pip not found"
    echo "Installing pip..."
    python3 -m ensurepip --default-pip || {
        print_error "Failed to install pip"
        echo "Please install pip manually"
        exit 1
    }
fi
print_success "pip is available"

# Check if we're in the right directory
if [ ! -f "oracle_test_lib.py" ] || [ ! -f "setup.py" ]; then
    print_error "Library files not found"
    echo ""
    echo "Please run this script from the library directory containing:"
    echo "  - oracle_test_lib.py"
    echo "  - setup.py"
    echo "  - requirements.txt"
    exit 1
fi

# Determine install method
INSTALL_METHOD="editable"
if [ "$1" = "--user" ]; then
    INSTALL_METHOD="user"
    print_status "Installing for current user only..."
elif [ "$1" = "--system" ]; then
    INSTALL_METHOD="system"
    print_status "Installing system-wide..."
else
    print_status "Installing in editable mode..."
fi

# Install
print_status "Installing oracle_test_lib..."

case $INSTALL_METHOD in
    editable)
        python3 -m pip install -e . || {
            print_error "Installation failed"
            echo ""
            echo "Try one of these alternatives:"
            echo "  ./install.sh --user      # Install for your user"
            echo "  pip install oracledb     # Install just the dependency"
            exit 1
        }
        ;;
    user)
        python3 -m pip install --user -e . || {
            print_error "Installation failed"
            exit 1
        }
        ;;
    system)
        sudo python3 -m pip install -e . || {
            print_error "Installation failed"
            exit 1
        }
        ;;
esac

print_success "Library installed"

# Verify
print_status "Verifying installation..."
if python3 -c "import oracle_test_lib" 2>/dev/null; then
    print_success "Installation verified"
else
    print_error "Import failed"
    echo ""
    echo "Troubleshooting:"
    echo "  1. Check PYTHONPATH: echo \$PYTHONPATH"
    echo "  2. Check installation: pip list | grep oracle"
    echo "  3. Try: export PYTHONPATH=\"\$(pwd):\$PYTHONPATH\""
    exit 1
fi

# Check dependencies
print_status "Checking dependencies..."
if python3 -c "import oracledb" 2>/dev/null; then
    print_success "oracledb is installed"
else
    print_warning "oracledb not found"
    print_status "Installing oracledb..."
    python3 -m pip install oracledb
    print_success "oracledb installed"
fi

# Success!
echo ""
echo "================================================================"
echo -e "${GREEN}Installation Complete!${NC}"
echo "================================================================"
echo ""
echo "Quick test:"
echo "  python -c \"from oracle_test_lib import OracleTestClient; print('✓ Working!')\""
echo ""
echo "Next steps:"
echo "  1. Set up Oracle database (Docker recommended)"
echo "  2. Run: ./setup_docker_tls_simple.sh"
echo "  3. Read: QUICKSTART.md"
echo ""
echo "Available tools:"
echo "  - oracle_test_cli.py         # Command-line interface"
echo "  - discover_oracle_services.py # Find database services"
echo "  - examples.py                 # Usage examples"
echo ""
echo "Documentation:"
echo "  - README.md              # Complete documentation"
echo "  - INSTALLATION.md        # Detailed install guide"
echo "  - DOCKER_QUICKSTART.md   # Docker setup"
echo "  - QUICKSTART.md          # 5-minute guide"
echo ""
echo "================================================================"
