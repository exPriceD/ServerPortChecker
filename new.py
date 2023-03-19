import csv
import socket
import time
from pythonping import ping
from contextlib import closing
import datetime
from typing import Union, List
from random import randint

class CsvFile:
    def __init__(self, path_to_csv: str):
        self.path_to_csv = path_to_csv

    def read(self) -> List:
        with open(self.path_to_csv, encoding='utf-8') as r_file:
            row_list = []
            file_reader = csv.reader(r_file, delimiter=";")
            row_number = 0
            for row in file_reader:
                if row_number != 0:
                    row_list.append([row[0], row[1]])
                row_number += 1
            return row_list


class Dialog:
    def start(self) -> tuple:
        save_path = input(
            "Enter the path to save. If you don't want to save the result to a file, leave the field empty\n")
        interval = int(input("Enter the interval between requests in seconds (ex.: 120) - "))
        print(f"The interval is set to {interval} seconds")
        return save_path, interval

    def error_output(self, error: str, row: int, hostname: str, port: str) -> None:
        answer = "ROW"
        if error == "PORT":
            answer = "PORT"
            print(f'Input error! Invalid PORT. Row {row + 1} (HOST={hostname} PORT={port})')
        elif error == "HOST":
            answer = "ROW"
            print(f'Input error! Not HOST in row. Row {row + 1} (HOST={hostname} PORT={port})')
        incorrect_answer = True
        while incorrect_answer:
            dialog = input(f"Skip this {answer} or exit? Write [Y/N]  :  ")
            if dialog == 'y' or dialog == 'Y':
                incorrect_answer = False
                continue
            elif dialog == 'n' or dialog == 'N':
                exit()
            else:
                print('Invalid symbol')


class RequestsListFilter:
    def __init__(self, requests_list: List):
        self.requests_list = requests_list

    def processing(self) -> List:
        processed_list = self.requests_list.copy()
        for request in processed_list:
            request[1].replace(" ", "")
            request[1] = request[1].split(',')
        for request in processed_list:
            if request[0] == '':
                Dialog().error_output(error="HOST",
                                      row=processed_list.index(request),
                                      hostname=request[0],
                                      port=request[1])
                del processed_list[processed_list.index(request)]
                continue
            for port_index in range(len(request[1])):
                if not request[1][port_index].isdigit() and request[1][port_index].strip() != '':
                    Dialog().error_output(error="PORT",
                                          row=self.requests_list.index(request),
                                          hostname=request[0],
                                          port=request[1][port_index])
                    del request[1][port_index]
                elif request[1][port_index] == '':
                    del request[1][port_index]
        return processed_list


class UserRequests:
    def __init__(self, hostname: str):
        self.hostname = hostname

    def get_port_status(self, port) -> List:
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
            request_start = time.time()
            s.settimeout(10)
            try:
                if s.connect_ex((self.hostname, int(port))) == 0:
                    return [round(((time.time() - request_start) * 1000), 2), "Opened"]
                else:
                    return [round(((time.time() - request_start) * 1000), 2), "Unknown"]
            except Exception: #????????
                pass
            return [round(((time.time() - request_start) * 1000), 2), "Unknown"]

    def get_ip_list(self) -> Union[list, str]:
        try:
            ip_list = list({addr[-1][0] for addr in socket.getaddrinfo(self.hostname, 0, 0, 0, 0)})
            if "::1" in ip_list:
                ip_list.remove("::1")
            return ip_list
        except Exception: #????????
            pass
        return "?"

    def get_ping(self) -> list:
        request_start = time.time()
        try:
            if ping(self.hostname):
                return [round(((time.time() - request_start) * 1000), 2), "Ip is available"]
            else:
                return [round(((time.time() - request_start) * 1000), 2), "???"]
        except Exception: #?????????
            pass
        return [round(((time.time() - request_start) * 1000), 2), "???"]


class Results:
    def __init__(self, request: List):
        self.hostname = request[0]
        self.ports = request[1]

    def result_processing(self) -> List:
        result = []
        request = UserRequests(hostname=self.hostname)
        hostname = self.hostname if not is_ip(address=self.hostname) else "???"
        ip_list = request.get_ip_list()
        if len(self.ports) > 0:
            for port in self.ports:
                for ip in ip_list:
                    date = get_time()
                    response = request.get_port_status(port=port)
                    rtt_max_ms = str(response[0]) if response[0] != 0.0 else "???"   #Вынести 149-151 в функцию? +date
                    port_check_state = str(response[1])
                    ip_address = ip if ip != '?' else '???'
                    port = str(port)
                    result.append([date, hostname, ip_address, rtt_max_ms, port, port_check_state])
        else:
            for ip in ip_list:
                date = get_time()
                response = request.get_ping()
                rtt_max_ms = str(response[0]) if response[0] != 0.0 else "???"
                port_check_state = str(response[1])
                ip_address = ip if ip != '?' else '???'
                port = "-1"
                result.append([date, hostname, ip_address, rtt_max_ms, port, port_check_state])

        return result


class Connection:
    def internet(self) -> bool:
        try:
            host = socket.gethostbyname("1.1.1.1")
            s = socket.create_connection((host, 80), 2)
            s.close()
            return True
        except Exception: #????????
            pass
        return False


class Output:
    def __init__(self, path: str):
        self.path = path

    def show_title(self, response_data_list: list) -> None:
        hostname = response_data_list[0][1]
        ip_list, ports = [], []
        for response in response_data_list:
            ip_list.append(response[2])
            if response[4] != '-1':
                ports.append(response[4])
        ip_list = list(set(ip_list))
        ports = list(set(ports))
        output = f"['{hostname}',{ip_list},{ports}]"
        if self.path == "":
            print(output)
        else:
            print(f"\t{output}")
            output_in_file(path=self.path, output=output)

    def show_result(self, response: list) -> None:
        output = response[0]
        output += ' | ' + response[1]
        output += ' | ' + response[2]
        output += ' | ' + response[3] + ' ms'
        output += ' | ' + response[4]
        output += ' | ' + response[5]
        if self.path == "":
            print(f"\t{output}")
        else:
            print(f"\t{output}")
            output_in_file(path=self.path, output=output)

    def lost_connection(self) -> None:
        problem_time = get_time()
        output = f"{problem_time} | There is no internet connection"
        if self.path == "":
            print(f"\t{output}")
        else:
            print(f"\t{output}")
            output_in_file(path=self.path, output=output)


def get_time() -> str:
    offset = datetime.timezone(datetime.timedelta(hours=3))
    date = datetime.datetime.now(offset).strftime("%Y-%m-%d %H:%M:%S.%f")
    return date


def is_ip(address: str) -> bool:
    return not address.split('.')[-1].isalpha()


def output_in_file(path: str, output: str) -> None:
    try:
        with open(f"{path}/result.txt", "a") as file:
            file.write(f"\t{output}\n")
    except NotADirectoryError:
        print("Directory Error")
        exit()


def main() -> None:
    dialog = Dialog()
    save_path, interval = dialog.start()
    csv = CsvFile(path_to_csv="example.csv")
    raw_list = csv.read()
    preparing = RequestsListFilter(requests_list=raw_list)
    processed_list = preparing.processing()
    last_responses = {}
    out = Output(path=save_path)
    connection_checker = Connection()
    for user_query in processed_list:
        result = Results(request=user_query)
        if connection_checker.internet():
            response_data_list = result.result_processing()
            out.show_title(response_data_list=response_data_list)
            for response in response_data_list:
                out.show_result(response=response)
                last_responses[response[2]] = response[5]
        else:
            out.lost_connection()
        print()
        print()
    while True:
        out = Output(path=save_path)
        connection_checker = Connection()
        for user_query in processed_list:
            result = Results(request=user_query)
            if connection_checker.internet():
                response_data_list = result.result_processing()
                for response in response_data_list:
                    if last_responses[response[2]] != response[5]:
                        out.show_result(response=response)
                        last_responses[response[2]] = response[5]
        time.sleep(interval)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("EXIT")
        exit()
