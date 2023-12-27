import serial
import time
import re
import matplotlib.pyplot as plt
from drawnow import drawnow

# Initialize empty lists for data storage
time_data = []
temperature_data = []

# Counter for generating unique filenames
plot_counter = 0
temp_file = open('temperature.txt', 'a', encoding='utf-8')

# Create a function to update the plot
def update_plot():
    plt.clf()
    plt.title("Real-Time Temperature Monitoring")
    plt.xlabel("Time")
    plt.ylabel("Temperature (°C)")
    plt.grid(True)
    plt.plot(time_data, temperature_data, label="Temperature (°C)")
    plt.xticks(rotation=45)  # Rotate x-axis labels by 45 degrees
    plt.legend(loc="upper left")

    # Save the plot with a unique filename
    global plot_counter
    plot_counter += 1
    filename = f'C:/Users/deep/Documents/CCS/pyserial/newplot/temperature_plot_{plot_counter}.png'
    plt.savefig(filename, format='png')

# Open a serial connection
ser = serial.Serial('COM5', 9600)

# Create a loop to continuously read data and update the plot
while True:
    line0 = ser.readline()
    line = ser.readline().decode().strip()

    year, month, day, hour, mins, secs, _, _, _ = time.localtime()
    today = "{:04d}-{:02d}-{:02d} , {:02d}:{:02d}:{:02d}".format(year, month, day, hour, mins, secs)

    # Extract temperature from the line
    match = re.search(r'Temperature is: (\d+\.\d+)', line)
    temp_file.write(today + " ,\t")
    temp_file.write(line0.decode())
  
    if match:
        temperature = float(match.group(1))
        print(today + " , " + line)
        time_data.append(today)
        temperature_data.append(temperature)

    # Limit the number of data points to display on the graph
    if len(time_data) > 10:
        time_data.pop(0)
        temperature_data.pop(0)

    # Call the update_plot function to redraw and save the graph
    drawnow(update_plot)
