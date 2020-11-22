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
pip install genie
```

### Or using requirements file:
```
pip install -r requirements.txt
```

## Put testbed.yaml file to config directory (see testbed_example.yaml for reference)

## Username and password for connection to devices
### If you are not going to run the tool via crontab - you can use Linux environment variables to store username and password:
Run the following commands from Bash:
```
export PYATS_USERNAME=admin
export PYATS_PASSWORD=cisco.123
export PYATS_AUTH_PASS=cisco.123
```
These environment variables to be used in the following configuration in config/testbed.yaml:
```
  credentials:
    default:
      username: "PYATS_USERNAME"
      password: "PYATS_PASSWORD"
    enable:
      password: "%ENV{PYATS_AUTH_PASS}"
    line:
      password: "%ENV{PYATS_AUTH_PASS}"
```

### If this tool is going to be run with crontab - it's recommended to store credentials for access devices in testbed.yaml file
While you could use the following configuration to store the username and password in testbed.yaml, it's not secure because if testbed.yaml is stolen - credentials would become compromised. Below is an example how to store credentials in testbed.yaml (cisco\cisco_pass) - **NOT RECOMMENDED!**:
```
  credentials:
    default:
      username: "cisco"
      password: "cisco_pass"
    enable:
      password: "cisco_pass"
    line:
      password: "cisco_pass"
```

The recommended way of storing credentials in **testbed.yaml** is in encrypted form:
```
  credentials:
    default:
      username: "cisco"
      password: "ENC{secret_pass}"
    enable:
      password: "ENC{secret_pass}"
    line:
      password: "ENC{secret_pass}"
```
In the example above secret_pass - is an encrypted string with cisco_pass. 
To generate this string follow the procedure:
