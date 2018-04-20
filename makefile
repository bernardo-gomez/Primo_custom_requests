#
# usage:  make -f makefile webserverAccess
CC = /usr/bin/gcc
OPTIONS = -c -g

webserverAccess: webserverAccess.o
	$(CC) -o webserverAccess webserverAccess.o
	chmod 6711  webserverAccess
webserverAccess.o: webserverAccess.c
	$(CC) $(OPTIONS) webserverAccess.c

