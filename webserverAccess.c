#include        <stdio.h>
#include        <stdlib.h>
#include	<string.h>
#include	<wchar.h>
#include	<locale.h>
#include	<errno.h>
#include        <unistd.h>


/* 
   this program performs an execv and its goal is to provide setuid
   to a designated program.
*/

static void givehelp(char *name){
     fprintf(stderr,"   %s %s\n",name, " expects at least one argument: a program name followed by its corresponding arguments.");
     fprintf(stderr,"   %s %s\n",name," performs an execv to run the designated program. " );
     fprintf(stderr,"   %s\n", " this method is recommended to give setuid permission to the program via 'chmod 6711 program'");

      }
#define MAX_ARGS    10

int main (int argc, char *argv[]){
  extern  void givehelp(char* name);

  int		i;
  int		k;
  int      	outcome;
  char*         argument[MAX_ARGS];
  setlocale(LC_ALL, "en_US.UTF-8");
/* chmod 6711  ./webserverAccess */
  if (argc < 2){
         fwprintf(stderr,L"%S\n",L"no program specified");
         givehelp(argv[0]);
         exit(1);
  }
  for (i=0;i<MAX_ARGS;i++){
    argument[i]=NULL;
  }
  k=0;
  for (i=1;i<argc ;i++){
      if (i == MAX_ARGS){   /* be safe */
         argument[MAX_ARGS-1]=NULL;
         break;
      }
      argument[k]=argv[i];
      k++;
  }
  
  outcome=execv(argv[1],argument); 
  if (outcome == -1){
         fwprintf(stderr,L"failure: %d\n",errno);
         exit(1);
  }
  exit(0);
}
