FROM postgres:16-alpine

# Cron + gzip já vêm no alpine
RUN apk add --no-cache busybox-suid

COPY backup.sh /usr/local/bin/backup.sh
RUN chmod +x /usr/local/bin/backup.sh

# Cron: todo dia às 03:00 UTC
RUN echo "0 3 * * * /usr/local/bin/backup.sh >> /var/log/cron.log 2>&1" > /etc/crontabs/root

CMD ["sh", "-c", "touch /var/log/cron.log && crond -f -L /var/log/cron.log"]
