FROM mysql:8.0
EXPOSE 3306

ADD ./my.cnf /etc/mysql/conf.d/my.cnf
COPY ./restore/dump.sql /
COPY ./restore/local_cat_db.sql /

CMD ["mysqld"]