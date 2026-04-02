import keyboard
import cv2
import dlib
from skimage import io
from scipy.spatial import distance
import os
import sys
import requests
import psutil
import win32gui
from datetime import datetime
import threading
import time
import socket

URL = "http://127.0.0.1:8000/"


def get_path(relative_path:str):
    """Получает абсолютный путь к файлу, учитывая режим EXE и разработки"""
    try:
        base_path = sys._MEIPASS # type: ignore
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def upadate_info():
    global sp_anti_app, sp_anti_website, t1
    while t1:
        try:
            sp_anti_app = requests.get(
                URL + f"sp_anti_app/{socket.gethostname()}"
            ).json()
            sp_anti_website = requests.get(
                URL + f"sp_anti_website/{socket.gethostname()}"
            ).json()
            t1 = True
            time.sleep(60)
        except:
            t1 = False


def not_rasp_player(name_game):
    response = requests.post(
                URL + "not_rasp_player",
                json=[name_game,socket.gethostname()],
                headers={"Content-Type": "application/json"},
            )
    

def who_played(name_game:str):
    global facerec, detector
    img = io.imread(get_path("ffff.png"))
    dets = detector(img, 1)
    for k, d in enumerate(dets):
        shape = model(img, d)
    try:
        face1 = facerec.compute_face_descriptor(img, shape)# type: ignore
    except:
        not_rasp_player(name_game)
        return None
    data = requests.get(URL + "rasp_group").json()
    today = datetime.today()
    weekday_num = str(today.weekday())
    current_time = datetime.now().time()
    group_id = get_group_id() 

    if group_id==0:
        not_rasp_player(name_game)
    print(group_id)
    data = requests.get(URL + f"student/{group_id}").json()
    for i in data:
        a = distance.euclidean(face1, i[1])
        if a < 0.6:
            k = i[0]
            d = requests.get(URL + f"who_played/{k}/{name_game}").json()
            return d[0]
    not_rasp_player(name_game)


def close_app():
    found = False
    for proc in psutil.process_iter(["pid", "name"]):
        try:
            for name_app in sp_anti_app:
                if name_app.lower() in proc.info["name"].lower():
                    process = psutil.Process(proc.info["pid"])
                    process.terminate()  # Попытка корректного завершения
                    try:
                        process.wait(timeout=3)
                    except psutil.TimeoutExpired:
                        proc.kill()  # Ждём завершения процесса
                    mes(name_app)
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess) as e:
            print(f"Ошибка при завершении процесса: {e}")
            continue


def get_active_window_title():
    return win32gui.GetWindowText(win32gui.GetForegroundWindow())


def close_website():
    title = get_active_window_title().replace(" ", " ").lower()
    for name_website in sp_anti_website:
        if name_website.lower() in title:
            keyboard.press("ctrl")
            keyboard.press("w")
            keyboard.release("ctrl")
            keyboard.release("w")
            mes(name_website)
            break


def mes(name_game:str):
    ret, img = web_cam.read()
    if not ret:
        return -1
    cv2.imwrite(get_path("ffff.png"), img)
    a = who_played(name_game)


def get_group_id():
    data = requests.get(URL + "rasp_group").json()
    today = datetime.today()
    weekday_num = str(today.weekday())
    current_time = datetime.now().time()
    group_id = 0 
    for i in data:
        try:
            if weekday_num in i[2].keys() and (
                i[2][weekday_num].split("-")[0].split(":")[0]
                < str(current_time).split(":")[0]
                < i[2][weekday_num].split("-")[1].split(":")[0]
                or (
                    i[2][weekday_num].split("-")[0].split(":")[0]
                    == str(current_time).split(":")[0]
                    and i[2][weekday_num].split("-")[0].split(":")[1]
                    <= str(current_time).split(":")[1]
                )
                or (
                    i[2][weekday_num].split("-")[1].split(":")[0]
                    == str(current_time).split(":")[0]
                    and int(i[2][weekday_num].split("-")[0].split(":")[1])
                    <= int(str(current_time).split(":")[1])
                )
            ):
                group_id = i[0]
                break
        except Exception as e:
            print(e)
                
    return group_id


def send_pris():
    ret, img = web_cam.read()
    dets = detector(img, 1)
    for k, d in enumerate(dets):
        shape = model(img, d)
    try:
        face1 = facerec.compute_face_descriptor(img, shape)# type: ignore
    except:
        return True
    data = requests.get(URL + "rasp_group").json()
    today = datetime.today()
    weekday_num = str(today.weekday())
    current_time = datetime.now().time()
    group_id = get_group_id()        
    if group_id==0:
        return True

    data = requests.get(URL + f"student/{group_id}").json()
    for i in data:
        a = distance.euclidean(face1, i[1])
        if a < 0.6:
            mesag = i[0]
            response = requests.post(
                URL + "upload",
                json=mesag,
                headers={"Content-Type": "application/json"},
            )
            return False
    return True


""" Функция для мониторинга экрана (работает в отдельном потоке) """
web_cam = cv2.VideoCapture(0)
model = dlib.shape_predictor(get_path("shape_predictor_68_face_landmarks.dat"))# type: ignore
facerec = dlib.face_recognition_model_v1(get_path("dlib_face_recognition_resnet_model_v1.dat"))# type: ignore
detector = dlib.get_frontal_face_detector()# type: ignore
t = True
t1 = True
sp_anti_app = []
sp_anti_website = []
thr1 = threading.Thread(target=upadate_info)
thr1.start()

while True:
    close_website()
    close_app()
    if t:
        print(1)
        t = send_pris()
    if not t1:
        thr1 = threading.Thread(target=upadate_info)
        thr1.start()
    time.sleep(1)
