# pycrawler
Repository for commands gathering tool - pycrawler

![image](https://user-images.githubusercontent.com/22170799/99851985-21aa6700-2b91-11eb-8851-dc278a4d5405.png)

For required libraries and their versions see **requirements.txt**.

This tool has been written and tested with Python 3.8 but should work with Python 3.6 and newer versions as well.
The tool is only supported on Linux since requires pyATS library to work (it might also work on WSL and macOS but hasn't been tested there).

## 1. To install required apps and Python libraries:
```
sudo apt-get install python3-dev -y
sudo apt-get install build-essential -y
```

## 2. It's always required to work inside Python virtual environment, hence install it:
```
sudo apt-get install python3-venv -y
```

## 3. Change to the directory where virtual environment to be placed and create it:
Use the command: **python3 -m venv {venv_name}**
For example:
```
python3 -m venv pycrawler
```

## 4. Activate created virtual environment (starting from this point, you should run pip and the tool from inside virtual environment):
```
source <path_to_venv>/bin/activate
```
### If you need to jump off the virtual environment, deactivate it:
```
source <path_to_venv>/bin/deactivate
```

## 5. Upgrade pip and pip setuptools
```
pip install --upgrade pip
pip install --upgrade pip setuptools
```

## 6. Install pyATS and Genie libraries
```
pip install pyats
pip install genie
```

### Or using requirements file:
```
pip install -r requirements.txt
```

## 7. Put testbed.yaml file to config directory (see testbed_example.yaml for the reference)

## 8. Decide how to store username and password for connection to devices
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

1. Activate virtual environment
```
source <path_to_venv>/bin/activate
```

2. Install the cryptography package:
```
pip install cryptography
```

3. Generate a cryptographic key:
```
pyats secret keygen
Newly generated key :
dSvoKX23jKQADn20INt3W3B5ogUQmh6Pq00czddHtgU=
```

4. Create configuration file for pyATS: **vim $VIRTUAL_ENV/pyats.conf** and add the following:
```
[secrets]
string.representer = pyats.utils.secret_strings.FernetSecretStringRepresenter
string.key = dSvoKX23jKQADn20INt3W3B5ogUQmh6Pq00czddHtgU=
```

5. Ensure the permissions are restricted on your pyATS configuration file to prevent other users from reading it:
```
chmod 600 $VIRTUAL_ENV/pyats.conf
```

6. Encode a password:
```
pyats secret encode
Password: cisco_pass
Encoded string :
gAAAAABdsgvwElU9_3RTZsRnd4b1l3Es2gV6Y_DUnUE8C9y3SdZGBc2v0B2m9sKVz80jyeYhlWKMDwtqfwlbg4sQ2Y0a843luOrZyyOuCgZ7bxE5X3Dk_NY=
```

7. Do a test decode of the encoded password:
```
pyats secret decode gAAAAABdsgvwElU9_3RTZsRnd4b1l3Es2gV6Y_DUnUE8C9y3SdZGBc2v0B2m9sKVz80jyeYhlWKMDwtqfwlbg4sQ2Y0a843luOrZyyOuCgZ7bxE5X3Dk_NY=
Decoded string :
cisco_pass
```

8. Add your encoded password to a testbed.yaml %ENC{} block. Now your password is secured.\n
The only way to decode the password from the testbed YAML file is to use the same pyATS configuration file (**$VIRTUAL_ENV/pyats.conf**) used to encode the password:
```
  credentials:
    default:
      username: "cisco"
      password: "ENC{gAAAAABdsgvwElU9_3RTZsRnd4b1l3Es2gV6Y_DUnUE8C9y3SdZGBc2v0B2m9sKVz80jyeYhlWKMDwtqfwlbg4sQ2Y0a843luOrZyyOuCgZ7bxE5X3Dk_NY=}"
    enable:
      password: "ENC{gAAAAABdsgvwElU9_3RTZsRnd4b1l3Es2gV6Y_DUnUE8C9y3SdZGBc2v0B2m9sKVz80jyeYhlWKMDwtqfwlbg4sQ2Y0a843luOrZyyOuCgZ7bxE5X3Dk_NY=}"
    line:
      password: "ENC{gAAAAABdsgvwElU9_3RTZsRnd4b1l3Es2gV6Y_DUnUE8C9y3SdZGBc2v0B2m9sKVz80jyeYhlWKMDwtqfwlbg4sQ2Y0a843luOrZyyOuCgZ7bxE5X3Dk_NY=}"
```

## More
Configuration files for pyATS:
https://pubhub.devnetcloud.com/media/pyats/docs/configuration/index.html#pyats-configuration

Complete procedure to generate pyATS Secret String:
https://pubhub.devnetcloud.com/media/pyats/docs/utilities/secret_strings.html#secret-strings
