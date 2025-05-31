# Steps to host the Discord Bot:

1) Get a Virtual Private Server (VPS) or self host using your own computer (I used DigitalOcean Ubuntu 24)
2) Clone the git repository 

`git clone https://github.com/Suvanth-Erranki/Coding-Club-Trainer.git`

3) Add the `.env` file in the root directory of the repo, with 

`DISCORD_TOKEN=token`

4) Install python package manager pip

`sudo apt update && sudo apt install python3-pip`

5) Install the required packages

`python3 -m pip install -U discord.py --break-system-packages`
`python3 -m pip install -U python-dotenv --break-system-packages`

6) Create the systemd service file

`vi /etc/systemd/system/potwbot.service`

Enter:

```
[Unit]
Description=Discord POTW Bot
After=network.target

[Service]
# User=basic
WorkingDirectory=/root/Coding-Club-Trainer/src
ExecStart=/usr/bin/python3 run.py
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

7) Run the systemd service and check its status

```
sudo systemctl daemon-reload
sudo systemctl enable potwbot
sudo systemctl start potwbot
sudo systemctl status potwbot
```

8) View logs

`journalctl -u potwbot -f`
