import os

path = "."


def setup_folders():
    os.makedirs(path + "/frontend")
    os.makedirs(path + "/frontend/components")
    os.makedirs(path + "/frontend/js")
    os.makedirs(path + "/frontend/css")
    os.makedirs(path + "/backend")
    os.makedirs(path + "/extras")

    os.system("git init")
    os.system(f"cd {path}/backend && uv init && uv sync")
    os.system(
        f"cd {path}/backend && uv add pocketbase && uv add fastapi && uv add uvicorn"
    )


def setup_backend():
    open(path + "/backend/main.py", "w").write("""from fastapi import FastAPI
import pocketbase
pb = pocketbase.PocketBase("http://pocketbase:8080")
app = FastAPI()
@app.get("/")
def root():
    return "Hello World"

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5000)
    """)


def setup_frontend():
    frontendboilerplate = """
    <!DOCTYPE html>
    <html lang="en">
      <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta http-equiv="X-UA-Compatible" content="ie=edge">
        <title>HTML 5 Boilerplate</title>
        <script src="https://cdn.jsdelivr.net/npm/htmx.org@2.0.8/dist/htmx.js" integrity="sha384-ezjq8118wdwdRMj+nX4bevEi+cDLTbhLAeFF688VK8tPDGeLUe0WoY2MZtSla72F" crossorigin="anonymous"></script>
        <script src="https://cdn.jsdelivr.net/npm/@tailwindcss/browser@4"></script>
        <link href="https://cdn.jsdelivr.net/npm/daisyui@5" rel="stylesheet" type="text/css" />
        <!-- <link rel="stylesheet" href="style.css"> -->
      </head>
      <body>
        <!-- <script src="index.js"></script> -->
      </body>
    </html>
    """
    open(path + "/frontend/index.php", "w").write(frontendboilerplate)


def dockerconfig():
    config = """services:
      php_app:
        image: php:8.3-fpm
        volumes:
          - ./frontend:/var/www/html
      nginx_server:
        image: nginx:alpine
        ports:
          - "80:80" # change the first port number to match your needs
        volumes:
          - ./frontend:/var/www/html
          - ./nginx.conf:/etc/nginx/conf.d/default.conf:ro
      backend:
        build: ./backend
        command: uv run main.py
        restart: always
        ports:
          - "5000:5000"
      pocketbase:
        image: ghcr.io/muchobien/pocketbase:latest
        ports:
          - "{preferences.pocketbaseport}:8080"
        volumes:
          - ./pb_data:/pb_data
        command:
          - serve
          - --http=0.0.0.0:8080
          - --dir=/pb_data
        restart: unless-stopped"""
    composefile = open(path + "/docker-compose.yml", "w")
    composefile.write(config)
    composefile.close()
    serverconfig = """FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1
ENV UV_NO_DEV=1

# Optimized layer caching
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

COPY . .
RUN uv sync --frozen --no-dev

CMD ["uv", "run", "main.py"]"""
    dockerfile = open(path + "/backend/Dockerfile", "w")
    dockerfile.write(serverconfig)
    dockerfile.close()

    nginxconfig = """server {
        listen 80;
        root /var/www/html;

        # Use Docker's internal DNS resolver
        resolver 127.0.0.11 valid=30s;

        location / {
            index index.php;
            try_files $uri $uri/ /index.php?$query_string;
        }

        location ~ .php$ {
            # Using a variable prevents Nginx from crashing if php_app is down
            set $upstream php_app:9000;
            fastcgi_pass $upstream;
            include fastcgi_params;
            fastcgi_param SCRIPT_FILENAME $document_root$fastcgi_script_name;
        }
    }"""

    nginxfile = open(path + "/nginx.conf", "w")
    nginxfile.write(nginxconfig)
    nginxfile.close()


def main():
    print("==============================================\nWelcome to JayStack!")
    print("Setting up folders")
    setup_folders()
    print("Setting up Docker configuration")
    dockerconfig()
    setup_frontend()
    setup_backend()
    print("""Your project is ready!\n
    start it with: sudo docker compose up -d\n
    If you have a frontend you can acces it at http://localhost:80
    If you have a backend you can acces it at http://localhost:5000 publicly and http://backend:5000 privately
    If you have a database you can acces it at http://localhost:8080/_ (enter sudo docker logs pocketbase to get the password)
    and http://pocketbase:8080 privately
    """)


main()
