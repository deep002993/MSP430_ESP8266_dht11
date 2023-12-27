from machine import Pin, ADC
from time import sleep
import time
import dht
import network
import usocket as socket

# Set up the DHT11 sensor
dht_pin = Pin(14)  # Replace with the actual GPIO pin number you're using
dht_sensor = dht.DHT11(dht_pin)

# Set up the MQ135 sensor
mq135_pin = 0  # Replace with the actual ADC pin number you're using
mq135_adc = ADC(mq135_pin)

# Set up Wi-Fi connection
ssid = "ruby"
password = "9953129282"
ap = network.WLAN(network.STA_IF)
ap.active(True)
ap.connect(ssid, password)

while not ap.isconnected():
    pass

station = network.WLAN(network.STA_IF)
print(station.ifconfig())
print("Connected to Wi-Fi")

# Create a list to store sensor readings
sensor_readings = []

# Create a socket server
port = 8046
server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(('', port))
server.listen(5)
print('Web server started on', 'http://{}:{}'.format(station.ifconfig()[0], port))

# Function to read MQ135 sensor data
def read_mq135_sensor():
    try:
        mq135_value = mq135_adc.read()
        # You may need to calibrate the MQ135 sensor to convert the ADC reading to PPM.
        # Refer to the sensor datasheet for calibration details.
        air_quality_ppm = mq135_value * 1.8  # Adjust this line based on calibration.
        return air_quality_ppm
    except Exception as e:
        print("Error reading MQ135:", e)
        return None

# Function to read DHT11 sensor data
def read_dht_sensor():
    try:
        dht_sensor.measure()
        temp = dht_sensor.temperature()
        hum = dht_sensor.humidity()
        temp_f = temp * (9/5) + 32.0
        return {
            "timestamp": time.localtime(),
            "temperature_celsius": temp,
            "temperature_fahrenheit": temp_f,
            "humidity_percentage": hum,
        }
    except Exception as e:
        print("Error reading DHT11:", e)
        return None

# Function to format the sensor reading as HTML table row
def format_sensor_row(sensor_data):
    timestamp_str = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}".format(
        sensor_data.get("timestamp", (0, 0, 0, 0, 0, 0))[0],
        sensor_data.get("timestamp", (0, 0, 0, 0, 0, 0))[1],
        sensor_data.get("timestamp", (0, 0, 0, 0, 0, 0))[2],
        sensor_data.get("timestamp", (0, 0, 0, 0, 0, 0))[3],
        sensor_data.get("timestamp", (0, 0, 0, 0, 0, 0))[4],
        sensor_data.get("timestamp", (0, 0, 0, 0, 0, 0))[5],
    )
    return "<tr><td>{}</td><td>{:.1f} C</td><td>{:.1f} F</td><td>{:.1f} %</td><td>{:.1f} PPM</td></tr>".format(
        timestamp_str,
        sensor_data.get("temperature_celsius", 0),
        sensor_data.get("temperature_fahrenheit", 0),
        sensor_data.get("humidity_percentage", 0),
        sensor_data.get("air_quality_ppm", 0),
    )

# Main loop
while True:
    try:
        # Read sensor data
        sensor_data = read_dht_sensor()
        air_quality_ppm = read_mq135_sensor()

        if sensor_data and air_quality_ppm is not None:
            # Add air quality reading to sensor data
            sensor_data["air_quality_ppm"] = air_quality_ppm

            # Append the sensor reading to the list
            sensor_readings.append(sensor_data)

            # Keep only the last 10 sensor readings
            if len(sensor_readings) > 17:
                sensor_readings.pop(0)

            # Create an HTML page with the current sensor reading and a table of previous readings
            html_response = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Sensor Readings</title>
                <meta http-equiv="refresh" content="2"> <!-- Auto-refresh the page every 3 seconds -->
                <style>
                    body {{
                        background-color: #FFF8E1; /* Cream background color */
                        font-family: Arial, sans-serif;
                        font-size: 24px; /* Increase the font size */
                        width: 100%; /* Decrease width to 80% */
                        margin: auto; /* Center the content */
                    }}
                    h1, h2 {{
                        color: #4CAF50; /* Green header text color */
                        font-size: 24px; /* Increase the font size */
                    }}
                    table {{
                        width: 100%;
                        border-collapse: collapse;
                        margin-top: 10px;
                    }}
                    th, td {{
                        border: 1px solid #ddd;
                        padding: 12px; /* Increase the padding */
                        text-align: left;
                    }}
                    tr:nth-child(even) {{
                        background-color: #f2f2f2;
                    }}
                </style>
            </head>
            <body>
                <h1>Current Sensor Reading</h1>
                <p>Timestamp: {:04d}-{:02d}-{:02d} {:02d}:{:02d}:{:02d}, 
                    Temperature: {:.1f} C, Temperature: {:.1f} F, 
                    Humidity: {:.1f} %, Air Quality: {:.1f} PPM</p>
                
                <h2>Previous Sensor Readings</h2>
                <table>
                    <tr>
                        <th>Timestamp</th>
                        <th>Temperature (C)</th>
                        <th>Temperature (F)</th>
                        <th>Humidity (%)</th>
                        <th>Air Quality (PPM)</th>
                    </tr>
                    {}
                </table>
            </body>
            </html>
            """.format(
                sensor_data.get("timestamp", (0, 0, 0, 0, 0, 0))[0],
                sensor_data.get("timestamp", (0, 0, 0, 0, 0, 0))[1],
                sensor_data.get("timestamp", (0, 0, 0, 0, 0, 0))[2],
                sensor_data.get("timestamp", (0, 0, 0, 0, 0, 0))[3],
                sensor_data.get("timestamp", (0, 0, 0, 0, 0, 0))[4],
                sensor_data.get("timestamp", (0, 0, 0, 0, 0, 0))[5],
                sensor_data.get("temperature_celsius", 0),
                sensor_data.get("temperature_fahrenheit", 0),
                sensor_data.get("humidity_percentage", 0),
                sensor_data.get("air_quality_ppm", 0),
                ''.join(map(format_sensor_row, sensor_readings) if sensor_readings else '')
            )

            # Serve the HTML page with the sensor readings
            conn, addr = server.accept()
            request = conn.recv(1024).decode()

            conn.send('HTTP/1.1 200 OK\n')
            conn.send('Content-Type: text/html\n')
            conn.send('Connection: close\n\n')
            conn.sendall(html_response)

            conn.close()

        # Sleep for 2 seconds before the next reading
        sleep(2)

    except OSError as e:
        print('Failed to read sensor.')
