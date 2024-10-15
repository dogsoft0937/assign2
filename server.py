import os
import socket
from datetime import datetime

class SocketServer:
    def __init__(self):
        self.bufsize = 1024
        self.DIR_PATH = './request'
        self.IMAGE_DIR_PATH = './images'
        self.RESPONSE_PATH = './response.bin'
        self.createDir(self.DIR_PATH)
        self.createDir(self.IMAGE_DIR_PATH)
        self.loadResponse()

    def createDir(self, path):
        try:
            if not os.path.exists(path):
                os.makedirs(path)
        except OSError:
            print(f"Error creating directory: {path}")

    def loadResponse(self):
        try:
            with open(self.RESPONSE_PATH, 'rb') as file:
                self.RESPONSE = file.read()
                print(f"response.bin 파일이 성공적으로 로드되었습니다.")
        except FileNotFoundError:
            print(f"{self.RESPONSE_PATH} 파일이 없습니다.")
            self.RESPONSE = b"HTTP/1.1 500 Internal Server Error\r\nContent-Type: text/plain\r\n\r\nError: response file not found"

    def saveData(self, data, dir_path, file_prefix, extension):
        now = datetime.now()
        filename = now.strftime(f"{file_prefix}-%Y-%m-%d-%H-%M-%S{extension}")
        filepath = os.path.join(dir_path, filename)
        with open(filepath, 'wb') as file:
            file.write(data)
        print(f"데이터가 {filepath}에 저장되었습니다.")
        return filepath

    def extractImage(self, response_data):
        """multipart/form-data에서 이미지 데이터를 추출하는 함수"""
        try:
            # Content-Type 헤더에서 boundary 값 추출
            boundary_start = response_data.find(b"boundary=") + len(b"boundary=")
            boundary_end = response_data.find(b"\r\n", boundary_start)
            boundary = response_data[boundary_start:boundary_end].strip()

            # boundary 기준으로 파트를 나눔
            parts = response_data.split(b"--" + boundary)

            for part in parts:
                # 이미지 데이터가 있는 파트를 찾음
                if b"Content-Type: image" in part:
                    # 이미지 데이터 추출 (헤더와 바디를 나누는 \r\n\r\n 이후가 이미지)
                    image_start = part.find(b"\r\n\r\n") + 4
                    image_end = part.rfind(b"\r\n")  # 이미지 끝부분 추정
                    image_data = part[image_start:image_end]

                    # 이미지 저장
                    self.saveData(image_data, self.IMAGE_DIR_PATH, "image", ".jpg")
                    print("이미지 데이터가 성공적으로 추출 및 저장되었습니다.")
                    return image_data

            print("이미지 데이터가 발견되지 않았습니다.")
            return None

        except Exception as e:
            print(f"이미지 추출 중 오류 발생: {e}")
            return None

    def run(self, ip, port):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((ip, port))
        self.socket.listen(10)
        print(f"서버가 {ip}:{port} 에서 시작되었습니다. 연결을 기다리는 중...")

        try:
            while True:
                client_sock, req_addr = self.socket.accept()
                print(f"클라이언트 {req_addr} 연결됨.")
                client_sock.settimeout(5.0)

                response_data = b""
                try:
                    while True:
                        packet = client_sock.recv(self.bufsize)
                        if not packet:
                            break
                        response_data += packet
                except socket.timeout:
                    print("데이터 수신 시간 초과")

                # 요청 데이터 전체를 bin 파일로 저장
                self.saveData(response_data, self.DIR_PATH, "request", ".bin")

                # 이미지 데이터 추출 및 저장
                self.extractImage(response_data)

                client_sock.sendall(self.RESPONSE)
                client_sock.close()

        except KeyboardInterrupt:
            print("Server is shutting down")
        except Exception as e:
            print(f"An error occurred: {e}")
        finally:
            self.socket.close()

if __name__ == '__main__':
    server = SocketServer()
    server.run("127.0.0.1", 8000)
