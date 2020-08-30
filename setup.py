import os
from setuptools import setup

with open("README.md", "r") as fh:
    README = fh.read()

# allow setup.py to be run from any path
os.chdir(os.path.normpath(os.path.join(os.path.abspath(__file__), os.pardir)))

setup(
    name="django-stagedoor",
    version="0.0.3",
    zip_safe=False,
    packages=["stagedoor"],
    author="Philip James",
    author_email="phildini@phildini.net",
    license="Apache License",
    description="A Django app for passwordless login with SMS and Email",
    include_package_data=True,
    long_description=README,
    long_description_content_type="text/markdown",
    install_requires=[
        "twilio>=6.40.0,<6.50.0",
        "django>=2.2,<4.0",
        "django-phonenumber-field>=4.0.0,<4.1.0",
        "phonenumbers>=8.12.0,<8.13",
    ],
    url="https://github.com/galaxybrainco/django-stagedoor",
    classifiers=[
        "Environment :: Web Environment",
        "Framework :: Django",
        "Intended Audience :: Developers",
        "Operating System :: OS Independent",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Topic :: Internet :: WWW/HTTP",
    ],
    python_requires=">=3.6",
)
