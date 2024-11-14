FROM ubuntu:18.04 AS linux
RUN apt update && \
        apt install -y openvswitch-switch mininet iproute2 arping netcat \
                curl inetutils-ping inetutils-traceroute \
                build-essential gdb git nano screen python python-pip python-twisted sudo && \
        pip install typing
RUN apt install -y python3 python3-pip && \
        pip3 install -U pip && \
        pip3 install -U cryptography && \
        pip3 install mininet pexpect scapy
RUN pip2 install mininet ltprotocol
VOLUME /project-base
WORKDIR /project-base
COPY project-base /project-base
CMD /project-base/boot.sh && bash

FROM --platform=linux/amd64 ubuntu:18.04 AS wsl-build
RUN apt update && \
        apt install -y build-essential flex bison libssl-dev libelf-dev git dwarves bc python3
RUN git clone --depth 1 https://github.com/microsoft/WSL2-Linux-Kernel.git --branch linux-msft-wsl-5.15.y --single-branch /wsl-kernel
COPY windows-configs/.config /wsl-kernel/.config
RUN yes "" | make -C /wsl-kernel -j $(expr $(nproc) - 1) modules

FROM linux AS windows
COPY --from=wsl-build /wsl-kernel /wsl-kernel
VOLUME /project-base
WORKDIR /project-base
RUN make -C /wsl-kernel modules_install
CMD /project-base/boot.sh && bash
