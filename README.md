1. modify /etc/rc.local to include the line

```
sudo nano /etc/xdg/lxsession/LXDE-pi/autostart 

#add the following at the end of this file
chromium-browser http://127.0.0.1:9000 --start-fullscreen &
```

2. cd into the clock_server dir and run this command to copy the service into its appropraite lcation

```
sudo cp school_classes.service /etc/systemd/system/school_classes.service
```

3. Test with

```
sudo systemctl start school_classes.service
sudo systemctl stop school_classes.service
```

4. enable with
```
sudo systemctl enable school_classes.service 
```

5. modify classes by editing the file classes.txt. Format is 

```
start time, end time, class name
```