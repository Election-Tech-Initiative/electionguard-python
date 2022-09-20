# Setup Surface Go 3 Tablet

This documentation is a reference on how to setup a brand new computer (in this case a Surface Go 3) to use the Python repository to run the Admin and Guardian GUIs for an election. Some steps, such as "Turn Off S Mode" might not apply to the computer you are setting up. All usernames and passwords are set to xxx in this document and should be set to valid values for your own purpose.

## Setup Windows
* When prompted for email address use
    * xxxx@xxxx.com
    * xxxx
* skip protecting account
* skip hello setup
* pin xxxx
* default privacy
* skip customization
* decline office 365
* installs Win11 (30 min or so)

## Turn Off S Mode
* settings -> system -> activation
* opens windows store
* hit Get button and wait for it to complete

## Windows Updates
* Do all the updates (a lot of updates)
* Change to best performance mode
    * Settings -> System -> Power and Battery
    * Power Mode -> Best Performance

## Install Hyper-V and Linux (admin only)
* Go to Settings
* Search for features
* Go to optional features
* More Windows Features
* Install WSL, Virtual Machine Platform and Windows Hypervisor Platform settings
* Restart windows
* Go to windows store and install ubuntu
* When running it the first time it will give a link to install a new kernel for WSL2
* Run ubuntu and setup a user
    * Username: xxxx
    * Password: xxxx

## Docker Installation (admin only)
* Get docker desktop and install.
* In the settings (gear icon) make the following changes:
    * Make sure that "Start Docker Desktop when you log in" is on
    * Make sure that "Use the WSL 2 based engine" is on

## Developer Tools
* Command prompt -> python3 (install from windows store)
* Install chrome (does not need to be set to current browser)
* Install VS Code
* Git
    * https://git-scm.com/download/win
* Install chocolatey using powershell command from https://chocolatey.org/install
* Install make
    * choco install make	
* Install poetry (powershell) https://python-poetry.org/docs
    * Add to path (See "Set Environment Variables" below on steps to get to the path)

## Download Python Source Code
* Open a Command prompt and use the following commands
    * mkdir code
    * cd code
    * git clone https://github.com/microsoft/electionguard-python


## Terminal Settings
* Open up Terminal
    * Go to settings in Terminal
    * Default Profile => Command Prompt
    * Profiles (left) -> Defaults 
        * Run this profile as Admin -> on
        * Starting Starting directory to be directory where source code is downloaded
    * Hit "Save" button at the bottom of the window

## User Interface Changes
* Change touch keyboard to traditional instead of default
* Go into resize (using the gear icon) and set the zoom to 200 (max value)

## Set Environment Variables
* Go to Settings
* Search for environment
* Select "Edit the system environment variables"
* Select the button "Environment Variables"
* Select "New…"
* Create the following settings
    * EG_DB_PASSWORD = xxxx
    * EG_DB_HOST = 10.10.0.100
    * EG_IS_ADMIN = true for an admin and false if guardian
    * admin only - EG_DB_DIR = ./database 

## Set Python Code
* Open Terminal and run the following commands
    * make environment
        * There will be an error at the end.  This is normal
    * poetry run eg 
        * should show the help for the eg command

