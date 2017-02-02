# About
Simple systemd service to backup scalets (VM) in https://vscale.io  

# Installation
* Create API token on https://vscale.io/panel/settings/tokens/
* Put token to `/etc/vscale.token`:
```bash
VSCALE_TOKEN=XXXXXXXXXXX
```

* Set secure permissions on our token file: `chmod 600 /etc/vscale.token`
* Put `scalets-backup.service` and `scalets-backup.timer` files to `/etc/systemd/system` directory.
* Run `systemctl daemon-reload`
* Run `systemctl enable scalets-backup.timer`

# How to use
Use tag `to_backup` to mark required scalets (VM) in https://vscale.io/panel/.

## Perform backup
Run following command to perform backup or wait scheduled job
```bash
systemctl start scalets-backup.service
```

## Change schedule
Edit `/etc/systemd/system/scalets-backup.timer` to change schedule. Read 
https://www.freedesktop.org/software/systemd/man/systemd.time.html to get help with `OnCalendar` syntax.

## Read logs
Use common approach to see service log:
```bash
journalctl -xeu scalets-backup.service
```