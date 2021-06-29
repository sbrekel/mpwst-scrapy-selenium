from setuptools import setup, find_packages

setup(
    name='scrapy_selenium',
    version='0.0.9',
    description='Selenium Middleware for Scrapy that allow for multiple concurrent headless browsers.',
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    keywords='scrapy selenium middleware webdriver web-scraping',
    license='MIT',
    author='Dylan Walker',
    author_email='dylan.travis.walker@gmail.com',
    maintainer='Dylan Walker',
    maintainer_email='dylan.travis.walker@gmail.com',
    url='https://github.com/dylanwalker/better-scrapy-selenium',
    python_requires='>=3.5',
    packages=find_packages(),
    install_requires=[
        "scrapy>=1.0.0",
        "selenium>=3.0.0"
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Operating System :: OS Independent",
    ],
    extras_require={
        "dev": [
            "pytest>=3.7",
        ]
    }
)
