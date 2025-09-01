# E-commerce (React + Flask mikroservisi)
Frontend: React (Vite) CRUD

Backend: Flask mikroservisi (products, orders, users) + API Gateway

Broker: Redis

Middleware: request logger sa X-Request-ID
## Start (potreban instaliran Docker)
docker compose up --build

Gateway: http://localhost:8000

Frontend: cd frontend && npm install && npm run dev (http://localhost:5173)

## Start (ako nemate Docker)

1. Instalirajte Python 3.10+ i Node.js 18+
2. U svakom servisu (gateway/, user_service/, product_service/, order_service/):

    pip install -r requirements.txt
    
    python app.py

3. U frontend/:

    npm install

    npm run dev

Pristup

Admin login:

Email: admin@gmail.com

Password: admin

Korisnici: registracija preko /register rute u aplikaciji.

## Za učitavanje .db fajlova iz foldera sample_data:

#### Posle prvog pokretanja compose-a, prekopiraj sample u volume:

docker cp ./sample_data/product.db $(docker compose ps -q product_service):/data/app.db

docker cp ./sample_data/order.db   $(docker compose ps -q order_service):/data/app.db

docker cp ./sample_data/user.db    $(docker compose ps -q user_service):/data/app.db

### Ako koristite Docker:

#### zaustavi servise
docker compose stop product_service order_service user_service

#### kopiraj tvoje baze u kontejnere
docker cp .\sample_data\product.db ecommerce-microservices-product_service-1:/data/app.db

docker cp .\sample_data\order.db   ecommerce-microservices-order_service-1:/data/app.db

docker cp .\sample_data\user.db    ecommerce-microservices-user_service-1:/data/app.db


#### ponovo pokreni servise
docker compose start product_service order_service user_service


### Ako ne koristite Docker:

Mora da se instalira Python i Node.js i da se pokreću servisi ručno.

U svakom servisu (product_service, order_service, user_service) postoji fajl app.db (SQLite).

Zamenite svoje app.db fajlove sa tvojim .db fajlovima:

sample_data/product.db → kopirajte u product_service/data/app.db

sample_data/order.db → kopirajte u order_service/data/app.db

sample_data/user.db → kopirajte u user_service/data/app.db

Kada pokrenete python app.py u svakom servisu, aplikacija koristi podatke.