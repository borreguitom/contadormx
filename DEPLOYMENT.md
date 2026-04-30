# ContadorMX — Manual de Despliegue en Producción
## AWS EC2 / Proxmox VE (Ubuntu 22.04 LTS)

---

## Índice

1. [Requisitos de hardware](#1-requisitos-de-hardware)
2. [Preparar el servidor](#2-preparar-el-servidor)
3. [Instalar dependencias del sistema](#3-instalar-dependencias-del-sistema)
4. [Clonar el proyecto](#4-clonar-el-proyecto)
5. [Configurar variables de entorno](#5-configurar-variables-de-entorno)
6. [Levantar servicios con Docker (PostgreSQL, Redis, Qdrant)](#6-levantar-servicios-con-docker)
7. [Backend — FastAPI](#7-backend--fastapi)
8. [Frontend — Next.js](#8-frontend--nextjs)
9. [Celery Worker + Beat Scheduler](#9-celery-worker--beat-scheduler)
10. [Nginx como reverse proxy](#10-nginx-como-reverse-proxy)
11. [SSL con Let's Encrypt (HTTPS)](#11-ssl-con-lets-encrypt)
12. [Servicios systemd (auto-arranque)](#12-servicios-systemd)
13. [Cargar base de leyes fiscales (Qdrant)](#13-cargar-base-de-leyes-fiscales)
14. [Crear usuario administrador](#14-crear-usuario-administrador)
15. [Verificación final](#15-verificación-final)
16. [Comandos de mantenimiento](#16-comandos-de-mantenimiento)
17. [Backup automático](#17-backup-automático)
18. [Diferencias AWS vs Proxmox](#18-diferencias-aws-vs-proxmox)

---

## 1. Requisitos de Hardware

### Mínimo recomendado (hasta ~50 usuarios simultáneos)
| Recurso | Mínimo | Recomendado |
|---------|--------|-------------|
| CPU | 2 vCPU | 4 vCPU |
| RAM | 4 GB | 8 GB |
| Disco | 40 GB SSD | 80 GB SSD |
| OS | Ubuntu 22.04 LTS | Ubuntu 22.04 LTS |

### En AWS EC2
- Tipo de instancia recomendada: **t3.medium** (2 vCPU, 4 GB) o **t3.large** (2 vCPU, 8 GB)
- Volumen EBS: 60 GB gp3

### En Proxmox VE
- VM con 4 vCPU, 8 GB RAM, 80 GB disco (thin provisioning)
- Red: bridge en la misma LAN o con IP pública por NAT

---

## 2. Preparar el Servidor

### 2.1 Primer acceso y actualización

```bash
# Conectarse al servidor (AWS usa llave .pem, Proxmox puede ser directo)
ssh ubuntu@TU_IP_DEL_SERVIDOR

# Actualizar el sistema
sudo apt update && sudo apt upgrade -y

# Instalar utilidades básicas
sudo apt install -y curl wget git unzip htop nano ufw fail2ban
```

### 2.2 Configurar firewall (UFW)

```bash
# Reglas básicas
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Permitir SSH
sudo ufw allow 22/tcp

# Permitir HTTP y HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Activar
sudo ufw enable

# Verificar
sudo ufw status
```

### 2.3 Crear usuario de aplicación (no correr como root)

```bash
sudo useradd -m -s /bin/bash contadormx
sudo usermod -aG sudo contadormx
sudo usermod -aG docker contadormx  # se agrega después de instalar Docker

# Cambiar a ese usuario para el resto de la instalación
sudo su - contadormx
```

---

## 3. Instalar Dependencias del Sistema

### 3.1 Docker y Docker Compose

```bash
# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
rm get-docker.sh

# Agregar usuario al grupo docker (ya fue hecho arriba)
sudo usermod -aG docker $USER

# Activar Docker al inicio
sudo systemctl enable docker
sudo systemctl start docker

# Verificar
docker --version
docker compose version
```

> Cierra la sesión SSH y vuelve a conectarte para que el grupo `docker` tome efecto.

### 3.2 Python 3.11

```bash
sudo apt install -y python3.11 python3.11-venv python3.11-dev python3-pip

# Verificar
python3.11 --version
```

### 3.3 Node.js 20 LTS

```bash
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs

# Verificar
node --version   # debe ser v20.x.x
npm --version
```

### 3.4 Dependencias del sistema para WeasyPrint y PyMuPDF

```bash
sudo apt install -y \
  libcairo2 \
  libpango-1.0-0 \
  libpangocairo-1.0-0 \
  libgdk-pixbuf2.0-0 \
  libffi-dev \
  shared-mime-info \
  fonts-liberation \
  libmupdf-dev \
  mupdf-tools \
  pkg-config \
  build-essential
```

### 3.5 Nginx

```bash
sudo apt install -y nginx
sudo systemctl enable nginx
```

---

## 4. Clonar el Proyecto

```bash
# Ir al home del usuario de la app
cd /home/contadormx

# Clonar repositorio (reemplaza con tu URL real)
git clone https://github.com/TU_USUARIO/contadormx.git

# O si usas SSH:
# git clone git@github.com:TU_USUARIO/contadormx.git

cd contadormx

# Verificar estructura
ls -la
# Debes ver: backend/  frontend/  docker-compose.yml  scripts/  ...
```

---

## 5. Configurar Variables de Entorno

### 5.1 Backend (.env)

```bash
cd /home/contadormx/contadormx/backend

# Copiar plantilla de producción
cp .env.production.example .env

# Editar con tus valores reales
nano .env
```

Contenido del archivo `.env` — llena cada valor:

```env
# ── Base de datos ─────────────────────────────────────────────────────────────
# Apunta a localhost porque PostgreSQL corre en Docker en el mismo servidor
DATABASE_URL=postgresql+asyncpg://contadormx:TU_PASSWORD_POSTGRES@localhost:5432/contadormx

# ── Redis ─────────────────────────────────────────────────────────────────────
REDIS_URL=redis://localhost:6379/0

# ── Qdrant (vector DB para búsqueda de leyes) ─────────────────────────────────
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=contadormx-laws

# ── Inteligencia Artificial ───────────────────────────────────────────────────
ANTHROPIC_API_KEY=sk-ant-api03-XXXXXXX
VOYAGE_API_KEY=pa-XXXXXXX
EMBEDDING_PROVIDER=voyage

# ── Autenticación JWT ─────────────────────────────────────────────────────────
# IMPORTANTE: genera una clave segura con: openssl rand -hex 32
JWT_SECRET=REEMPLAZA_CON_RESULTADO_DE_openssl_rand_-hex_32
JWT_EXPIRE_MINUTES=10080

# ── Email (Resend) ────────────────────────────────────────────────────────────
RESEND_API_KEY=re_XXXXXXX
FROM_EMAIL=noreply@tudominio.com

# ── Stripe (pagos) ────────────────────────────────────────────────────────────
STRIPE_SECRET_KEY=sk_live_XXXXXXX
STRIPE_WEBHOOK_SECRET=whsec_XXXXXXX
STRIPE_PRICE_PRO=price_XXXXXXX
STRIPE_PRICE_AGENCIA=price_XXXXXXX

# ── URLs ──────────────────────────────────────────────────────────────────────
FRONTEND_URL=https://tudominio.com
CORS_ORIGINS=["https://tudominio.com","https://www.tudominio.com"]

# ── Ambiente ──────────────────────────────────────────────────────────────────
APP_ENV=production

# ── Sentry (monitoreo de errores, opcional) ───────────────────────────────────
# SENTRY_DSN=https://XXXXXXX@sentry.io/XXXXXXX
```

Genera el JWT_SECRET seguro:
```bash
openssl rand -hex 32
# Copia el resultado y pégalo en JWT_SECRET
```

### 5.2 Frontend (.env.local)

```bash
cd /home/contadormx/contadormx/frontend

# Crear el archivo
cat > .env.local << 'EOF'
# En producción, el frontend y backend están en el mismo dominio via Nginx
# Next.js hace proxy de /api/* → backend. No se expone directamente.
NEXT_PUBLIC_API_URL=https://tudominio.com
EOF
```

---

## 6. Levantar Servicios con Docker

### 6.1 Modificar docker-compose.yml para producción

El `docker-compose.yml` actual está configurado para desarrollo (puertos locales). Para producción, el único cambio es la contraseña de PostgreSQL:

```bash
cd /home/contadormx/contadormx

# Editar contraseña de PostgreSQL para que coincida con tu .env
nano docker-compose.yml
```

Cambia estas líneas:
```yaml
environment:
  POSTGRES_USER: contadormx
  POSTGRES_PASSWORD: TU_PASSWORD_POSTGRES   # <-- mismo que en DATABASE_URL
  POSTGRES_DB: contadormx
```

### 6.2 Levantar los contenedores

```bash
cd /home/contadormx/contadormx

# Levantar en background
docker compose up -d

# Verificar que los 3 contenedores están corriendo
docker compose ps
```

Debes ver:
```
NAME                      STATUS    PORTS
contadormx_postgres       Up        127.0.0.1:5432->5432/tcp
contadormx_redis          Up        127.0.0.1:6379->6379/tcp
contadormx_qdrant         Up        127.0.0.1:6333->6333/tcp
```

### 6.3 Verificar PostgreSQL

```bash
# Conectarse y verificar
docker exec -it contadormx_postgres psql -U contadormx -c "\l"
# Debe listar la base de datos "contadormx"
```

---

## 7. Backend — FastAPI

### 7.1 Crear entorno virtual Python

```bash
cd /home/contadormx/contadormx/backend

python3.11 -m venv venv
source venv/bin/activate

# Verificar Python correcto
which python  # debe ser /home/contadormx/contadormx/backend/venv/bin/python
```

### 7.2 Instalar dependencias Python

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

Este proceso tarda ~3-5 minutos la primera vez.

### 7.3 Ejecutar migraciones de base de datos

```bash
# Con el venv activado, desde /backend
alembic upgrade head
```

Verás algo como:
```
INFO  [alembic.runtime.migration] Running upgrade  -> 001, create users
INFO  [alembic.runtime.migration] Running upgrade 001 -> 002, create clientes
INFO  [alembic.runtime.migration] Running upgrade 002 -> 003, ...
INFO  [alembic.runtime.migration] Running upgrade ed13d28c -> 007, add sat verificacion
```

La migración **007** agrega tres columnas a `documentos`:
- `sat_estado` — Vigente / Cancelado / No Encontrado / error
- `sat_cancelable` — No cancelable / Cancelable con aceptación / ...
- `sat_verificado_at` — timestamp de la consulta al SAT

### 7.4 Probar el backend manualmente

```bash
# Prueba rápida para verificar que arranca sin errores
uvicorn app.main:app --host 127.0.0.1 --port 8000

# Verás:
# INFO:     Application startup complete.
# Ctrl+C para detener
```

---

## 8. Frontend — Next.js

### 8.1 Instalar dependencias Node

```bash
cd /home/contadormx/contadormx/frontend

npm install
```

### 8.2 Build de producción

```bash
npm run build
```

Este proceso tarda ~2-3 minutos y genera la carpeta `.next/`.

### 8.3 Probar el frontend manualmente

```bash
npm start
# Escucha en puerto 3000
# Ctrl+C para detener
```

---

## 9. Celery Worker + Beat Scheduler

Celery maneja tareas en background:
- Emails de bienvenida y reseteo de contraseña
- Recordatorios fiscales diarios
- Descarga masiva de CFDIs del SAT
- Scraping de DOF, SAT, INPC

### 9.1 Probar Celery manualmente

```bash
cd /home/contadormx/contadormx/backend
source venv/bin/activate

# Worker (procesador de tareas)
celery -A celery_app worker --loglevel=info

# En otra terminal, beat (programador de tareas)
celery -A celery_app beat --loglevel=info
```

Si no hay errores, pasa al siguiente paso para convertirlos en servicios systemd.

---

## 10. Nginx como Reverse Proxy

Nginx recibe todo el tráfico en el puerto 80/443 y lo distribuye:
- `/api/*` → FastAPI en `localhost:8000`
- Todo lo demás → Next.js en `localhost:3000`

### 10.1 Crear configuración Nginx

```bash
sudo nano /etc/nginx/sites-available/contadormx
```

Pega este contenido (reemplaza `tudominio.com`):

```nginx
server {
    listen 80;
    server_name tudominio.com www.tudominio.com;

    # Tamaño máximo de archivo para subida de documentos
    client_max_body_size 20M;

    # Headers de seguridad
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Backend API
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts más largos para procesamiento de documentos y LLM
        proxy_read_timeout 120s;
        proxy_connect_timeout 10s;
        proxy_send_timeout 120s;
    }

    # WebSockets (si los necesitas en el futuro)
    location /ws/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }

    # Frontend Next.js
    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Next.js hot reload (HMR) en dev — en prod no es necesario pero no daña
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 10.2 Activar el sitio

```bash
# Crear enlace simbólico
sudo ln -s /etc/nginx/sites-available/contadormx /etc/nginx/sites-enabled/

# Eliminar el sitio por defecto
sudo rm -f /etc/nginx/sites-enabled/default

# Verificar configuración
sudo nginx -t
# Debe decir: configuration file /etc/nginx/nginx.conf test is successful

# Recargar Nginx
sudo systemctl reload nginx
```

---

## 11. SSL con Let's Encrypt

### 11.1 Instalar Certbot

```bash
sudo apt install -y certbot python3-certbot-nginx
```

### 11.2 Obtener certificado SSL

```bash
# Reemplaza con tu email y dominio reales
sudo certbot --nginx -d tudominio.com -d www.tudominio.com \
  --email tu@email.com \
  --agree-tos \
  --non-interactive

# Certbot modifica automáticamente el nginx.conf para redirigir HTTP→HTTPS
```

### 11.3 Renovación automática

Certbot instala un cron automáticamente. Para verificar:

```bash
sudo certbot renew --dry-run
# Debe decir: Congratulations, all simulated renewals succeeded
```

---

## 12. Servicios systemd

Systemd mantiene todos los procesos corriendo y los reinicia si fallan.

### 12.1 Backend (FastAPI)

```bash
sudo nano /etc/systemd/system/contadormx-backend.service
```

```ini
[Unit]
Description=ContadorMX Backend (FastAPI)
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
User=contadormx
WorkingDirectory=/home/contadormx/contadormx/backend
Environment="PATH=/home/contadormx/contadormx/backend/venv/bin"
ExecStart=/home/contadormx/contadormx/backend/venv/bin/uvicorn \
    app.main:app \
    --host 127.0.0.1 \
    --port 8000 \
    --workers 2
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### 12.2 Frontend (Next.js)

```bash
sudo nano /etc/systemd/system/contadormx-frontend.service
```

```ini
[Unit]
Description=ContadorMX Frontend (Next.js)
After=network.target

[Service]
Type=simple
User=contadormx
WorkingDirectory=/home/contadormx/contadormx/frontend
ExecStart=/usr/bin/npm start
Restart=always
RestartSec=5
Environment=NODE_ENV=production
Environment=PORT=3000
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### 12.3 Celery Worker

```bash
sudo nano /etc/systemd/system/contadormx-celery-worker.service
```

```ini
[Unit]
Description=ContadorMX Celery Worker
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
User=contadormx
WorkingDirectory=/home/contadormx/contadormx/backend
Environment="PATH=/home/contadormx/contadormx/backend/venv/bin"
ExecStart=/home/contadormx/contadormx/backend/venv/bin/celery \
    -A celery_app worker \
    --loglevel=info \
    --concurrency=2
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### 12.4 Celery Beat (programador)

```bash
sudo nano /etc/systemd/system/contadormx-celery-beat.service
```

```ini
[Unit]
Description=ContadorMX Celery Beat Scheduler
After=network.target docker.service
Requires=docker.service

[Service]
Type=simple
User=contadormx
WorkingDirectory=/home/contadormx/contadormx/backend
Environment="PATH=/home/contadormx/contadormx/backend/venv/bin"
ExecStart=/home/contadormx/contadormx/backend/venv/bin/celery \
    -A celery_app beat \
    --loglevel=info
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### 12.5 Docker Compose como servicio

```bash
sudo nano /etc/systemd/system/contadormx-docker.service
```

```ini
[Unit]
Description=ContadorMX Docker Services (Postgres, Redis, Qdrant)
After=docker.service
Requires=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
User=contadormx
WorkingDirectory=/home/contadormx/contadormx
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
Restart=no
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

### 12.6 Activar todos los servicios

```bash
# Recargar systemd
sudo systemctl daemon-reload

# Habilitar (auto-arrancan en boot)
sudo systemctl enable contadormx-docker
sudo systemctl enable contadormx-backend
sudo systemctl enable contadormx-frontend
sudo systemctl enable contadormx-celery-worker
sudo systemctl enable contadormx-celery-beat

# Iniciar en orden
sudo systemctl start contadormx-docker
sleep 10  # Esperar que PostgreSQL y Redis estén listos

sudo systemctl start contadormx-backend
sudo systemctl start contadormx-frontend
sudo systemctl start contadormx-celery-worker
sudo systemctl start contadormx-celery-beat

# Verificar estado
sudo systemctl status contadormx-backend
sudo systemctl status contadormx-frontend
sudo systemctl status contadormx-celery-worker
```

---

## 13. Cargar Base de Leyes Fiscales

El agente de IA necesita la base de conocimiento legal (DOF, SAT, LISR, LIVA, etc.) cargada en Qdrant para responder preguntas fiscales.

```bash
cd /home/contadormx/contadormx
source backend/venv/bin/activate

# Paso 1: Descargar documentos legales
python scripts/download_laws.py

# Paso 2: Procesar y cargar en Qdrant
python scripts/bootstrap_laws.py

# El proceso puede tardar 15-30 minutos dependiendo del volumen de documentos
```

---

## 14. Crear Usuario Administrador

```bash
cd /home/contadormx/contadormx/backend
source venv/bin/activate

python create_admin.py
# Crea: admin@contadormx.mx / Admin2025! con plan agencia

# Para dar plan agencia a un usuario existente:
python upgrade_plan.py tu@email.com
```

---

## 15. Verificación Final

### Checklist de servicios

```bash
# Verificar todos los servicios están activos
sudo systemctl is-active contadormx-docker      # active
sudo systemctl is-active contadormx-backend     # active
sudo systemctl is-active contadormx-frontend    # active
sudo systemctl is-active contadormx-celery-worker  # active
sudo systemctl is-active contadormx-celery-beat    # active

# Verificar contenedores Docker
docker compose -f /home/contadormx/contadormx/docker-compose.yml ps

# Verificar Nginx
sudo systemctl is-active nginx  # active
```

### Verificar endpoints

```bash
# Health check del backend
curl https://tudominio.com/api/health
# Respuesta esperada: {"status":"ok"}

# Frontend (debe devolver HTML)
curl -I https://tudominio.com
# Respuesta esperada: HTTP/2 200
```

### Verificar logs

```bash
# Backend
sudo journalctl -u contadormx-backend -n 50 --no-pager

# Frontend
sudo journalctl -u contadormx-frontend -n 50 --no-pager

# Celery
sudo journalctl -u contadormx-celery-worker -n 50 --no-pager

# Nginx
sudo tail -50 /var/log/nginx/error.log
```

---

## 16. Comandos de Mantenimiento

### Actualizar el sistema (deploy de nueva versión)

```bash
cd /home/contadormx/contadormx

# 1. Descargar cambios
git pull origin main

# 2. Actualizar dependencias Python (si cambiaron)
source backend/venv/bin/activate
pip install -r backend/requirements.txt

# 3. Aplicar migraciones de BD
cd backend && alembic upgrade head && cd ..

# 4. Rebuild del frontend
cd frontend && npm install && npm run build && cd ..

# 5. Reiniciar servicios
sudo systemctl restart contadormx-backend
sudo systemctl restart contadormx-frontend
sudo systemctl restart contadormx-celery-worker
sudo systemctl restart contadormx-celery-beat
```

### Ver logs en tiempo real

```bash
# Backend en vivo
sudo journalctl -u contadormx-backend -f

# Todos los servicios a la vez
sudo journalctl -u contadormx-backend -u contadormx-frontend \
  -u contadormx-celery-worker -f
```

### Reiniciar un servicio específico

```bash
sudo systemctl restart contadormx-backend
sudo systemctl restart contadormx-frontend
sudo systemctl restart contadormx-celery-worker
sudo systemctl restart contadormx-celery-beat
```

### Conectarse a PostgreSQL

```bash
docker exec -it contadormx_postgres psql -U contadormx
```

### Conectarse a Redis

```bash
docker exec -it contadormx_redis redis-cli
```

---

## 17. Backup Automático

### 17.1 Script de backup

```bash
sudo nano /usr/local/bin/backup-contadormx.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/home/contadormx/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p "$BACKUP_DIR"

# Dump de PostgreSQL
docker exec contadormx_postgres pg_dump -U contadormx contadormx \
  | gzip > "$BACKUP_DIR/db_$DATE.sql.gz"

# Backup de Qdrant
docker exec contadormx_qdrant tar -czf - /qdrant/storage \
  > "$BACKUP_DIR/qdrant_$DATE.tar.gz"

# Backup del .env (contiene API keys)
cp /home/contadormx/contadormx/backend/.env \
  "$BACKUP_DIR/env_$DATE.bak"

# Eliminar backups de más de 30 días
find "$BACKUP_DIR" -name "*.gz" -mtime +30 -delete
find "$BACKUP_DIR" -name "*.bak" -mtime +7 -delete

echo "Backup completado: $DATE"
```

```bash
sudo chmod +x /usr/local/bin/backup-contadormx.sh
```

### 17.2 Programar con cron

```bash
sudo crontab -e
```

Agrega:
```cron
# Backup diario a las 3am
0 3 * * * /usr/local/bin/backup-contadormx.sh >> /var/log/backup-contadormx.log 2>&1
```

### 17.3 Restaurar backup

```bash
# Restaurar base de datos desde backup
gunzip -c /home/contadormx/backups/db_FECHA.sql.gz \
  | docker exec -i contadormx_postgres psql -U contadormx contadormx
```

---

## 18. Diferencias AWS vs Proxmox

### AWS EC2

| Aspecto | Configuración AWS |
|---------|------------------|
| Firewall | Security Groups en vez de UFW (ambos funcionan juntos) |
| IP pública | Asignar Elastic IP para que no cambie al reiniciar |
| Dominio | Route 53 o cualquier registrador apuntando al Elastic IP |
| Disco | Volumen EBS — el backup de BD es suficiente, EBS tiene snapshots propios |
| Acceso SSH | Llave `.pem`, usuario `ubuntu` por defecto |

Pasos adicionales AWS:
```bash
# En Security Groups, abrir:
# - Puerto 22 (SSH) — solo tu IP
# - Puerto 80 (HTTP) — 0.0.0.0/0
# - Puerto 443 (HTTPS) — 0.0.0.0/0
# Los puertos internos (5432, 6379, 6333) NO deben estar abiertos al exterior
```

### Proxmox VE

| Aspecto | Configuración Proxmox |
|---------|----------------------|
| VM | Ubuntu 22.04 cloud-init o instalación manual |
| Red | Bridge `vmbr0` con IP estática en la LAN |
| IP pública | NAT en el router: puerto 80/443 → IP de la VM |
| Dominio | DNS apuntando a tu IP pública del router |
| Snapshots | Proxmox permite snapshot de toda la VM (además del backup de BD) |

Configurar IP estática en Proxmox VM:
```bash
sudo nano /etc/netplan/00-installer-config.yaml
```
```yaml
network:
  version: 2
  ethernets:
    ens18:
      dhcp4: no
      addresses: [192.168.1.50/24]
      gateway4: 192.168.1.1
      nameservers:
        addresses: [8.8.8.8, 1.1.1.1]
```
```bash
sudo netplan apply
```

---

## Resumen del Stack Final

```
Internet
    ↓ 443 (HTTPS)
Nginx (reverse proxy + SSL)
    ├─ /api/* → FastAPI (puerto 8000)
    └─ /*     → Next.js (puerto 3000)

FastAPI
    ├─ PostgreSQL (Docker, puerto 5432)
    ├─ Redis (Docker, puerto 6379)
    ├─ Qdrant (Docker, puerto 6333)
    └─ Anthropic API (externa)

Celery Worker + Beat
    └─ Redis como broker
```

---

---

## Notas de versión

| Versión | Fecha | Cambios |
|---------|-------|---------|
| 1.1 | Abril 2026 | Tablas fiscales 2026 (UMA $117.31, SM $315.04, tarifa ISR Anexo 8 RMF 2026, subsidio fijo $536.21, CyV progresivo LSS Art. 168 BIS). Verificación automática CFDI vs SAT (migración 007). |
| 1.0 | Enero 2026 | Release inicial |

**Sistema objetivo:** Ubuntu 22.04 LTS  
**Última actualización:** Abril 2026
