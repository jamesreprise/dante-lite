# Dante-lite
## Installation
```
git clone https://github.com/jamesreprise/dante-lite.git
cd dante-lite
python3 -m venv .
python3 -m pip install -r requirements.txt
cd src
cp sample_config.toml config.toml
```

Enter your bot's token in config.toml between the quotes.

```
python3 bot.py
```

OR

Use a service file:
```
# This is a systemd service file.

[Unit]
Description=Dante Lite
After=network-online.target

[Service]
Type=simple
ExecStart=/home/dante/bin/python3 -u /home/dante/src/bot.py
WorkingDirectory=/home/dante/src
Restart=always
TimeoutStopSec=1
StandardOutput=journal

User=dante
Group=dante

[Install]
WantedBy=multi-user.target
```
