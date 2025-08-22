from setuptools import setup, find_packages

setup(
    name="market-dashboards",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "streamlit>=1.47.0",
        "pandas>=2.0.0",
        "numpy>=1.20.0",
        "plotly>=5.0.0",
        "altair>=5.0.0",
        "duckdb>=1.0.0",
        "requests>=2.25.0",
        "python-decouple>=3.0.0",
        "cryptography>=3.0.0",
    ],
    python_requires=">=3.8",
)
