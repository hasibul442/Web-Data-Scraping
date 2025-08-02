#!/usr/bin/env python3
"""
Project Setup and Verification Script
Checks dependencies, paths, and provides helpful setup information.
"""

import sys
import os
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print(f"❌ Python {version.major}.{version.minor} detected. Python 3.8+ is required.")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro} - Compatible")
    return True

def check_file_structure():
    """Verify the project structure is correct."""
    project_root = Path(__file__).parent
    
    required_dirs = [
        'src/core',
        'src/scrapers', 
        'src/utils',
        'src/media',
        'mongodb/config',
        'mongodb/importers',
        'tools/error_tracking',
        'tools/retry_system',
        'requirements',
        'output',
        'docs'
    ]
    
    missing_dirs = []
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if not full_path.exists():
            missing_dirs.append(dir_path)
        else:
            print(f"✅ Found: {dir_path}")
    
    if missing_dirs:
        print("\n❌ Missing directories:")
        for missing in missing_dirs:
            print(f"   - {missing}")
        return False
    
    return True

def check_requirements_files():
    """Check if requirements files exist."""
    project_root = Path(__file__).parent
    req_files = [
        'requirements/requirements.txt',
        'requirements/requirements_mongo.txt'
    ]
    
    for req_file in req_files:
        file_path = project_root / req_file
        if file_path.exists():
            print(f"✅ Found: {req_file}")
        else:
            print(f"❌ Missing: {req_file}")
            return False
    
    return True

def install_dependencies():
    """Install project dependencies."""
    project_root = Path(__file__).parent
    req_file = project_root / 'requirements' / 'requirements.txt'
    
    print(f"\n🔧 Installing dependencies from {req_file}")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', '-r', str(req_file)])
        print("✅ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def create_gitignore():
    """Create a .gitignore file if it doesn't exist."""
    project_root = Path(__file__).parent
    gitignore_path = project_root / '.gitignore'
    
    if gitignore_path.exists():
        print("✅ .gitignore already exists")
        return
    
    gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# PyInstaller
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.nox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
*.py,cover
.hypothesis/
.pytest_cache/
cover/

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# Project specific
output/*.json
output/*.txt
output/assets/
*.log
temp/
tmp/

# MongoDB
mongodb_data/
dump/

# OS
.DS_Store
Thumbs.db
"""
    
    gitignore_path.write_text(gitignore_content)
    print("✅ Created .gitignore file")

def main():
    """Main setup function."""
    print("=" * 60)
    print("🔧 Web Data Scraping - Project Setup & Verification")
    print("=" * 60)
    
    # Check Python version
    print("\n📋 Checking Python version...")
    if not check_python_version():
        return False
    
    # Check file structure
    print("\n📁 Checking project structure...")
    if not check_file_structure():
        print("\n❌ Project structure is incomplete.")
        print("Please ensure all required directories exist.")
        return False
    
    # Check requirements files
    print("\n📄 Checking requirements files...")
    if not check_requirements_files():
        return False
    
    # Create .gitignore
    print("\n📝 Setting up .gitignore...")
    create_gitignore()
    
    # Ask about dependency installation
    print("\n🔧 Dependency Installation")
    install = input("Install project dependencies? (y/n): ").strip().lower()
    if install in ['y', 'yes']:
        if not install_dependencies():
            return False
    
    print("\n" + "=" * 60)
    print("✅ Project setup completed successfully!")
    print("\n🚀 Quick Start Commands:")
    print("   1. Run scraper:        python run_scraper.py")
    print("   2. Download images:    python run_image_download.py")
    print("   3. Import to MongoDB:  python mongodb/run_mongo_import.py")
    print("   4. Check errors:       python tools/error_tracking/scan_404_errors.py")
    print("\n📚 Documentation: See docs/ directory for detailed guides")
    print("=" * 60)
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
