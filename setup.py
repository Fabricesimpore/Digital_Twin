"""
Digital Twin - Intelligent Personal Assistant
Setup configuration for package installation
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text()

# Read requirements
requirements = []
with open('requirements_consolidated.txt') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and not line.startswith('-'):
            requirements.append(line)

setup(
    name="digital-twin",
    version="0.8.0",
    author="Fabrice Simpore",
    author_email="your-email@example.com",
    description="AI-powered autonomous agent with human oversight for critical decisions",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/Fabricesimpore/Digital_Twin",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Office/Business",
        "Topic :: System :: Monitoring",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-asyncio>=0.21.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=1.0.0",
        ],
        "full": [
            "google-api-python-client>=2.0.0",
            "google-auth-oauthlib>=1.0.0",
            "fastapi>=0.100.0",
            "uvicorn>=0.23.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "digital-twin=backend.core.twin_decision_loop:main",
            "twin-cli=backend.core.cli_extensions:main",
            "twin-validate=backend.core.run_validations:main",
        ],
    },
    include_package_data=True,
    package_data={
        "": ["*.yaml", "*.yml", "*.json", "*.md", "*.txt"],
    },
    keywords="ai assistant automation human-in-the-loop decision-making productivity",
    project_urls={
        "Bug Reports": "https://github.com/Fabricesimpore/Digital_Twin/issues",
        "Source": "https://github.com/Fabricesimpore/Digital_Twin",
        "Documentation": "https://github.com/Fabricesimpore/Digital_Twin#readme",
    },
)