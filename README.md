# PA2b Container Build (and Run) Instructions

## Step 1. Clone the git repo by using either of the commands below:

***Windows: You need to run this from an Ubuntu shell in WSL, not from Powershell***

```bash
# Clone with submodules
git clone --recurse-submodules https://github.com/ucsd-cse123-fa24/project2b-container.git

# Or, clone and update submodules after clone
git clone https://github.com/ucsd-cse123-fa24/project2b-container.git
cd project2b-container/
git submodule update --init --recursive
```

## Step 2: Build and run the Docker container

### Linux and macOS M1/M2

```bash
# Create a volume for your docker container so your project directory will live when your container dies
docker volume create cse123pa2b_data
# Build the docker container for the project
docker build -t cse123pa2b --target linux .
# Run the docker container for the project. Run this each time you work on the project.
# You should be able to attach to the running container in VSCode (or using the exec comand below) after this is executed.
docker run -d --rm --privileged -it --name pa2b -v /lib/modules:/lib/modules -v cse123pa2b_data:/project-base -t cse123pa2b
```

### Windows 

#### You need to use both Ubuntu shell and Powershell

This project requres WSL with the Ubuntu distribution.  You can check if you already have that installed by typing;
```bash
wsl -l
```

You should see 
```bash
Windows Subsystem for Linux Distributions:
Ubuntu (Default)
```

If you see something else, you will need to (re)install WSL with the Ubuntu distribution using the following commands:
```bash
wsl --install
wsl --set-default Ubuntu
```

Ubuntu Shell:

If you do not already have an Ubuntu shell running, you can start one with:
```bash
wsl
```

#### For Ubuntu Shell user, make sure inside the Docker Desktop -> Settings -> Resource -> WSL Integration, your "ubuntu" button is on.
```bash
# Create a volume for your docker container so your project directory will live when your container dies
docker volume create cse123pa2b_data
# Build the docker container for the project (this will take ~30mins to build the new kernel)
docker build -t cse123pa2b --target windows .
# Run the docker container for the project. Run this each time you work on the project.
# You should be able to attach to the running container in VSCode (or using the exec comand below) after this is executed 
docker run -d --rm --privileged -it --name pa2b -v cse123pa2b_data:/project-base -t cse123pa2b
# Copy the new kernel out of the docker image into WSL
docker cp pa2b:/wsl-kernel/vmlinux /tmp/vmlinux
```

Powershell:
```bash
# Switch to your windows home directory
cd ~
# Copy the kernel image out of WSL into your Windows home directory
wsl cp /tmp/vmlinux cse123pa2-kernel
# Launch notepad to edit your wsl config file
notepad .wslconfig
```

In your .wslconfig write the following text save it in notepad (replace YourUserName with your actual windows user name):
```
[wsl2]
kernel=C:\\Users\\YourUserName\\cse123pa2-kernel
```

Powershell:
```
# Shut down wsl (Docker will crash and force a restart of wsl if you have it running)
wsl --shutdown
```

Ubuntu Shell:
```bash
# Run the docker container again
docker run -d --rm --privileged -it --name pa2b -v cse123pa2b_data:/project-base -t cse123pa2b
```

## Step 3: Clone your project repo inside the container

We recommend using VSCode to do this (so that it uses your standard Git credentials), but you can also do it from the command line inside the docker container:

```bash
# To open a shell inside the running container, in each terminal run the following (or attach to the running container using VSCode):
docker exec -it pa2b bash
# Inside the container you may need to switch to the /project-base folder
root@docker$ cd /project-base

# You can now clone the github repo into your project from inside the Docker container's bash shell and run the rest of the commands!
```
