# pycrawler
Repository for commands gathering tool - pycrawler

![image](https://user-images.githubusercontent.com/22170799/99851985-21aa6700-2b91-11eb-8851-dc278a4d5405.png)

For required libraries and their versions see **requirements.txt**.

This tool has been written and tested with Python 3.8 but should work with Python 3.6 and newer versions as well.
The tool is only supported on Linux since requires pyATS library to work (it might also work on WSL and macOS but hasn't been tested there).

## To install required apps and Python libraries:
```
sudo apt-get install python3-venv -y
sudo apt-get install python3-dev -y
sudo apt-get install build-essential -y
```

```
pip install --upgrade pip
pip install --upgrade pip setuptools
```

```
pip install pyats
pip install tabulate
pip install genie
```

### Or using requirements file:
```
pip install -r requirements.txt
```

## Specify username and password (as Linux env variable) to access your devices
```
export PYATS_USERNAME=admin
export PYATS_PASSWORD=cisco.123
export PYATS_AUTH_PASS=cisco.123
```

## Put testbed.yaml file to config directory (see testbed_example.yaml for reference)
