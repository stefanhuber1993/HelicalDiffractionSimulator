# HelicalDiffractionSimulator
Web Service to Simulate the diffraction patterns of helical (protein) specimen

## Screenshot
![Screenshot](/img/screen.png) 


## Run directly
Run it by:
python2.7 bin/server.py ${SPRING_IP} ${SPRING_PORT} ${SPRING_UPLOAD} ${SPRING_BASE}${SPRING_WWWSTATIC}
The python interpreter in this case is the one packaged with EMAN2, since EMAN2 is required for reading hdf and mrc files.

## Run as a Service
File springServer.service in /etc/systemd/system/ containing:

[Unit]
Description=Web Service Helical Specimen Simulation
After=syslog.target network.target

[Service]
User=spring
EnvironmentFile=/opt/springWeb/etc/server.cfg
WorkingDirectory=/opt/springWeb/var/
ExecStart=/usr/bin/python ${SPRING_BASE}/bin/server.py ${SPRING_IP} ${SPRING_PORT} ${SPRING_UPLOAD} ${SPRING_BASE}${SPRING_WWWSTATIC}

StandardOutput=syslog
StandardError=syslog
ExecStop=/bin/kill -HUP $MAINPID
Type=simple
Restart=always

[Install]
WantedBy=default.target

## Dependencies
* Bokeh 0.12.4
* Flask
* Python 2.7
* EMAN2


