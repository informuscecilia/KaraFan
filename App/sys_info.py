#!python3.10

#   MIT License - Copyright (c) 2023 - Captain FLAM
#
#   https://github.com/Captain-FLAM/KaraFan

import os, sys, subprocess, json, gc, torch
import regex as re

#  Shows the tensors that are still in use by the Notebook.
#  If this list is (mostly) empty, then you have freed all the memory you can free.

def pretty_size(size):
	"""Pretty prints a torch.Size object"""
	assert(isinstance(size, torch.Size))
	return " x ".join(map(str, size))

def dump_tensors(gpu_only=True):
	"""Prints a list of the Tensors being tracked by the garbage collector."""
	total_size = 0
	for obj in gc.get_objects():
		try:
			if torch.is_tensor(obj):
				if not gpu_only or obj.is_cuda:
					total_size += obj.numel()
					
					print("%s:%s%s %s" % (
						type(obj).__name__, 
						" GPU" if obj.is_cuda else "",
						" pinned" if obj.is_pinned else "",
						pretty_size(obj.size())))
					
			elif hasattr(obj, "data") and torch.is_tensor(obj.data):
				if not gpu_only or obj.is_cuda:
					total_size += obj.data.numel()
					
					print("%s → %s:%s%s%s%s %s" % (
						type(obj).__name__, 
						type(obj.data).__name__, 
						" GPU" if obj.is_cuda else "",
						" pinned" if obj.data.is_pinned else "",
						" grad" if obj.requires_grad else "", 
						" volatile" if obj.volatile else "",
						pretty_size(obj.data.size())))
		
		except Exception as e:  pass

	print("Total size:", total_size)


def Get(font_size):

	import platform, psutil

	system = platform.system()

	html  = '<pre style="font: bold '+ font_size +' monospace; line-height: 1.4">'
	html += "****  System Informations  ****<br><br>"

	# Get the total virtual memory size (in bytes)
	total_virtual_memory = psutil.virtual_memory().total
	unit_index = 0
	units = ['B', 'KB', 'MB', 'GB', 'TB']

	# Convert size into larger units until size is less than 1024
	while total_virtual_memory >= 1024:
		total_virtual_memory /= 1024
		unit_index += 1

	html += "Python : "+ re.sub(r'\(.*?\)\s*', '', sys.version) +"<br>"
	html += f"OS : {system} { platform.release() }<br>"
	html += f"RAM : {total_virtual_memory:.2f} {units[unit_index]}<br>"
	html += f"Current directory : { os.getcwd() }<br><br>"

	html += "****    CPU Informations    ****<br><br>"
	match system:
		case 'Windows':  # use 'wmic'
			try:
				cpu_info = subprocess.check_output(['wmic', 'cpu', 'get', 'Caption,MaxClockSpeed,NumberOfCores,NumberOfLogicalProcessors', '/FORMAT:CSV']).decode('utf-8')
				cpu_info = cpu_info.split('\n')[-2].strip()  # catch the last line
				# Split values
				cpu_info = cpu_info.split(',')
				html += f"CPU : {cpu_info[1]}<br>"
				html += f"Cores : {cpu_info[3]}<br>"
				html += f"Threads : {cpu_info[4]}<br>"
				html += f"MaxClock Speed : {cpu_info[2]} MHz"
			except FileNotFoundError:
				html += "--> Can't get CPU infos : 'wmic' tool is not available on this platform."

		case 'Linux':  # use 'lscpu'
			try:
				cpu_info = subprocess.check_output(['lscpu', '-J']).decode('utf-8')
				cpu_info = json.loads(cpu_info)
				if 'lscpu' in cpu_info:
					sockets = cores = threads = 1
					for item in cpu_info["lscpu"]:
						if 'field' in item and 'data' in item:
							data = item['data']
							match item['field']:
								case "Architecture:":		html += f"Arch : {data}<br>"
								case "Model name:":			html += f"CPU : {data}<br>"
								case "CPU max MHz:":		html += f"MaxClock Speed : {int(data)} MHz<br>"
								case "Socket(s):":			sockets = int(data)
								case "Core(s) per socket:":	cores   = int(data)
								case "Thread(s) per core:":	threads = int(data)
					
					html += f"Cores : {cores * sockets}<br>"
					html += f"Threads : {threads * cores * sockets}"

			except FileNotFoundError:
				html += "--> Can't get CPU infos : 'lscpu' tool is not available on this platform."

		case 'Darwin':  # For macOS, use 'sysctl'
			try:
				## TODO : decode CPU infos on macOS
				html += "CPU : " + subprocess.check_output(['sysctl', 'machdep.cpu']).decode('utf-8')
			except FileNotFoundError:
				html += "--> Can't get CPU infos : 'sysctl' tool is not available on this platform."

		case _:
			# For other platforms, display a generic message
			html += "--> CPU informations are not available for this platform."

	html += "<br><br>****    GPU Informations    ****<br><br>"
	try:
		# Nvidia details information
		gpu_info = subprocess.check_output('nvidia-smi').decode('utf-8')
		
		html += '<div style="line-height: 1; ">'+ gpu_info +'</div><br>'

		if gpu_info.find('failed') >= 0:
			html += "<b>GPU runtime is disabled. You can only use your CPU with available RAM.</b>"
		elif gpu_info.find('Tesla T4') >= 0:
			html += "You got a Tesla T4 GPU. (speeds are around  10-25 iterations/sec)"
		elif gpu_info.find('Tesla P4') >= 0:
			html += "You got a Tesla P4 GPU. (speeds are around  8-22 iterations/sec)"
		elif gpu_info.find('Tesla K80') >= 0:
			html += "You got a Tesla K80 GPU. (This is the most common and slowest gpu, speeds are around 2-10 iterations/sec)"
		elif gpu_info.find('Tesla P100') >= 0:
			html += "You got a Tesla P100 GPU. (This is the FASTEST gpu, speeds are around  15-42 iterations/sec)"
	
	except FileNotFoundError:
		html += "<b>--> Can't get GPU infos : 'nvidia-smi' tool is not available on this platform.</b>"

	html += "</pre>"
	
	return html
