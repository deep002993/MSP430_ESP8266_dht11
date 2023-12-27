#include <msp430.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include "SSD1306.h"
#include "i2c.h"
#include <inttypes.h>
#include <stdio.h>
#include <Library/LunchboxCommon.h>

#define OLED_PWR    BIT0

volatile int temp[50];
volatile int diff[50];
volatile unsigned int i = 0;
volatile unsigned int j = 0;
char th_char[5];
char tl_char[5];
char hh_char[5];
char hl_char[5];
volatile int hh = 0;
volatile int hl = 0;
volatile int th = 0;
volatile int tl = 0;
volatile int check = 0;
volatile int checksum = 0;
volatile int dataok;
char temperature[] = "Temperature is: ";
char dot[] = ".";
char celcius[] = " degrees Celsius  ";
char humidity[] = "Humidity is: ";
char percent[] = " %";
char air_quality[] = " Air Quality: ";
char ppm[] = " ppm\r\n";

volatile unsigned int mq_reading = 0;
volatile unsigned int ppm_concentration;

void ser_output(char *str);
void mq135_init();
void mq135_read();
void displayDataOnOLED(int temperature, int humidity, int airQuality);

void main(void) {
    WDTCTL = WDTPW | WDTHOLD;
    P1SEL = BIT1 | BIT2;
    P1SEL2 = BIT1 | BIT2;

    UCA0CTL1 |= UCSSEL_1;
    UCA0BR0 = 3;
    UCA0BR1 = 0;
    UCA0MCTL = UCBRF_0 + UCBRS_3;
    UCA0MCTL &= ~UCOS16;
    UCA0CTL1 &= ~UCSWRST;
    IE2 |= UCA0RXIE;

    __delay_cycles(2000000);

    P2DIR |= BIT4;
    P2OUT &= ~BIT4;
    __delay_cycles(20000);
    P2OUT |= BIT4;
    __delay_cycles(20);
    P2DIR &= ~BIT4;
    P2SEL |= BIT4;

    TA1CTL = TASSEL_2 | MC_2;
    TA1CCTL2 = CAP | CCIE | CCIS_0 | CM_2 | SCS;
    _enable_interrupts();

    mq135_init();

    while (1) {
        if (i >= 40) {
            for (j = 1; j <= 8; j++) {
                if (diff[j] >= 110)
                    hh |= (0x01 << (8 - j));
            }
            for (j = 9; j <= 16; j++) {
                if (diff[j] >= 110)
                    hl |= (0x01 << (16 - j));
            }
            for (j = 17; j <= 24; j++) {
                if (diff[j] >= 110)
                    th |= (0x01 << (24 - j));
            }
            for (j = 25; j <= 32; j++) {
                if (diff[j] >= 110)
                    tl |= (0x01 << (32 - j));
            }
            for (j = 33; j <= 40; j++) {
                if (diff[j] >= 110)
                    checksum |= (0x01 << (40 - j));
            }
            check = hh + hl + th + tl;
            if (check == checksum)
                dataok = 1;
            else
                dataok = 0;

            // Convert temperature and humidity to strings
            ltoa(th, th_char, 10);
            ltoa(tl, tl_char, 10);
            ltoa(hh, hh_char, 10);
            ltoa(hl, hl_char, 10);

            // Send data over UART
            ser_output(temperature);
            ser_output(th_char);
            ser_output(dot);
            ser_output(tl_char);
            ser_output(celcius);
            ser_output(humidity);
            ser_output(hh_char);
            ser_output(dot);
            ser_output(hl_char);
            ser_output(percent);

            // Display data on OLED


            // Convert MQ135 reading to ppm
            mq135_read();
            displayDataOnOLED(th, hh, ppm_concentration);

            __delay_cycles(1000000);
            WDTCTL = WDT_MRST_0_064;
        }
    }
}

void displayDataOnOLED(int temperature, int humidity, int airQuality) {
    char tempStr[10];
    char humStr[10];
    char airQualityStr[10];
    char airQualityStatus[20];

    // Initialize I2C and OLED
    i2c_init();
    ssd1306_init();

    // Convert temperature, humidity, and air quality values to strings
    ltoa(temperature, tempStr, 10);
    ltoa(humidity, humStr, 10);
    ltoa(airQuality, airQualityStr, 10);

    // Clear OLED display
    ssd1306_clearDisplay();

    // Display temperature
    ssd1306_printText(0, 0, "Temperature: ");
    ssd1306_printText(80, 0, tempStr);
    ssd1306_printText(95, 0, "C");

    // Display humidity
    ssd1306_printText(0, 2, "Humidity: ");
    ssd1306_printText(70, 2, humStr);
    ssd1306_printText(85, 2, "%");

    // Display air quality
    ssd1306_printText(0, 4, "Air Quality: ");
    ssd1306_printText(75, 4, airQualityStr);
    ssd1306_printText(100, 4, "ppm");

    // Determine air quality status
    if (airQuality >= 0 && airQuality <= 50) {
        strcpy(airQualityStatus, "Good ");
    } else if (airQuality <= 100) {
        strcpy(airQualityStatus, "Moderate ");
    } else if (airQuality <= 150) {
        strcpy(airQualityStatus, "Unhealthy ");
    } else if (airQuality <= 200) {
        strcpy(airQualityStatus, "Unhealthy adverse effects");
    } else if (airQuality <= 300) {
        strcpy(airQualityStatus, "Very Unhealthy-Health alert");
    } else {
        strcpy(airQualityStatus, "Hazardous-Emergency");
    }

    // Display air quality status
    ssd1306_printText(0, 6, airQualityStatus);

}

// Rest of the code remains unchanged


#pragma vector = TIMER1_A1_VECTOR
__interrupt void Timer_A1(void) {
    temp[i] = TA1CCR2;
    i += 1;
    TA1CCTL2 &= ~CCIFG;
    if (i >= 2)
        diff[i - 1] = temp[i - 1] - temp[i - 2];
}

void ser_output(char *str) {
    while (*str != 0) {
        while (!(IFG2 & UCA0TXIFG));
        UCA0TXBUF = *str++;
    }
}

void mq135_init() {
    P1DIR &= ~BIT0;  // Set P1.0 as an input (analog input)
    P1SEL |= BIT0;   // Select P1.0 for analog input
}

void mq135_read() {
    // Read the analog value from P1.0
    ADC10CTL1 = INCH_0;          // Set the input channel to A0 (P1.0)
    ADC10CTL0 = SREF_0 + ADC10SHT_3 + ADC10ON + ADC10IE;
    __delay_cycles(1000);        // Delay for reference voltage settling
    ADC10CTL0 |= ENC + ADC10SC;   // Start the conversion
    __bis_SR_register(CPUOFF + GIE);  // Enter LPM0 with interrupts enabled

    // Assuming a linear relationship between analog value and gas concentration
    // You may need to calibrate this for your specific sensor
    mq_reading = ADC10MEM;  // Store the analog reading

    // Convert the analog reading to ppm (adjust these parameters)
    ppm_concentration = mq_reading * 2;  // Adjust this factor

    // Send the result over UART
    ser_output(air_quality);
    ltoa(ppm_concentration, th_char, 10);  // Convert to string
    ser_output(th_char);
    ser_output(ppm);
}

#pragma vector = ADC10_VECTOR
__interrupt void ADC10_ISR(void) {
    __bic_SR_register_on_exit(CPUOFF);  // Disable Low Power Mode and return to active mode
}
