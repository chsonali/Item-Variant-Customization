from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in core_frappe/__init__.py
from core_frappe import __version__ as version

setup(
	name="core_frappe",
	version=version,
	description="Customization",
	author="Customization",
	author_email="chsonali225@gmail.com",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
