from setuptools import setup, find_packages

# Read the contents of your README file
from pathlib import Path
this_directory = Path(__file__).parent
long_description = (this_directory / "README.md").read_text(encoding='utf-8')

setup(
    name='soup3D',
    version='4.2.1',
    author='OrangeSoup',
    author_email='deanliusy@163.com',
    description='A 3D engine based on OpenGL and pygame for beginners',
    long_description=long_description,
    long_description_content_type='text/markdown',
    packages=find_packages(),
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.8',
        'Programming Language :: Python :: 3.9',
        'Programming Language :: Python :: 3.10',
        'Programming Language :: Python :: 3.11',
        'Topic :: Multimedia :: Graphics :: 3D Rendering',
        'Topic :: Software Development :: Libraries :: Python Modules',
    ],
    python_requires='>=3.8',
    install_requires=[
        'PyOpenGL',
        'pyglm',
        'Pillow',
        'numpy',
        'pygame'
    ],
    package_data={
        'soup3D': ['*.md', 'LICENSE', 'help.md', '*.png'],
    },
    include_package_data=True,
    keywords='3D, OpenGL, pygame, graphics, game development',
)
