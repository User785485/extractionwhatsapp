"""Setup script for WhatsApp Extractor v2"""

from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of README file
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

# Read requirements
requirements = []
with open('requirements.txt', 'r') as f:
    for line in f:
        line = line.strip()
        if line and not line.startswith('#') and not line.startswith('-'):
            # Remove version specifiers for setup.py
            req = line.split('>=')[0].split('==')[0].split('#')[0].strip()
            if req != 'sqlite3':  # Skip built-in modules
                requirements.append(req)

setup(
    name="whatsapp-extractor-v2",
    version="2.0.0",
    author="WhatsApp Extractor Team",
    author_email="",
    description="Professional WhatsApp data extraction and transcription tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/your-username/whatsapp-extractor-v2",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Communications :: Chat",
        "Topic :: Multimedia :: Sound/Audio :: Conversion",
        "Topic :: Text Processing :: Markup :: HTML",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=1.0.0",
        ]
    },
    entry_points={
        "console_scripts": [
            "whatsapp-extractor=src.main:cli",
        ],
    },
    include_package_data=True,
    zip_safe=False,
)