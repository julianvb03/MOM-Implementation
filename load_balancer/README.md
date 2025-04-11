# Rest API Load Balancer

## Content Table
- [Developers](#developers)
- [Introduction](#introduction)
- [Project Structure](#project-structure)
- [Pre-requisites](#pre-requisites)
- [Setup Instructions](#setup-instructions)
- [Docker Image](#docker-image)
  - [Image Build](#image-build)
  - [Image Usage](#image-usage)
- [Endpoints](#endpoints)
- [Contribution](#contribution)
- [Contact](#contact)

## Developers

- Juan Felipe Restrepo Buitrago
- Kevin Quiroz González 
- Julian Estiven Valencia Bolaños
- Julian Agudelo Cifuentes

## Introduction

This is a docker compose file to run a load balancer for the MOM API. The load balancer is designed to distribute the traffic between the different instances of the API. The load balancer is built using Nginx and is designed to be easy to use and extend.

## Project Structure

```bash
. \
├── docker-compose.yml # Docker compose file. \
└── nginx.conf # Nginx configuration file. \
```

## Pre-requisites

- Docker.

## Setup Instructions

1. **Environment Setup**: Make sure you have docker installed and your API instances running.
2. **Directory Navigation**: navigate to the load_balancer directory `cd PATH/TO/PROJECT/load_balancer`.
3. **Nginx Config**: You must edit the `nginx.conf` file to add the IPs of the API instances. The IPs must be added in the `upstream` section of the file. The IPs must be separated by a space. If using AWS, you can use the private IPs of the instances.
    1. Example:
    ```nginx
      server 172.31.1.10:8080 max_fails=5 fail_timeout=60s; # API Instance 1 private IP which must be modified
      server 172.31.1.11:8080 max_fails=5 fail_timeout=60s; # API Instance 2 private IP which must be modified
      server 172.31.1.12:8080 max_fails=5 fail_timeout=60s; # API Instance 3 private IP which must be modified
    ```
4. **Docker Compose**: Execute `docker compose up -d` or `docker-compose up -d` to run the load balancer. This will create a docker container with the load balancer running.
5. **Stop the Load Balancer**: Execute `docker compose down` or `docker-compose down` to stop the load balancer. This will stop the docker container with the load balancer running.

## Contribution

For contributing to this project, follow the instructions below:

1. **Fork the repository**: Make a fork of the repository and clone your fork on your local machine.
2. **Create a new branch**: Create a new branch with a name which gives an idea of the addition or correction to the project. 
3. **Make your changes**: Make your code changes and test them. 
4. **Make a pull request**: Finally, make a pull request to the original repository. 

## Contact

For any questions or issues, feel free to reach out to:
- Juan Felipe Restrepo Buitrago: [jfrestrepb@eafit.edu.co](jfrestrepb@eafit.edu.co)
- Kevin Quiroz González: [kquirozg@eafit.edu.co](mailto:kquirozg@eafit.edu.co)
- Julian Estiven Valencia Bolaños: [jevalencib@eafit.edu.co](mailto:jevalencib@eafit.edu.co)
- Julian Agudelo Cifuentes: [jagudeloc@eafit.edu.co](mailto:jagudeloc@eafit.edu.co)