import http.server
import socketserver
import threading
import json
from urllib.parse import unquote


import pygame
from datetime import datetime, timedelta
pygame.init()
pygame.mixer.music.load("flight.mp3")

class school_class:
    def __init__(self,start_hour,start_minute,end_hour,end_minute,class_name):
        self.start = datetime(1,1,1,start_hour,start_minute,0,0)
        self.end = datetime(1,1,1,end_hour,end_minute,0,0)
        self.playing = False
        self.in_session = False
        self.name = class_name
        
    def __gt__(self, other):
        return self.name > other.name or self.start > other.start or self.end > other.end
    
    def __lt__(self, other):
        return self.name < other.name or self.start < other.start or self.end < other.end
        
    def __eq__(self, other):
        return self.name == other.name or self.start == other.start or self.end == other.end

    def toJson(self,is_current):
        start_correct_date = datetime.now()
        start_correct_date = start_correct_date.replace(hour=self.start.hour,minute=self.start.minute, second=self.start.second)
        
        end_correct_date = datetime.now()
        end_correct_date = end_correct_date.replace(hour=self.end.hour,minute=self.end.minute,second=self.end.second)
        
        if is_current:
            seconds = (end_correct_date - datetime.now()).seconds
        else:
            seconds = (start_correct_date - datetime.now()).seconds
        minutes = seconds/60
        seconds = seconds % 60
        import math
        if len(str(seconds)) == 1:
            seconds = "0" + str(seconds)
        else:
            seconds = str(seconds)
        time_left = f"{math.floor(minutes)}:{seconds}"
            
        return {"name":self.name, "start":str(start_correct_date),"end":str(end_correct_date),"time_left":time_left}
    
    def is_one_minute_away(self):
        compare_date = datetime.now() + timedelta(minutes=1)
        if(self.playing):
            return False
        if(compare_date.time() > self.start.time() and datetime.now().time() < self.start.time()):
            return True
        else:
            return False
    
    def is_currently_in_class(self):
        return (datetime.now().time() > self.start.time() and datetime.now().time() < self.end.time())
    
    def start_class(self):
        pygame.mixer.music.pause()
        self.in_session = True
        self.playing = False
    
    def end_class(self):
        self.in_session = False
    
    def play(self):
        self.playing = True
        pygame.mixer.music.rewind()
        pygame.mixer.music.play()


#State machi#ne that  controls what the 
#web app shows and when plays music before class
current_class = None
next_class = None

acknowledge_button_pushed = False
def class_loop():
    global current_class
    global next_class
    global classes
    incoming_class = None
    import time
    waiting_minute = False
    while not cancelled:
        try:
            #setup state for next class info
            temp_next_class = None
            for class_in_list in classes:
                if temp_next_class is None:
                    if class_in_list.start.time() > datetime.now().time() :
                        temp_next_class = class_in_list
                else:
                    if temp_next_class.start.time() >  class_in_list.start.time() :
                        temp_next_class = class_in_list
                if temp_next_class is not None:
                    next_class = temp_next_class
                else:
                    next_class = None

            #setup state for current class, play song when its one minute away
            if(current_class is None and incoming_class is None):
                for class_in_list in classes:
                    if(class_in_list.is_one_minute_away()):
                        class_in_list.play()
                        incoming_class = class_in_list
                        print("class is about to start")
                    elif(class_in_list.is_currently_in_class()):
                        incoming_class = class_in_list #will update on the next loop but wont play song so we dont start playing music during consecutive classes
            elif (incoming_class is not None):
                if(incoming_class.is_currently_in_class()):
                    print("class is starting")
                    incoming_class.start_class()
                    current_class = incoming_class
                    incoming_class = None
            else:
                if(not current_class.is_currently_in_class()):
                    print("class is ending")
                    current_class.end_class()
                    current_class = None    
            time.sleep(1)
        except:
            print("error occured in loop")

#the list of classes
def get_classes():
    file = open("classes.txt")
    data = file.read()
    file.close()

    global classes
    global next_class
    global current_class
    classes = []
    print("getting classes")
    for line in data.split("\n"):
        parts = line.split(",")
        start = parts[0].split(":")
        end = parts[1].split(":")
        classes.append(school_class(int(start[0]), int(start[1]), int(end[0]), int(end[1]), parts[2] ))
    next_class = None
    current_class = None
    print(data)

get_classes()


cancelled = False

thread = threading.Thread(target=class_loop)
thread.start()
    

def datetime_converter(o):
    if isinstance(o, datetime.datetime):
        return o.__str__()

class MyHttpRequestHandler(http.server.SimpleHTTPRequestHandler):
    def set_headers_json(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        
    def set_headers_text(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        
    def do_HEAD(self):
        self._set_headers()
    
    def do_GET(self):
        global current_class, next_class, thread, cancelled
        #print(self.path)
        if self.path == '/':
            self.path = 'index.html'
            return http.server.SimpleHTTPRequestHandler.do_GET(self)
        elif self.path == "/class_state":
            self.set_headers_json()
            #print("im here")
            self.wfile.write(json.dumps({"current_class": current_class.toJson(True) if current_class is not None else None, "next_class":next_class.toJson(False) if next_class is not None else None }).encode())
            #self.send_response(200)
        elif self.path == "/classes.html":
            return http.server.SimpleHTTPRequestHandler.do_GET(self)
        elif self.path == "/classes":
            self.set_headers_text()
            temp_file = open("classes.txt")
            data = temp_file.read()
            temp_file.close()
            self.wfile.write(data.encode())
        elif self.path.startswith("/classes_update"):
            path = unquote(self.path)
            classes_data = path.split("data=")[1]
            temp_file = open("classes.txt","w")
            temp_file.write(classes_data)
            temp_file.close()
            get_classes()
            self.set_headers_json()
            self.wfile.write(json.dumps({"status": "saved"}).encode())      
            

def run_server():
    handler_object = MyHttpRequestHandler
    PORT = 9000
    my_server = socketserver.TCPServer(("", PORT), handler_object)
    # Star the server
    my_server.serve_forever()
    
thread_server = threading.Thread(target=run_server)
thread_server.start()