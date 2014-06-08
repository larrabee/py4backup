#!/usr/bin/python3
# -*- coding: UTF-8 -*-
#Requres python3
__author__ = 'larrabee'
#version 1.1.1
import re
import os
import datetime
import select
import sys
import socket
import smtplib
import math
import configparser
import binascii
import hashlib
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email.mime.text import MIMEText
from email import encoders


class Logger():
    log_buffer = ''

    def __init__(self, logpath='', login='', passwd='', server='', port=25, tls=True, sendto='',
                 log_with_time=True, attach=''):
        self.attach = attach
        self.log_with_time = log_with_time
        self.sendto = sendto
        self.tls = tls
        self.port = port
        self.server = server
        self.passwd = passwd
        self.login = login
        self.logpath = logpath

    def add(self, *message, mtype=0):
        str_message = ''
        if mtype == 0:
            smtype = 'INFO     :'
        elif mtype == 1:
            smtype = 'WARN     :'
        elif mtype == 2:
            smtype = 'ERROR    :'
        elif mtype == 3:
            smtype = 'J_ERROR  :'
        elif mtype == -3:
            smtype = 'J_ERROR  :'
        elif mtype == 4:
            smtype = 'F_ERROR  :'
        elif mtype == -4:
            smtype = 'F_ERROR  :'
        else:
            smtype = 'UNK_CODE:'
        for element in message:
            str_message += str(element)
        if self.log_with_time:
            time = datetime.datetime.now()
            self.log_buffer = self.log_buffer + smtype + time.strftime('%Y-%m-%d %H:%M:%S') + ': ' + str(
                str_message) + '\n'
        else:
            self.log_buffer = self.log_buffer + smtype + str(str_message) + '\n'
        if mtype == 3:
            raise JobError
        elif mtype == 4:
            raise FatalError

    def write(self):
        try:
            logdircheck = re.match(r'/([\w*\d*\-*\.*,*\\\\*]+/)*', self.logpath)
            if not os.path.isdir(logdircheck.group()):
                try:
                    os.makedirs(logdircheck.group())
                except:
                    Logger.add(self, 'Cannot create log dir in', logdircheck, mtype=2)
                else:
                    Logger.add(self, 'Successfully create dir: ', logdircheck.group())
        except AttributeError:
            Logger.add(self, 'Cannot parse log path:', self.logpath)
        except:
            Logger.add(self, 'Unknown error occurred while check log path var', mtype=2)
        try:
            logfile = open(self.logpath, 'a')
            logfile.write(self.log_buffer)
        except:
            Logger.add(self, 'Cannot write to file: ', self.logpath)
        else:
            logfile.close()

    def get_log(self, ask=False):
        str_message = ''
        if ask:
            try:
                print('Print saved log to terminal? y/n')
                stdinselect, _, _ = select.select([sys.stdin], [], [], 10)
                if stdinselect:
                    stdin = sys.stdin.readline()
                else:
                    stdin = None
                if ('y' in stdin) or ('Y' in stdin) or ('yes' in stdin):
                    try:
                        for element in self.log_buffer:
                            str_message += element
                        return str_message
                    except:
                        print('Cannot print log. Unknown error')
                else:
                    return ''
            except KeyboardInterrupt:
                return
            except UnboundLocalError:
                return
            except:
                return
        else:
            try:
                for element in self.log_buffer:
                    str_message += element
                return str_message
            except:
                print('Cannot return log. Unknown error')

    def send_email(self):
        basename = os.path.basename(self.attach)

        # Compose message
        msg = MIMEMultipart()
        msg['From'] = 'Py4Backup@' + socket.getfqdn()
        msg['To'] = self.sendto
        if self.attach != '':
            try:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(open(self.attach, 'rb').read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', 'attachment; filename="%s"' % basename)
                msg.attach(part)
            except FileNotFoundError:
                Logger.add(self, 'Attached file not found, path: ', self.attach, mtype=2)
            except:
                Logger.add(self, 'Unknown error while create attachment for email', mtype=2)

        msg['Subject'] = 'Backup completed on host ' + socket.getfqdn()
        msg.attach(MIMEText(Logger.get_log(self)))

        # Send mail
        try:
            for element in self.sendto.split():
                smtp = smtplib.SMTP(self.server, self.port)
                if self.tls:
                    smtp.starttls()
                smtp.login(self.login, self.passwd)
                smtp.sendmail(self.login, element, msg.as_string())
                smtp.quit()
        except smtplib.SMTPAuthenticationError:
            Logger.add(self, 'Cannot send email. Auth error', mtype=2)
        except TimeoutError:
            Logger.add(self, 'Cannot send email. Cannot connect to server, timeout error', mtype=2)
        except socket.gaierror:
            Logger.add(self, 'Cannot send email. Cannot resolve server name', mtype=2)
        except smtplib.SMTPException:
            Logger.add(self, 'Cannot send email. Maybe server no support SMTP AUTH. You can try use TLS AUTH', mtype=2)
        except:
            Logger.add(self, 'Cannot send email. Unknown error', mtype=2)
        else:
            Logger.add(self, 'Mail report successfully sended')


class Counts():
    starttime = None
    stoptime = None
    __resulttime = None
    totalsize = 0

    def start_timer(self):
        self.starttime = datetime.datetime.now()

    def stop_timer(self):
        if self.starttime is not None:
            self.stoptime = datetime.datetime.now()
            self.__resulttime = self.stoptime - self.starttime
            self.__resulttime = self.__resulttime.total_seconds()
        else:
            raise ValueError

    def get_timer_delta(self, format=True):
        if format:
            if self.__resulttime is not None:
                return self.__resulttime // 60, ' min ', int(math.fmod(self.__resulttime, 60)), ' sec'
            elif (self.__resulttime is None) and (self.starttime is not None):
                timepoint = datetime.datetime.now() - self.starttime
                timepoint = int(timepoint.total_seconds())
                return timepoint // 60,  min, int(math.fmod(timepoint, 60)), ' sec'
        else:
            if self.__resulttime is not None:
                return self.__resulttime
            elif (self.__resulttime is None) and (self.starttime is not None):
                timepoint = datetime.datetime.now() - self.starttime
                timepoint = int(timepoint.total_seconds())
                return timepoint

    def get_size(self, path):
        if os.path.isdir(path):
            for (joinpath, dirs, files) in os.walk(path, followlinks=False):
                for file in files:
                    try:
                        filename = os.path.join(joinpath, file, )
                        self.totalsize += int(os.path.getsize(filename))
                    except:
                        pass
        else:
            try:
                self.totalsize += int(os.path.getsize(path))
            except:
                pass

    def return_total_size(self, format=True):
        if format:
            if self.totalsize >= 1024 * 1024 * 1024 * 1024:
                return round(self.totalsize / (1024 * 1024 * 1024 * 1024), 2), 'Tb'
            elif self.totalsize >= 1024 * 1024 * 1024:
                return round(self.totalsize / (1024 * 1024 * 1024), 2), 'Gb'
            elif self.totalsize >= 1024 * 1024:
                return round(self.totalsize / (1024 * 1024), 2), 'Mb'
            elif self.totalsize >= 1024:
                return round(self.totalsize / 1024, 2), 'Kb'
            else:
                return self.totalsize, 'bytes'
        else:
            return self.totalsize

    def get_speed(self, format=True):
        if format:
            if (self.__resulttime is not None) and (self.__resulttime != 0):
                return round(self.totalsize / (1024 * 1024 * self.__resulttime), 2), 'Mb/s'
            elif (self.__resulttime is None) and (self.starttime is not None):
                timepoint = datetime.datetime.now() - self.starttime
                timepoint = int(timepoint.total_seconds())
                return round(self.totalsize / (1024 * 1024 * timepoint), 2), 'Mb/s'
        else:
            if (self.__resulttime is not None) and (self.__resulttime != 0):
                return round(self.totalsize / self.__resulttime, 0)
            elif (self.__resulttime is None) and (self.starttime is not None):
                timepoint = datetime.datetime.now() - self.starttime
                timepoint = int(timepoint.total_seconds())
                return round(self.totalsize / timepoint, 0)

    def reset_total_size(self):
        self.totalsize = 0


class MainConfigParser():
    def __init__(self, config_path,):
        self.__config_path = config_path
        #Default values
        self.send_mail_reports = True
        self.login = ''
        self.passwd = ''
        self.sendto = ''
        self.server = ''
        self.port = 25
        self.tls = True
        self.bs = '4M'
        self.ddd_bs = 4096
        self.ddd_hash = None
        self.logpath = '/var/log/py4backup.log'
        self.logging = True
        self.log_with_time = True
        self.temp_snap_name = str('py4backup_temp_snap')
        self.host_desc = None
        self.pathenv = None
        self.read_values = []
        MainConfigParser.__parse_config(self)

    def __parse_config(self):
        config = configparser.ConfigParser()
        config.read(self.__config_path)
        try:
            self.send_mail_reports = config.getboolean('MAIL', 'send_mail_reports')
            self.read_values.append('MAIL:send_mail_reports')
        except:
            pass
        try:
            self.login = str(config['MAIL']['login'])
            self.read_values.append('MAIL:login')
        except:
            pass
        try:
            self.passwd = str(config['MAIL']['passwd'])
            self.read_values.append('MAIL:passwd')
        except:
            pass
        try:
            self.sendto = str(config['MAIL']['sendto'])
            self.read_values.append('MAIL:sendto')
        except:
            pass
        try:
            self.server = str(config['MAIL']['server'])
            self.read_values.append('MAIL:server')
        except:
            pass
        try:
            self.port = str(config['MAIL']['port'])
            self.read_values.append('MAIL:port')
        except:
            pass
        try:
            self.tls = config.getboolean('MAIL', 'tls')
            self.read_values.append('MAIL:tls')
        except:
            pass
        try:
            self.bs = str(config['DD']['bs'])
            self.read_values.append('DD:bs')
        except:
            pass
        try:
            self.ddd_bs = config.getint('DD', 'ddd_bs')
            self.read_values.append('DD:ddd_bs')
        except:
            pass
        try:
            self.ddd_hash = str(config['DD']['ddd_hash'])
            self.read_values.append('DD:ddd_hash')
        except:
            pass
        try:
            self.logpath = str(config['LOGGING']['logpath'])
            self.read_values.append('LOGGING:logpath')
        except:
            pass
        try:
            self.logging = config.getboolean('LOGGING', 'enable_logging')
            self.read_values.append('LOGGING:enable_logging')
        except:
            pass
        try:
            self.log_with_time = config.getboolean('LOGGING', 'log_with_time')
            self.read_values.append('LOGGING:log_with_time')
        except:
            pass
        try:
            self.temp_snap_name = str(config['OTHER']['temp_snap_name'])
            self.read_values.append('OTHER:temp_snap_name')
        except:
            pass
        try:
            self.host_desc = str(config['OTHER']['host_desc'])
            self.read_values.append('OTHER:host_desc')
        except:
            pass
        try:
            if (str(config['OTHER']['pathenv']) is not None) and (str(config['OTHER']['pathenv']) is not '') and \
                    (str(config['OTHER']['pathenv']) is not ' '):
                self.pathenv = str(config['OTHER']['pathenv'])
                self.read_values.append('OTHER:pathenv')
        except:
            pass


class JobParser():
    def __init__(self, job_config_path,):
        self.__job_config_path = job_config_path
        #Default values
        self.type = None
        self.sopath = None
        self.snpath = None
        self.dpath = None
        self.exclude = ''
        self.include = ''
        self.dayexp = None
        self.prescript = None
        self.postscript = None

    def get_values(self, job_name):
        config = configparser.ConfigParser()
        config.read(self.__job_config_path)
        try:
            self.sopath = str(config[job_name]['sopath'])
        except:
            self.sopath = None
        try:
            self.snpath = str(config[job_name]['snpath'])
        except:
            self.snpath = None
        try:
            self.dpath = str(config[job_name]['dpath'])
        except:
            self.dpath = None
        try:
            self.exclude = config[job_name]['exclude']
        except:
            self.exclude = ''
        try:
            self.include = config[job_name]['include']
        except:
            self.include = ''
        try:
            self.dayexp = int(config[job_name]['dayexp'])
        except:
            self.dayexp = None
        try:
            self.prescript = config[job_name]['prescript']
        except:
            self.prescript = None
        try:
            self.postscript = config[job_name]['postscript']
        except:
            self.postscript = None
        try:
            if str(config[job_name]['type']) == 'btrfs-full':
                self.type = 'btrfs-full'
            elif str(config[job_name]['type']) == 'btrfs-diff':
                self.type = 'btrfs-diff'
            elif str(config[job_name]['type']) == 'btrfs-snap':
                self.type = 'btrfs-snap'
            elif str(config[job_name]['type']) == 'file-full':
                self.type = 'file-full'
            elif str(config[job_name]['type']) == 'file-diff':
                self.type = 'file-diff'
            elif str(config[job_name]['type']) == 'lvm-full':
                self.type = 'lvm-full'
            elif str(config[job_name]['type']) == 'lvm-diff':
                self.type = 'lvm-diff'
            elif str(config[job_name]['type']) == 'custom':
                self.type = 'custom'
            else:
                self.type = None
        except:
            self.type = None

    def check_job_name(self, job_name):
        config = configparser.ConfigParser()
        config.read(self.__job_config_path)
        if job_name not in config.sections():
            return False
        else:
            return True

    def jobs_list(self):
        config = configparser.ConfigParser()
        config.read(self.__job_config_path)
        return config.sections()


class ReadFile():
    def __init__(self, filename, diff_map=False, block_size=4096):
        self.chunksize = block_size
        self.diff = diff_map
        self.filename = filename
        if diff_map:
            self.file = open(self.filename, "r")
            self.data = self.__read_diff()
        else:
            self.file = open(self.filename, "rb")
            self.data = self.__read_full()

    i = 0

    def next(self, without_formatting=False):
        if self.diff:
            try:
                element = next(self.data)
            except StopIteration:
                element = None
                checksumm = None
                control = None
            else:
                control = str(element.split(sep=':')[0])
                checksumm = str(element.split(sep=':')[1])
            if without_formatting:
                return element
            else:
                return control, checksumm
        else:
            try:
                element = next(self.data)
            except StopIteration:
                element = None
            return element

    def __read_full(self):
        while True:
            chunk = self.file.read(self.chunksize)
            if chunk:
                yield chunk
            else:
                break

    def __read_diff(self):
        while True:
            chunk = self.file.readline()
            if chunk:
                yield chunk
            else:
                break

    def close(self):
        self.file.close()


class WriteFile():
    def __init__(self, filename, diff_map=False):
        self.filename = filename
        self.diff = diff_map
        if diff_map:
            self.file = open(self.filename, "a", encoding='ASCII')
        else:
            self.file = open(self.filename, "ab")

    def write(self, data=None, control='', checksumm='', custom=None):
        if self.diff:
            if custom is None:
                self.file.write(str(control) + ':' + str(checksumm) + '\n')
            else:
                self.file.write(str(custom) + '\n')
        else:
            self.file.write(data)

    def close(self):
        self.file.close()


class JobError(Exception):
    def __init__(self, message=''):
        self.message = message

    def __str__(self):
        return self.message


class FatalError(Exception):
    def __init__(self, message=''):
        self.message = message

    def __str__(self):
        return self.message


def create_diff(full_backup, current_backup, result, blocksize=4096, hash_alg=None):
    read_full = ReadFile(full_backup, block_size=int(blocksize))
    read_diff = ReadFile(current_backup, block_size=int(blocksize))
    write_diff = WriteFile(result + '.dd')
    write_diff_map = WriteFile(result + '.ddm', diff_map=True)
    write_diff_map.write(
        custom=str(full_backup) + ':' + str(blocksize) + ':' + str(hash_alg))
    total_blocks = 1
    changed_blocks = 0
    while True:
        full_data = read_full.next()
        diff_data = read_diff.next()
        if diff_data is None:
            write_diff_map.write(control=str(0))
            break
        if full_data != diff_data:
            if hash_alg == 'md5':
                write_diff_map.write(control=str(1), checksumm=hashlib.md5(diff_data).hexdigest())
            elif hash_alg == 'crc32':
                write_diff_map.write(control=str(1), checksumm=binascii.crc32(diff_data))
            else:
                write_diff_map.write(control=str(1))
            write_diff.write(diff_data)
            changed_blocks += 1
        else:
            if hash_alg == 'md5':
                write_diff_map.write(control=str(2), checksumm=hashlib.md5(full_data).hexdigest())
            elif hash_alg == 'crc32':
                write_diff_map.write(control=str(2), checksumm=binascii.crc32(full_data))
            else:
                write_diff_map.write(control=str(2))
        total_blocks += 1
    read_full.close()
    read_diff.close()
    write_diff.close()
    write_diff_map.close()
    print('Total read blocks: ', total_blocks)
    print('Changed blocks: ', changed_blocks)


def restore(diff_file, result, full_backup=None, blocksize=None, hash_alg=None):
    read_diff_map = ReadFile(diff_file + '.ddm', diff_map=True)
    control_string = read_diff_map.next(without_formatting=True)
    #Read values from .ddm file
    if full_backup is None:
        full_backup = control_string.split(sep=':')[0]
    if blocksize is None:
        blocksize = int(control_string.split(sep=':')[1])
    if hash_alg is None:
        hash_alg = control_string.split(sep=':')[2]
    print('Full backup:', full_backup)
    print('bs:', blocksize, '\nHash algorithm:', hash_alg, end='')
    read_diff = ReadFile(diff_file + '.dd', block_size=int(blocksize))
    read_full = ReadFile(full_backup, block_size=int(blocksize))
    write_result = WriteFile(result)
    corrupted_blocks = []
    i = 1
    while True:
        control_symbol, block_hash = read_diff_map.next()
        full_data = read_full.next()
        if control_symbol == '0':
            break
        elif control_symbol == '1':
            diff_data = read_diff.next()
            write_result.write(diff_data)
            if 'md5' in hash_alg:
                if hashlib.md5(diff_data).hexdigest() not in block_hash:
                    corrupted_blocks.append('diff' + str(i))
            elif 'crc32' in hash_alg:
                if str(binascii.crc32(diff_data)) not in str(block_hash):
                    corrupted_blocks.append('diff' + str(i))
        elif control_symbol == '2':
            write_result.write(full_data)
            if 'md5' in hash_alg:
                if hashlib.md5(full_data).hexdigest() not in block_hash:
                    corrupted_blocks.append('full' + str(i))
            elif 'crc32' in hash_alg:
                if str(binascii.crc32(full_data)) not in str(block_hash):
                    corrupted_blocks.append('full' + str(i))
        i += 1
    read_full.close()
    read_diff.close()
    write_result.close()
    read_diff_map.close()
    print('Corrupted blocks:', corrupted_blocks)


def date(time=False):
    if time:
        date_with_time = datetime.datetime.now()
        return date_with_time.strftime('%Y-%m-%d %H:%M:%S')
    else:
        return datetime.date.today()
