#include <stdlib.h>     //exit()
#include <signal.h>     //signal()
#include "test.h"
#include <string.h>


int main(int argc, char *argv[])
{
    
    if (argc < 2){
        printf("please input OLED size and type! \r\n");
        printf("example: sudo ./main 1.12v3 or sudo ./main 1.12v3badapple \r\n");
        exit(1);
    }
	
	printf("%s OLED Module\r\n", argv[1]);
		
	if(strcmp(argv[1], "meteo") == 0)
		show_meteo(argv[2], argv[3], argv[4]);
	else if(strcmp(argv[1], "logo") == 0)
		show_logo();
	else if(strcmp(argv[1], "time") == 0)
		show_time(argv[2]);
	else
	{
		printf("error: can not find the OLED\r\n");
		return -1;
	}
	
	return 0;	
}
