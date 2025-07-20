FROM arm64v8/ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=en_US.UTF-8
ENV LC_ALL=en_US.UTF-8
ENV ROS_PYTHON_VERSION=3
ENV ROS_DISTRO=humble

RUN apt-get update && apt-get install -y \
    curl \
    locales \
    software-properties-common \
    git \
    build-essential \
    libssl-dev \
    zlib1g-dev \
    libbz2-dev \
    libreadline-dev \
    libsqlite3-dev \
    wget \
    llvm \
    libncursesw5-dev \
    xz-utils \
    tk-dev \
    libxml2-dev \
    libxmlsec1-dev \
    libffi-dev \
    ca-certificates \
    gpg \
    python3.10 \
    python3.10-dev \
    python3.10-venv \
    python3-pip \
    && locale-gen en_US.UTF-8 \
    && update-locale LC_ALL=en_US.UTF-8 LANG=en_US.UTF-8 \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir numpy lxml

RUN add-apt-repository universe \
    && curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg

RUN echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu jammy main" > /etc/apt/sources.list.d/ros2.list

RUN apt-get update && apt-get install -y \
    python3-flake8-docstrings \
    python3-pytest-cov \
    python3-flake8-blind-except \
    python3-flake8-builtins \
    python3-flake8-class-newline \
    python3-flake8-comprehensions \
    python3-flake8-deprecated \
    python3-flake8-import-order \
    python3-flake8-quotes \
    python3-pytest-repeat \
    python3-pytest-rerunfailures \
    python3-colcon-common-extensions \
    python3-rosdep \
    gz-fortress \
    ros-humble-desktop \
    ros-dev-tools \
    ros-humble-position-controllers \
    ros-humble-xacro \
    ros-humble-twist-mux \
    ros-humble-rviz2 \
    joystick \
    jstest-gtk \
    evtest \
    apt-transport-https \
    terminator \
    && rosdep init \
    && rosdep update \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

COPY . /TrailblazerML/

RUN echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc \
    && echo "source /usr/share/colcon_argcomplete/hook/colcon-argcomplete.bash" >> ~/.bashrc \
    && bash -c "source ~/.bashrc"

RUN apt-get update

COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/bin/bash","/entrypoint.sh"]

CMD ["bash"]