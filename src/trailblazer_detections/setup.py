from setuptools import setup, find_packages
from glob import glob

package_name = 'trailblazer_detections'

setup(
    name=package_name,
    version='0.0.1',
    packages=find_packages(),
    data_files=[
        ('share/ament_index/resource_index/packages', 
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        ('share/' + package_name + '/models', glob('models/*.pt')),
        ('share/' + package_name + '/launch', glob('launch/*.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='walkowiczf',
    maintainer_email='fillio00@wp.pl',
    description='TODO: Package description',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            'yolo_node = trailblazer_detections.yolo_node:main'
        ],
    },
)
