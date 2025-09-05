# 🚀 Quick Start: Publishing apicrafter to PyPI

## Prerequisites

1. **Create PyPI accounts**:
   - [PyPI](https://pypi.org/account/register/) - Production
   - [TestPyPI](https://test.pypi.org/account/register/) - Testing

2. **Get API tokens**:
   - Go to Account Settings → API tokens
   - Create tokens for both PyPI and TestPyPI
   - Save them securely

## 🎯 Quick Publishing Steps

### Option 1: Automated (Recommended)

1. **Set up GitHub Secrets**:
   - Go to your GitHub repository settings
   - Navigate to Secrets and Variables → Actions
   - Add these secrets:
     - `PYPI_API_TOKEN`: Your PyPI API token
     - `TEST_PYPI_API_TOKEN`: Your TestPyPI API token

2. **Create a release**:
   ```bash
   # Update version in pyproject.toml if needed
   git add .
   git commit -m "Prepare for release v0.1.0"
   git tag v0.1.0
   git push origin main --tags
   ```

3. **GitHub Actions will automatically**:
   - Run tests
   - Build the package
   - Publish to TestPyPI
   - Publish to PyPI
   - Create a GitHub release

### Option 2: Manual Publishing

1. **Test locally**:
   ```bash
   # Clean and build
   make clean
   make build
   
   # Test the package
   make test-publish
   ```

2. **Publish to PyPI**:
   ```bash
   # Interactive publishing
   make publish
   
   # Or use the script directly
   ./scripts/publish.sh
   ```

## 📋 What's Already Set Up

✅ **Complete PyPI configuration** in `pyproject.toml`
✅ **GitHub Actions workflow** for automated publishing
✅ **Publishing scripts** with error handling and validation
✅ **Makefile** with convenient commands
✅ **Comprehensive documentation** in `PUBLISHING.md`
✅ **Package validation** and testing

## 🔧 Available Commands

```bash
# Development
make install-dev    # Install with dev dependencies
make test          # Run tests
make lint          # Run linting
make format        # Format code

# Building
make build         # Build package
make clean         # Clean artifacts

# Publishing
make test-publish  # Publish to TestPyPI only
make publish       # Publish to PyPI (interactive)
make dry-run       # Show what would be published
```

## 🎉 You're Ready!

Your apicrafter project is fully configured for PyPI publishing. Choose your preferred method and start sharing your amazing API client with the world!

**Next steps after publishing**:
1. Verify installation: `pip install apicrafter`
2. Test the CLI: `apicrafter --help`
3. Share with the community! 🚀
