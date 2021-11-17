# Dante
## Installation
All in src/ :
```
pip install -r requirements.txt
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
ExecStart=/usr/bin/python3 -u /home/dante-lite/src/bot.py
WorkingDirectory=/home/dante-lite/src
Restart=always
TimeoutStopSec=1
StandardOutput=journal

User=dante
Group=dante

[Install]
WantedBy=multi-user.target
```
