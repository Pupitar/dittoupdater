# dittoupdater

## Installation
1. Install `python3.8 python3.8-venv git`
2. Install required system packages for https://pypi.org/project/mysqlclient
3. Clone repository `git clone https://github.com/Pupitar/dittoupdater.git /home/$USER/repos/dittoupdater`
4. Create virtual env `python3 -m venv /home/$USER/pyenv/dittoupdater`
5. Install required python packages `/home/$USER/pyenv/dittoupdater/bin/pip install -r /home/$USER/repos/dittoupdater/requirements.txt`
6. Copy example config `cp /home/$USER/repos/dittoupdater/config.example.yml /home/$USER/repos/dittoupdater/config.yml`
7. Fill `config.yml`
8. Start `/home/$USER/pyenv/dittoupdater/bin/python /home/$USER/repos/dittoupdater/main.py`
