/******************************************************************
*  Title: USR-WIFI232-T PWM configurator
*  Description: This program starts an Arduino and simply sends 
*               the proper commands in order to make it work as 
*               a remote PWM module
*
*  Version:      0.1
*  Date:         February 2nd, 2015
*  License:      GPL
*  Author:       Ángel Hernández
*  Contributors: Ángel Hernández
*  Contact:  angel@tupperbot.com   
*            @mifulapirus
******************************************************************/

void setup() {
  Serial.begin(115200);  //Create the serial port at the default speed for the WiFi module
}

void loop() {
  Serial.print("+++");  //Enter the AT mode for configuration
  delay(200);           
  Serial.print("a");    //Block AT mode until reset
  delay(200);  
  Serial.println("AT+TMODE=pwm");  //Set the module to PWM mode. It will not send data through its serial port anymore
  while (true) {}       //Block the program
}
