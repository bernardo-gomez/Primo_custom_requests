#
# usage:  make -f makefile webserverAccess
CC = /usr/bin/gcc
OPTIONS = -c -g

webserverAccess: webserverAccess.o
	$(CC) -o webserverAccess webserverAccess.o
webserverAccess.o: webserverAccess.c
	$(CC) $(OPTIONS) webserverAccess.c

