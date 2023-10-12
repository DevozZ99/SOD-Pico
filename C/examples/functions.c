#include "test.h"
#include "OLED_1in12_v3.h"

#include<time.h>
#include<unistd.h>
#include<stdio.h>

int show_meteo(char* cond_code, char* temp, char* hum)
{
	if(DEV_ModuleInit() != 0) {
		return -1;
	}
	
	OLED_1in12_v3_Init();
	DEV_Delay_ms(500);	
	// 0.Create a new image cache
	UBYTE *BlackImage;
	UWORD Imagesize = ((OLED_1in12_v3_WIDTH%8==0)? (OLED_1in12_v3_WIDTH/8): (OLED_1in12_v3_WIDTH/8+1)) * OLED_1in12_v3_HEIGHT;
	if((BlackImage = (UBYTE *)malloc(Imagesize)) == NULL) {
			printf("Failed to apply for black memory...\r\n");
			return -1;
	}
	
	Paint_NewImage(BlackImage, OLED_1in12_v3_WIDTH, OLED_1in12_v3_HEIGHT, 180, BLACK);	

	//1.Select Image
	Paint_SelectImage(BlackImage);
	DEV_Delay_ms(500);
	Paint_Clear(BLACK);
	// Drawing on the image
	GUI_ReadBmp(cond_code, 0, 0);
	// Show image on page4
	OLED_1in12_v3_Display(BlackImage);
	DEV_Delay_ms(2000);	
	Paint_Clear(BLACK);	
	OLED_1in12_v3_Clear();
	
	Paint_DrawString_EN(10, 48, temp, &FontCUSTOM, WHITE, WHITE);
	// Show image on page4
	OLED_1in12_v3_Display(BlackImage);
	DEV_Delay_ms(2000);		
	Paint_Clear(BLACK);
	OLED_1in12_v3_Clear();
	
	Paint_DrawString_EN(10, 48, hum, &FontCUSTOM, WHITE, WHITE);
	// Show image on page4
	OLED_1in12_v3_Display(BlackImage);
	DEV_Delay_ms(2000);		
	Paint_Clear(BLACK);
	OLED_1in12_v3_Clear();
	
	//DEV_ModuleExit();
	
	return 0;
}

int show_logo(void)
{
	if(DEV_ModuleInit() != 0) {
		return -1;
	}
	  
	printf("OLED Init...\r\n");
	OLED_1in12_v3_Init();
	DEV_Delay_ms(500);	
	// 0.Create a new image cache
	UBYTE *BlackImage;
	UWORD Imagesize = ((OLED_1in12_v3_WIDTH%8==0)? (OLED_1in12_v3_WIDTH/8): (OLED_1in12_v3_WIDTH/8+1)) * OLED_1in12_v3_HEIGHT;
	if((BlackImage = (UBYTE *)malloc(Imagesize)) == NULL) {
			printf("Failed to apply for black memory...\r\n");
			return -1;
	}
	printf("Paint_NewImage\r\n");
	Paint_NewImage(BlackImage, OLED_1in12_v3_WIDTH, OLED_1in12_v3_HEIGHT, 180, BLACK);	

	
	printf("Drawing\r\n");
	//1.Select Image
	Paint_SelectImage(BlackImage);
	DEV_Delay_ms(500);
	Paint_Clear(BLACK);
	// Drawing on the image
	GUI_ReadBmp("./pic/rasplogo.bmp", 0, 0);
	// Show image on page4
	OLED_1in12_v3_Display(BlackImage);
	DEV_Delay_ms(5000);		
	Paint_Clear(BLACK);
	OLED_1in12_v3_Clear();
	
	return 0;
}

int show_time(char* time_str)
{
	if(DEV_ModuleInit() != 0) {
		return -1;
	}
	  
	printf("OLED Init...\r\n");
	OLED_1in12_v3_Init();
	DEV_Delay_ms(500);	
	// 0.Create a new image cache
	UBYTE *BlackImage;
	UWORD Imagesize = ((OLED_1in12_v3_WIDTH%8==0)? (OLED_1in12_v3_WIDTH/8): (OLED_1in12_v3_WIDTH/8+1)) * OLED_1in12_v3_HEIGHT;
	if((BlackImage = (UBYTE *)malloc(Imagesize)) == NULL) {
			printf("Failed to apply for black memory...\r\n");
			return -1;
	}
	printf("Paint_NewImage\r\n");
	Paint_NewImage(BlackImage, OLED_1in12_v3_WIDTH, OLED_1in12_v3_HEIGHT, 180, BLACK);	

	
	printf("Drawing\r\n");
	//1.Select Image
	Paint_SelectImage(BlackImage);
	DEV_Delay_ms(500);
	Paint_Clear(BLACK);
	// Drawing on the image
	
	//time_t currentTime;
	//struct tm *localTime;
	//time(&currentTime);
	//localTime = localtime(&currentTime);
	//int hours = localTime->tm_hour;
	//int mins = localTime->tm_min;
	
	//char hours_str[3];
	//char mins_str[3];
	//char time_str[6];
	
	//sprintf(hours_str, "%02d", hours);
	//sprintf(mins_str, "%02d", mins);
	
	//time_str[5] = '\0';
	//time_str[4] = mins_str[1];
	//time_str[3] = mins_str[0];
	//time_str[2] = ':';
	//time_str[1] = hours_str[1];
	//time_str[0] = hours_str[0];	
	
	Paint_DrawString_EN(10, 48, time_str, &FontCUSTOM, WHITE, WHITE);
	
	// Show image on page4
	OLED_1in12_v3_Display(BlackImage);	
	DEV_Delay_ms(5000);
	Paint_Clear(BLACK);
	OLED_1in12_v3_Clear();
	
	return 0;
}

