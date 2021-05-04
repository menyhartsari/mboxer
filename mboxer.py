#!/usr/bin/env python3
import socket
import os
import sys
import signal
import hashlib
import re


def dopln(d):
	hlavicka=""
	obsah=""
	d=d.strip()
	if not d.isascii():
		return (hlavicka,obsah)
	if d.isspace():
		return (hlavicka,obsah)
	if d.find(":") != -1:
		d=d.split(":")
		if len(d)!=2:
			return (hlavicka,obsah)
		if d[0].find("/") == -1:
			hlavicka=d[0]
			obsah=d[1]
		else:
			return (hlavicka,obsah)
	else:
		return (hlavicka,obsah)
	return (hlavicka,obsah)
	
def kontrola(hlav_zoz):
	status_num=100
	status_comment="OK"
	for s in hlav_zoz:
		if s=="":
			status_num,status_comment=(200, 'Bad request')
		if hlav_zoz[s]=="":
			status_num,status_comment=(200, 'Bad request')
		if status_num==200:
			return (status_num,status_comment)
	return status_num,status_comment


def m_write(hlav_zoz,fu):
	status_num=100
	status_comment="OK"
	odpoved_hlav=""
	odpoved_obsah=""
	try:
		dlzka=int(hlav_zoz["Content-length"])
		obsah=fu.read(dlzka)
		nazov = hashlib.md5(obsah).hexdigest()
		with open(f'{hlav_zoz["Mailbox"]}/{nazov}',"wb") as fr:
			fr.write(obsah)
	except FileNotFoundError:
		status_num,status_comment=(203,'No such mailbox')
	except KeyError:
		status_num,status_comment=(200,'Bad request')
	except ValueError:
		status_num,status_comment=(200,'Bad request')
	except:
		status_num,status_comment=(200,'Bad request')
	return (status_num,status_comment,odpoved_hlav,odpoved_obsah)


def m_read(hlav_zoz):
	status_num=100
	status_comment="OK"
	odpoved_hlav=""
	odpoved_obsah=""
	try:
		with open(f'{hlav_zoz["Mailbox"]}/{hlav_zoz["Message"]}','rb') as fr:
			odpoved_obsah=fr.read()
			dlzka=len(odpoved_obsah)
			odpoved_hlav=(f'Content-length: {dlzka}\n')
	except FileNotFoundError:
		status_num,status_comment=(201,'No such message')
	except OSError:
		status_num,status_comment=(202,'Read error')
	except KeyError:
		status_num,status_comment=(200,'Bad request')
	except:
		status_num,status_comment=(200,'Bad request')
	return (status_num,status_comment,odpoved_hlav,odpoved_obsah)


def m_ls(hlav_zoz):
	status_num=100
	status_comment="OK"
	odpoved_hlav=""
	odpoved_obsah=""
	try:
		spravy = os.listdir(hlav_zoz["Mailbox"])
		dlzka = len(spravy)
		odpoved_hlav=(f'Number-of-messages: {dlzka}\n')
		odpoved_obsah = "\n".join(spravy) + "\n"
	except FileNotFoundError:
		status_num,status_comment=(203,'No such mailbox')
	except KeyError:
		status_num,status_comment=(200,'Bad request')
	except:
		status_num,status_comment=(200,'Bad request')
	return status_num,status_comment,odpoved_hlav,odpoved_obsah



s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1)
s.bind(('',9999))
signal.signal(signal.SIGCHLD,signal.SIG_IGN)
s.listen(5)
while True:
	connected_socket,address=s.accept()
	print(f'spojenie z {address}')
	pid_chld=os.fork()
	if pid_chld==0:
		s.close()
		f=connected_socket.makefile(mode='rwb')
		while True:
			hlavicky_zoz={}
			odpoved_hlav=""
			odpoved_obsah=""
			method=f.readline().decode('utf-8')
			method=method.strip()
			d=f.readline().decode('utf-8')
			while d != "\n":
				hlavicka,obsah=dopln(d)
				d=f.readline().decode('utf-8')
				hlavicky_zoz[hlavicka]=obsah
			status_num,status_comment=kontrola(hlavicky_zoz)
			if status_num==100:
				if method=="WRITE":
					status_num,status_comment,odpoved_hlav,odpoved_obsah=m_write(hlavicky_zoz,f)
				elif method=="READ":
					status_num,status_comment,odpoved_hlav,odpoved_obsah=m_read(hlavicky_zoz)
				elif method=="LS":
					status_num,status_comment,odpoved_hlav,odpoved_obsah=m_ls(hlavicky_zoz)
				else:
					status_num,status_comment=(204,'Unknown method')
			f.write(f'{status_num} {status_comment}\n'.encode('utf-8'))
			f.write(odpoved_hlav.encode('utf-8'))
			f.write('\n'.encode('utf-8'))
			if type(odpoved_obsah)==bytes:
				f.write(odpoved_obsah)
			else:
				f.write(odpoved_obsah.encode('utf-8'))
			f.flush()
			if status_num==204:
				print(f'{address} uzavrel spojenie')
				sys.exit(0)
		print(f'{address} uzavrel spojenie')
		sys.exit(0)
	else:
		connected_socket.close()
