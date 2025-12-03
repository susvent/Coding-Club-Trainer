# Problem of the Day Trainer - WWP High School South Coding Club

A fully automated **Problem of the Day (POTD)** system built for High School South Coding Club community.  
This Discord bot posts new Codeforces problems every other morning, tracks member submissions in real time, and maintains a dynamic leaderboard, requiring no manual intervention or updates from officers.

<img width="1728" height="998" alt="image" src="https://github.com/user-attachments/assets/68d2d5e2-a8d5-4c4c-ac5f-de569d6ec037" />

## Features

### Daily / Bi-Daily Problem Drops
- Automatically posts **three Codeforces problems** (Easy / Medium / Hard) every other day at 8 AM ET.
- Problems are randomly selected within rating ranges and guaranteed to be **unique**, avoiding repeats.
- Officers can also manually create POTDs with `/add`.

<img width="1396" height="982" alt="image" src="https://github.com/user-attachments/assets/65f90e33-76e5-4482-9ca3-5607e0323941" />

### Real-Time Leaderboard
- Tracks user solves across all POTDs.
- Awards **points for each solved problem**, updating every 5 minutes.
- Distinguishes between regular members and observers.
- Includes a clean `/lb` leaderboard view and optional top-N preview for announcements.

<img width="512" height="489" alt="image" src="https://github.com/user-attachments/assets/b65164eb-3731-40e6-9da4-2037364236ac" />

### Automatic Solve Detection
- Detects Codeforces submissions in background intervals.
- Posts celebratory messages like:
  > “✅ @user completed POTD #12 — Medium in 4m 32s!”

<img width="613" height="525" alt="image" src="https://github.com/user-attachments/assets/8902fe37-3f67-4d68-845f-e4e05b4a6bb0" />

### Codeforces Verification
- `/verify <handle>` asks users to submit a **compile error** to a random CF problem.
- Once verified, their CF profile is linked permanently for score tracking.

<img width="604" height="253" alt="image" src="https://github.com/user-attachments/assets/bb4c21c8-5445-4f23-ae7e-3511d4506577" />

### Historical Problem Lookup
- `/potd` shows today’s problems.
- `/potd <num>` lets users browse any previous day.

<img width="375" height="402" alt="image" src="https://github.com/user-attachments/assets/9a50b951-b0d4-4ae4-9fb6-d0131c867c10" />

### Personal Stats
- `/stats` shows solved status for every day’s problems.
- Tracks Easy/Medium/Hard completion separately.

<img width="411" height="723" alt="image" src="https://github.com/user-attachments/assets/bd495055-f0af-4db5-85f6-9b7a3915b923" />

### Officer Tools
- Pause/resume all POTD operations using `/off` and `/on`.
- Add custom problem sets via `/add`.

## Data Storage
All state is stored in JSON files:
- `users.json` → verified users, scores, solve history  
- `problems.json` → all POTD entries  
- `old.json` → previously used problem URLs  
- `cache.json` → Codeforces API cache  

## Tech Stack
- Python 3  
- `discord.py` + Application Commands  
- Codeforces API wrapper (`cf.py`)  
- Persistent JSON storage  

## Purpose
This bot was designed to make competitive programming more fun, consistent, and community-driven.
It removes all administrative overhead so club officers can prioritze teaching, creating useful resources, and helping members grow.

<img width="1728" height="999" alt="image" src="https://github.com/user-attachments/assets/1013f131-a5ee-4676-b035-792c0d6fce1d" />
<img width="629" height="475" alt="image" src="https://github.com/user-attachments/assets/88d98312-da24-4bc8-beca-2232dc2436ff" />

---

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
