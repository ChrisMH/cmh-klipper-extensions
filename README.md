# cmh-klipper

git clone https://github.com/ChrisMH/cmh-klipper.git

or

git clone git@github.com:ChrisMH/cmh-klipper.git

# Install
./cmh-klipper/install.sh

# Uninstall
./cmh-klipper/install.sh -u

# Update Manager
[update_manager cmh-klipper]
type: git_repo
path: ~/cmh-klipper
origin: https://github.com/ChrisMH/cmh-klipper.git
install_script: install.sh
managed_services: klipper
primary_branch: main

