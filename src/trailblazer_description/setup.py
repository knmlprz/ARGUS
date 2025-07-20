from setuptools import find_packages, setup
from glob import glob

package_name = 'trailblazer_description'

setup(
    name=package_name,
    version='0.0.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/urdf', glob('urdf/*.xacro')),
        ('share/' + package_name + '/urdf/include', glob('urdf/include/*.xacro')),
        ('share/' + package_name + '/meshes', glob('meshes/*.STL')),
        ('share/' + package_name + '/launch', glob('launch/*.py')),
        ('share/' + package_name + '/config', glob('config/*.yaml')),

    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='walkowiczf',
    maintainer_email='fillio00@wp.pl',
    description='TODO: Package description',
    entry_points={
        'console_scripts': [
        ],
    },
)
