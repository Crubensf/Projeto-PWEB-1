FROM httpd:2.4

RUN apt-get update && apt-get install -y --no-install-recommends openssl \
    && rm -rf /var/lib/apt/lists/*

RUN mkdir -p /usr/local/apache2/conf/ssl && \
    openssl req -x509 -nodes -days 3650 -newkey rsa:2048 \
      -keyout /usr/local/apache2/conf/ssl/server.key \
      -out /usr/local/apache2/conf/ssl/server.crt \
      -subj "/C=BR/ST=SP/L=SaoPaulo/O=VanJa/OU=Dev/CN=localhost"

COPY httpd.conf /usr/local/apache2/conf/httpd.conf

COPY . /usr/local/apache2/htdocs/

RUN rm -f /usr/local/apache2/htdocs/Dockerfile \
          /usr/local/apache2/htdocs/httpd.conf

EXPOSE 80 443
