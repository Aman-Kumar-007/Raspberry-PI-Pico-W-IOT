import network
import utime
import socket
import json
from machine import Pin

# WiFi Credentials
SSID = 'Your SSID'
PASSWORD = 'Your SSID Password'

# Pins for sensors
trigger = Pin(3, Pin.OUT)
echo = Pin(2, Pin.IN)
pir_sensor = Pin(4, Pin.IN)

# Connect to WiFi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(SSID, PASSWORD)

# Wait for the connection
wait = 10
while wait > 0:
    if wlan.status() < 0 or wlan.status() >= 3:
        break
    wait -= 1
    print('waiting for connection...')
    utime.sleep(1)

# Handle connection error
if wlan.status() != 3:
    raise RuntimeError('WiFi connection failed')
else:
    print('Connected')
    ip = wlan.ifconfig()[0]
    print('IP:', ip)

def ultra():
    trigger.low()
    utime.sleep_us(2)
    trigger.high()
    utime.sleep_us(5)
    trigger.low()
    while echo.value() == 0:
        signaloff = utime.ticks_us()
    while echo.value() == 1:
        signalon = utime.ticks_us()
    timepassed = signalon - signaloff
    distance = (timepassed * 0.0343) / 2
    return distance

def webpage():
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Raspberry pi pico W web server</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                text-align: center;
                margin-top: 50px;
                background-color: #f4f4f4;
            }}
            p {{
                background-color: #fff;
                display: inline-block;
                padding: 20px 40px;
                border-radius: 10px;
                box-shadow: 0px 0px 15px rgba(0, 0, 0, 0.1);
            }}
            span {{
                font-weight: bold;
                color: #2c3e50;
            }}
        </style>
        <script>
            function updateData() {{
                fetch('/data')
                .then(response => response.json())
                .then(data => {{
                    document.getElementById('dist').innerHTML = data.distance;
                    document.getElementById('motion').innerHTML = data.motion;
                }});
            }}
            setInterval(updateData, 1000);  // fetch new data every 5 seconds
        </script>
    </head>
    <body onload="updateData()">  <!-- Call the function when the page loads -->
        <p>Distance: <span id="dist"></span> cm</p>
        <br>
        <p>Motion Status: <span id="motion"></span></p>
    </body>
    </html>
    """
    return html


def serve(connection):
    while True:
        client, _ = connection.accept()
        request = client.recv(1024)
        request = str(request)
        try:
            request = request.split()[1]
        except IndexError:
            pass
        if request == '/data':
            distance = ultra()
            motion_status = "Detected" if pir_sensor.value() == 1 else "Clear"
            response = json.dumps({'distance': distance, 'motion': motion_status})
            client.send("HTTP/1.1 200 OK\n")
            client.send("Content-Type: application/json\n")
            client.send("Content-Length: {}\n\n".format(len(response)))
            client.send(response)
        else:
            html = webpage()
            client.send("HTTP/1.1 200 OK\n")
            client.send("Content-Type: text/html\n")
            client.send("Content-Length: {}\n\n".format(len(html)))
            client.send(html)
        client.close()

def open_socket(ip):
    address = (ip, 80)
    connection = socket.socket()
    connection.bind(address)
    connection.listen(1)
    return connection

try:
    if ip is not None:
        connection = open_socket(ip)
        serve(connection)
except KeyboardInterrupt:
    pass
