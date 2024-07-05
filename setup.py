import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="noroutine-grit",
    version="0.0.9",
    author='Oleksii Khilkevych',
    author_email="oleksiy@noroutine.me",
    maintainer="Noroutine GmbH",
    maintainer_email="info@noroutine.me",
    description='Grid Toolkit for Grafana',
    long_description=long_description,
    long_description_content_type='text/markdown',
    url='https://github.com/noroutine/grit',
    keywords='grafana, grafanalib, generator',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.9, <4',
    license="MIT",
    install_requires=[
        "attrs==21.4.0",
        "git+https://github.com/hawk-ai-aml/grafanalib.git@feature/grafana-11",
        "pydantic==1.9.1",
        "pydantic-argparse==0.5.0",
        "python-decouple==3.6",
        "python-dotenv==0.20.0",
        "PyYAML==6.0",
        "requests==2.28.0",
    ],
    package_dir={
        "": "src"
    }
)
