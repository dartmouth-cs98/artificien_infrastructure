FROM ubuntu:20.04
MAINTAINER Artificien artificien1@gmail.com

# Install Node
ENV NODE_VERSION=14.2.0
RUN apt install -y curl
RUN curl -o- https://raw.githubusercontent.com/creationix/nvm/v0.34.0/install.sh | bash
ENV NVM_DIR=/root/.nvm
RUN . "$NVM_DIR/nvm.sh" && nvm install ${NODE_VERSION}
RUN . "$NVM_DIR/nvm.sh" && nvm use v${NODE_VERSION}
RUN . "$NVM_DIR/nvm.sh" && nvm alias default v${NODE_VERSION}
ENV PATH="/root/.nvm/versions/node/v${NODE_VERSION}/bin/:${PATH}"

# Install AWS CDK
RUN npm install -g aws-cdk

# Install python packages
RUN apt update -y && apt install -y python3-pip python3-dev
COPY . /opt/app
WORKDIR /opt/app
RUN pip install -r requirements.txt
