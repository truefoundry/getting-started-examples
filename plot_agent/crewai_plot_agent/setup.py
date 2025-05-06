from setuptools import setup, find_packages

setup(
    name="crewai_plot_agent",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "fastapi",
        "uvicorn",
        "crewai",
        "pydantic",
        "traceloop",
    ],
) 