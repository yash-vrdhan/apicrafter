#!/bin/bash
# Publishing script for apicrafter

set -e  # Exit on any error

echo "🚀 Starting apicrafter publishing process..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    print_error "pyproject.toml not found. Please run this script from the project root."
    exit 1
fi

# Check if virtual environment is activated
if [ -z "$VIRTUAL_ENV" ]; then
    print_warning "Virtual environment not detected. Activating venv..."
    if [ -f "venv/bin/activate" ]; then
        source venv/bin/activate
        print_success "Virtual environment activated"
    else
        print_error "Virtual environment not found. Please create one first:"
        print_error "python -m venv venv && source venv/bin/activate"
        exit 1
    fi
fi

# Parse command line arguments
DRY_RUN=false
TEST_ONLY=false
SKIP_TESTS=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --dry-run)
            DRY_RUN=true
            shift
            ;;
        --test-only)
            TEST_ONLY=true
            shift
            ;;
        --skip-tests)
            SKIP_TESTS=true
            shift
            ;;
        --help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --dry-run     Show what would be done without actually doing it"
            echo "  --test-only   Only test on TestPyPI, don't publish to PyPI"
            echo "  --skip-tests  Skip running tests before publishing"
            echo "  --help        Show this help message"
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Get current version
CURRENT_VERSION=$(python -c "import tomllib; print(tomllib.load(open('pyproject.toml', 'rb'))['project']['version'])")
print_status "Current version: $CURRENT_VERSION"

# Clean previous builds
print_status "Cleaning previous builds..."
rm -rf build/ dist/ *.egg-info/

# Install/upgrade build tools
print_status "Installing build tools..."
pip install --upgrade pip build twine

# Run tests unless skipped
if [ "$SKIP_TESTS" = false ]; then
    print_status "Running tests..."
    if command -v pytest &> /dev/null; then
        pytest tests/ -v
        print_success "Tests passed"
    else
        print_warning "pytest not found, skipping tests"
    fi
    
    # Run linting
    print_status "Running code quality checks..."
    if command -v black &> /dev/null; then
        black apicrafter/ --check
        print_success "Black formatting check passed"
    fi
    
    if command -v isort &> /dev/null; then
        isort apicrafter/ --check-only
        print_success "Import sorting check passed"
    fi
    
    if command -v mypy &> /dev/null; then
        mypy apicrafter/
        print_success "Type checking passed"
    fi
fi

# Build the package
print_status "Building package..."
python -m build

# Check the package
print_status "Checking package..."
twine check dist/*

if [ "$DRY_RUN" = true ]; then
    print_warning "DRY RUN: Would publish the following files:"
    ls -la dist/
    exit 0
fi

# Publish to TestPyPI
print_status "Publishing to TestPyPI..."
twine upload --repository testpypi dist/*

print_success "Published to TestPyPI successfully!"
print_status "You can test the installation with:"
print_status "pip install --index-url https://test.pypi.org/simple/ apicrafter"

# Test installation from TestPyPI
print_status "Testing installation from TestPyPI..."
pip install --index-url https://test.pypi.org/simple/ apicrafter
if apicrafter --help > /dev/null 2>&1; then
    print_success "TestPyPI installation works correctly"
else
    print_error "TestPyPI installation failed"
    exit 1
fi

if [ "$TEST_ONLY" = true ]; then
    print_success "Test-only mode: Stopping here. Package published to TestPyPI only."
    exit 0
fi

# Ask for confirmation before publishing to PyPI
echo ""
print_warning "About to publish to production PyPI!"
print_warning "This will make the package available to everyone."
echo ""
read -p "Are you sure you want to continue? (y/N): " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_status "Publishing cancelled. Package is available on TestPyPI for testing."
    exit 0
fi

# Publish to PyPI
print_status "Publishing to PyPI..."
twine upload dist/*

print_success "🎉 Successfully published apicrafter $CURRENT_VERSION to PyPI!"
print_status "Package URL: https://pypi.org/project/apicrafter/"
print_status "Installation: pip install apicrafter"

# Test final installation
print_status "Testing final installation..."
pip install apicrafter
if apicrafter --help > /dev/null 2>&1; then
    print_success "Final installation test passed"
else
    print_error "Final installation test failed"
    exit 1
fi

print_success "🚀 Publishing process completed successfully!"
