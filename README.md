# cmh-klipper-extensions

git clone https://github.com/ChrisMH/cmh-klipper-extensions.git

or

git clone git@github.com:ChrisMH/cmh-klipper-extensions.git

# Install
./cmh-klipper-extensions/install-extensions.sh
./cmh-klipper-extensions/install-kinematics.sh

# Uninstall
./cmh-klipper-extensions/install-extensions.sh -u
./cmh-klipper-extensions/install-kinematics.sh -u

# Update Manager

[update_manager cmh-klipper-extensions]
type: git_repo
path: ~/cmh-klipper-extensions
origin: https://github.com/ChrisMH/cmh-klipper-extensions.git
install_script: install-extensions.sh
managed_services: klipper

