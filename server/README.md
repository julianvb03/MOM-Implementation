# REST API for MOM Implementation

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

This is a REST API for the implementation of a MOM middleware for the Topics of Telematics course at EAFIT University. The API is designed to send, receive, suscribe and disconnect to messages from the MOM. The API is built using FastAPI and is designed to be easy to use and extend. 

## Project Structure

```bash
. \
├── app \
│   ├── adapters \
│   │   ├── __init__.py # Adapters initialization. \
│   │   ├── db.py # Database interface file. \
│   │   ├── factory.py # Database factory file. \
│   │   ├── user_repository.py # User repository interface file. \
│   │   └── user_service.py # User service interface file. \
│   ├── auth \
│   │   ├── __init__.py # Authentication initialization. \
│   │   └── auth.py # Authentication handling file. \
│   ├── config \
│   │   ├── __init__.py # Configuration initialization. \
│   │   ├── db.py # Database handling file. \
│   │   ├── env.py # Environment variables handling file. \
│   │   ├── logging.py # Logger handling file. \
│   │   └── limiter.py # Rate limiter handling file. \
│   ├── dtos \
│   │   │   ├── admin \
│   │   │   │   ├── __init__.py # Admin initialization. \
│   │   │   │   ├── mom_management_dto.py # MOM management DTO file. \
│   │   │   │   └── user_management_dto.py # User management DTO file. \
│   │   ├── __init__.py # Models initialization. \
│   │   ├── general_dtos.py # General DTO file. \
│   │   ├── mom_dto.py # MOM DTO file. \
│   │   └── user_dto.py # User DTO file. \
│   ├── exceptions \
│   │   ├── __init__.py # Exceptions initialization. \
│   │   └── database_exceptions.py # Database exceptions file. \
│   ├── models \
│   │   └── user.py # User model file. \
│   ├── MOM \    
│   ├── repositories \
│   │   ├── __init__.py # Repositories initialization. \
│   │   └── user_repository.py # User repository file. \
│   ├── services \
│   │   ├── __init__.py # Services initialization. \
│   │   └── user_service.py # User service file. \
│   ├── routes \  
│   │   ├── admin \
│   │   │   ├── mom_management \
│   │   │   │   ├── __init__.py # MOM management initialization. \
│   │   │   │   └── routes.py # MOM management routes file. \
│   │   │   ├── __init__.py # Admin initialization. \
│   │   │   └── routes.py # Admin routes file for user handling. \
│   │   ├── mom \
│   │   │   ├── __init__.py # MOM initialization. \
│   │   │   └── routes.py # MOM interaction routes file. \
│   │   ├── __init__.py # Routes initialization. \   
│   │   └── routes.py # Routes file. \      
│   ├── utils \
│   │   ├── __init__.py # Utils initialization. \
│   │   ├── db.py # Database initialization file. \
│   │   └── exceptions.py # Exception handling file. \
│   ├── tests # Tests folder. \
│   ├── __init__.py # API initialization. \
│   └── app.py # API routes and methods. \
├── .env.example # Environment variables example. \
├── README.md # Folder or Service README. \
├── Dockerfile # File to build the docker image. \
├── .dockerignore # Files to ignore when building the docker image. \
└── requirements.txt # Python dependencies. \
```

## Pre-requisites

- Python 3.8 or higher.
- Pip.
- Virtual Environment (Optional).
- Docker (Optional).

## Setup Instructions

1. **Environment Setup**: Make sure you have python 3.8 or higher installed. The python version used was the 3.12.4. 
2. **Directory Navigation**: navigate to the BACKEND directory `cd PATH/TO/PROJECT`.
3. **Virtual Environment Setup (Optional)**: setup a python venv if desired `python -m  venv .venv` and activate it `.venv\Scripts\activate` in Windows or `source .venv\bin\activate` in Linux or Mac.
4. **Dependencies Installation**: Execute `pip install -r requirements.txt` to install the needed dependencies. 
5. **Environment Variables**: Configure the environment variables as in the `.env.example` file.
    1. **.env**: Create a `.env` file in the root directory of the project.
    2. **Environment Variables**: Copy the content of the `.env.example` file to the `.env` file and modify the values as needed.
    3. **Execute**: Execute `source .env` in Linux or Mac, or `Get-Content .env | ForEach-Object { if ($_ -match '^\s*#|^\s*$') { return }; $line = ($_ -replace '#.*$', '').Trim(); if ($line -match '^\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*(.+)$') { $name = $Matches[1]; $value = $Matches[2].Trim(); if ($value -match '^"(.*)"$') { $value = $Matches[1] } elseif ($value -match "^'(.*)'$") { $value = $Matches[1] }; Set-Item -Path "Env:$name" -Value $value } }` in Windows to load the environment variables.
6. **Database Initialization**: Execute `docker compose -f ./docker-compose-dev.yml up -d` to initialize the database. This will create the database and the tables needed for the API.
7. **Execution**: Execute `uvicorn app.app:app --reload --port 8000` to initialize the API in the 8000 port. 
8. **Tests Execution**: Execute `pytest` to run the tests. The tests are located in the `tests` folder.
9. **Linter Execution**: Execute `pylint --rcfile=.pylintrc app/` to run the linter. The linter is configured to use the `.pylintrc` file in the root directory.

## Docker Image

### Image Usage

We didn't upload the docker image to any registry, so you need to build it locally. The developer mode run only has the databases necessary to execute the API and the API itself. The production mode has the API, the database of MOM and the gRPC image execution (For production you need the other 2 mongo IPs, the backup database and the users database).

- To run in developer mode you can run the following command in the root directory of the project:

```bash
docker compose -f ./docker-compose-dev.yml up -d --build
```

To stop the docker containers, you can run the following command:

```bash
docker compose -f ./docker-compose-dev.yml down
```

- To run in production mode you can run the following command in the root directory of the project:

```bash
docker compose -f ./docker-compose.yml up -d --build
```
To stop the docker containers, you can run the following command:

```bash
docker compose -f ./docker-compose.yml down
```

## Endpoints

The API provides several endpoint to apply or use different numerical methods for different purposes. The available endpoints are at the [Endpoint Documentation File](Endpoints.md).

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