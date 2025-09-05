# 📦 Publishing apicrafter to PyPI

This guide covers everything you need to publish your apicrafter package to PyPI (Python Package Index).

## 🚀 Quick Start

### Prerequisites

1. **PyPI Account**: Create accounts on both PyPI and TestPyPI
   - [PyPI](https://pypi.org/account/register/) - Production releases
   - [TestPyPI](https://test.pypi.org/account/register/) - Testing releases

2. **API Tokens**: Generate API tokens for both platforms
   - Go to Account Settings → API tokens
   - Create a new token with appropriate scope
   - Save the tokens securely

3. **Required Tools**: Install build and upload tools
   ```bash
   pip install build twine
   ```

## 📋 Publishing Steps

### 1. Prepare for Release

```bash
# Ensure you're in the project directory
cd /home/yash-singh/Documents/apix

# Activate virtual environment
source venv/bin/activate

# Update version in pyproject.toml (if needed)
# Edit the version field in [project] section
```

### 2. Clean and Test

```bash
# Clean previous builds
rm -rf build/ dist/ *.egg-info/

# Run tests
pytest

# Check code quality
black apicrafter/ --check
isort apicrafter/ --check-only
mypy apicrafter/
```

### 3. Build the Package

```bash
# Build source distribution and wheel
python -m build

# Verify the build
twine check dist/*
```

### 4. Test on TestPyPI (Recommended)

```bash
# Upload to TestPyPI first
twine upload --repository testpypi dist/*

# Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ apicrafter

# Test the installation
apicrafter --help
```

### 5. Publish to PyPI

```bash
# Upload to production PyPI
twine upload dist/*

# Verify installation from PyPI
pip install apicrafter
apicrafter --help
```

## 🔄 Automated Publishing with GitHub Actions

The project includes a GitHub Actions workflow for automated publishing:

### Setup GitHub Secrets

1. Go to your GitHub repository settings
2. Navigate to Secrets and Variables → Actions
3. Add the following secrets:
   - `PYPI_API_TOKEN`: Your PyPI API token
   - `TEST_PYPI_API_TOKEN`: Your TestPyPI API token

### Workflow Features

- **Automatic versioning**: Uses git tags for version management
- **Dual publishing**: Publishes to both TestPyPI and PyPI
- **Quality checks**: Runs tests and linting before publishing
- **Manual trigger**: Can be triggered manually or on tag creation

### Triggering a Release

```bash
# Create and push a tag
git tag v0.1.0
git push origin v0.1.0

# Or trigger manually from GitHub Actions tab
```

## 📝 Version Management

### Semantic Versioning

Follow [Semantic Versioning](https://semver.org/) principles:
- `MAJOR.MINOR.PATCH` (e.g., 1.0.0)
- `MAJOR`: Breaking changes
- `MINOR`: New features (backward compatible)
- `PATCH`: Bug fixes (backward compatible)

### Updating Version

1. **Edit pyproject.toml**:
   ```toml
   [project]
   version = "0.2.0"  # Update this
   ```

2. **Commit and tag**:
   ```bash
   git add pyproject.toml
   git commit -m "Bump version to 0.2.0"
   git tag v0.2.0
   git push origin main --tags
   ```

## 🛠️ Development Workflow

### Local Development

```bash
# Install in development mode
pip install -e .

# Run tests
pytest

# Format code
black apicrafter/
isort apicrafter/

# Type checking
mypy apicrafter/
```

### Pre-release Testing

```bash
# Create a pre-release version
# Edit pyproject.toml: version = "0.2.0a1"

# Build and test
python -m build
twine upload --repository testpypi dist/*

# Test installation
pip install --index-url https://test.pypi.org/simple/ apicrafter==0.2.0a1
```

## 🔍 Troubleshooting

### Common Issues

1. **"Package already exists"**
   - Solution: Increment version number in pyproject.toml

2. **"Invalid distribution"**
   - Solution: Run `twine check dist/*` to validate

3. **"Authentication failed"**
   - Solution: Check API token and ensure it's correctly set

4. **"Missing dependencies"**
   - Solution: Ensure all dependencies are listed in pyproject.toml

### Validation Commands

```bash
# Check package metadata
python -m build --sdist --wheel
twine check dist/*

# Test installation
pip install dist/apicrafter-*.whl

# Verify CLI works
apicrafter --help
```

## 📊 Post-Publication

### Verify Publication

1. **Check PyPI page**: https://pypi.org/project/apicrafter/
2. **Test installation**: `pip install apicrafter`
3. **Test CLI**: `apicrafter --help`

### Update Documentation

1. **Update README**: Add PyPI installation instructions
2. **GitHub releases**: Create a release with changelog
3. **Documentation**: Update any external documentation

### Monitor Usage

- **PyPI statistics**: Check download counts
- **GitHub insights**: Monitor repository activity
- **Issue tracking**: Respond to user feedback

## 🎯 Best Practices

### Before Publishing

- [ ] All tests pass
- [ ] Code is properly formatted
- [ ] Documentation is up to date
- [ ] Version is incremented
- [ ] Changelog is updated
- [ ] Tested on TestPyPI

### After Publishing

- [ ] Verify installation works
- [ ] Test CLI functionality
- [ ] Update documentation
- [ ] Create GitHub release
- [ ] Announce on social media/forums

## 📚 Additional Resources

- [PyPI Packaging Guide](https://packaging.python.org/tutorials/packaging-projects/)
- [Twine Documentation](https://twine.readthedocs.io/)
- [GitHub Actions for Python](https://docs.github.com/en/actions/guides/building-and-testing-python)
- [Semantic Versioning](https://semver.org/)

---

**Happy Publishing! 🚀**
