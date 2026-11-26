# Lightning Webstore
A Flask web application that accepts Lightning payments via LND.

## Install dependencies
`pip install -r requirements.txt` or `pip3 install -r requirements.txt`

## Start Application
Start app with command `python app.py`

## View in Browser
Open `http://127.0.0.1:5000` on your browser to view website

## Windows (WSL) with Polar
Polar runs on Windows, so the app looks for its data under
`/mnt/c/Users/<name>/.polar` and converts the Windows paths it finds there.
Check the connection first with `python lnd_client.py`; it should print
`LND client working!`.

If it says `Connection refused`, WSL cannot reach Docker's port on
`127.0.0.1`. Either turn on Docker Desktop > Settings > Resources >
WSL integration for your distro, or point the app at the Windows host.
Set both variables, since one on its own is ignored:

```
export LND_DIR=/mnt/c/Users/<name>/.polar/networks/<id>/volumes/lnd/bob
export REST_HOST=https://$(ip route show default | awk '{print $3}'):<rest port>
```

The network id and REST port are shown on bob's page in Polar.
