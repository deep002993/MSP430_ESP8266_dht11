import requests
from bs4 import BeautifulSoup
import csv
from datetime import datetime
import time
import pywhatkit
import pyautogui
from pynput.keyboard import Key, Controller

keyboard = Controller()


def send_whatsapp_message(msg: str):
    try:
        pywhatkit.sendwhatmsg_instantly(
            phone_no="+91xxxxxxxxxx",
            message=msg,
            tab_close=True
        )
        time.sleep(10)  # Adjust the sleep duration as needed
        pyautogui.click()  # Click on the WhatsApp Web window
        
        time.sleep(2)
        keyboard.press(Key.enter)
        keyboard.release(Key.enter)
        print("Message sent!")
    except Exception as e:
        print(str(e))
        


def scrape_and_send():
    # URL of the webpage to scrape
    url = "http://192.168.1.41/:80"  # Replace with the actual URL

    while True:
        # Send an HTTP request to the webpage
        response = requests.get(url)

        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Parse the HTML content of the page
            soup = BeautifulSoup(response.text, "html.parser")

            # Find the table containing the sensor readings
            table = soup.find("table")

            # Check if the table is found
            if table:
                # Extract data from each row in the table
                rows = table.find_all("tr")[1:]  # Skip the header row
                for row in rows:
                    # Extract data from each cell in the row
                    cells = row.find_all("td")

                    # Extract values from each cell
                    timestamp = cells[0].text.strip()
                    temperature_c = cells[1].text.strip()
                    temperature_f = cells[2].text.strip()
                    humidity = cells[3].text.strip()
                    air_quality_ppm = cells[4].text.strip()

                    # Do something with the extracted data (e.g., print or store in a data structure)
                    print("Timestamp:", timestamp)
                    print("Temperature (C):", temperature_c)
                    print("Temperature (F):", temperature_f)
                    print("Humidity (%):", humidity)
                    print("Air Quality (PPM):", air_quality_ppm)
                    print("----------------")

                    # Create a message with the sensor readings
                    message = f"Sensor Readings:\nTimestamp: {timestamp}\nTemperature (C): {temperature_c}\nTemperature (F): {temperature_f}\nHumidity (%): {humidity}\nAir Quality (PPM): {air_quality_ppm}"

                    # Send the message to the specified WhatsApp number
                    print("Sending message...")
                    send_whatsapp_message(message)
                    print("Message sent successfully.")
            else:
                print("Table not found on the webpage.")
        else:
            print(f"Failed to retrieve data from {url}. Status code: {response.status_code}")

        # Wait for two seconds before fetching data again
        time.sleep(18)


if __name__ == "__main__":
    scrape_and_send()
