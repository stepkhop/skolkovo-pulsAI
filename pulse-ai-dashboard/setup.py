from setuptools import find_packages, setup

setup(
    name="pulse-ai-dashboard",
    version="1.0.0",
    description="Pulse AI — дашборд метрик российской экосистемы ИИ",
    author="Pulse AI Team",
    python_requires=">=3.11",
    packages=find_packages(exclude=["tests", "tests.*"]),
    install_requires=[
        "pydantic>=2.0.0",
        "requests>=2.31.0",
        "pyyaml>=6.0.1",
        "streamlit>=1.28.0",
        "pandas>=2.0.0",
        "plotly>=5.18.0",
    ],
    entry_points={
        "console_scripts": [
            "pulse-ai=main:main",
        ],
    },
)