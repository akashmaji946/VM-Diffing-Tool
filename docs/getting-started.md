# Getting Started

0. Download the repository:
```bash
git clone https://github.com/akashmaji/VM-Diffing-Tool.git
```

1. Install dependencies:
```bash
python3 -m pip install --upgrade pip setuptools wheel
sudo apt update && sudo apt upgrade -y
sudo apt install -y \
    build-essential \
    cmake \
    g++ \
    git \
    python3.10 \
    python3.10-dev \
    python3-pip \
    libguestfs-dev \
    libguestfs-tools \
    python3-guestfs \
    libguestfs0 \
    qemu-utils \
    sqlite3 \
    libsqlite3-dev \
    linux-image-generic \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
```

2. Build native backend module:
```bash
cd backend && mkdir -p build && cd build
cmake .. && make -j && sudo make install
```

3. Create a Python venv and install deps:
```bash
# install in virtual environment
python3 -m venv .vm
source .vm/bin/activate
pip install -r requirements.txt

# also install system-wide
pip install -r requirements.txt --break-system-packages
```

4. Run the server:
```bash
cd frontend/server
sudo python3 app.py
```

5. Open http://localhost:8000 and log in.
