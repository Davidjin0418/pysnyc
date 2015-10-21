#!/usr/bin/env python3

#author Bojun Jin
#UPI bjin718
import sys
from os import listdir,chdir,stat,getcwd,makedirs,walk,remove
from os.path import isfile, join,isdir,getmtime,abspath,basename,exists
import hashlib
import time
import datetime
import json
import shutil
from datetime import timezone

def check_num_of_argu(argv):
	if len(argv)==3:
		pass
	else:
		print('wrong number of argv')
		sys.exit(0)


def check_directory(argv):
	if isdir(argv) and exists(argv):
		return True
	else:
		return False


def get_modification_time(f):
	"""ctime() does not refer to creation time on *nix systems, 
	but rather the last time the inode data changed."""
	t = getmtime(f)
	time=datetime.datetime.fromtimestamp(t).replace(tzinfo=timezone.utc).astimezone(tz=None)
	return time.strftime('%Y-%m-%d %H:%M:%S %z')

def get_current_time():
	time=datetime.datetime.now().replace(tzinfo=timezone.utc).astimezone(tz=None)
	return datetime.datetime.strftime(time, '%Y-%m-%d %H:%M:%S %z')


def generate_sha_value(f):
    return hashlib.sha256(open(f, 'rb').read()).hexdigest()
        
def get_subdirectory(directory):
	pass

def generate_Json_for_dir(directory):
	#update digest file in local dir as well as all subdir
	
	onlyfiles = [ f for f in listdir(directory) if isfile(join(directory,f)) and not f.startswith('.')]
	subdirectories=[d for d in listdir(directory) if d not in onlyfiles and not d.startswith('.')]

	if not isfile(abspath(directory)+'/'+'.sync') or (isfile(abspath(directory)+'/'+'.sync') and stat(abspath(directory)+'/'+'.sync').st_size==0):
		# first time creating a digest file or digest is empty
		with open(abspath(directory)+'/'+'.sync','w') as digest_file:
			final=dict()
			for f in onlyfiles:
				modifcation_time=str(get_modification_time(abspath(directory)+'/'+basename(f)))
				digest=generate_sha_value(abspath(directory)+'/'+basename(f))
				value=[[modifcation_time,digest]]
				a_dict={basename(f):value}
				final.update(a_dict)
			json.dump(final,digest_file,indent=4)
	else:
		#not first time,load json first
		with open(abspath(directory)+'/'+'.sync', 'r') as f:
			data=json.load(f)
		with open(abspath(directory)+'/'+'.sync','w') as digest_file:
			for f in onlyfiles:
				 #case: new file,file not change,file updated,file deleted
				modifcation_time=str(get_modification_time(abspath(directory)+'/'+basename(f)))
				digest=generate_sha_value(abspath(directory)+'/'+basename(f))
				value=[[modifcation_time,digest]]
				a_dict={basename(f):value}
				if basename(f) not in data:
					#new file
					data.update(a_dict)
				else:
					old_digest=data[basename(f)][0][1]
					if digest==old_digest:
						#same nothing to update
						pass
					else:
						#update list
						data[basename(f)].insert(0,[modifcation_time,digest])
			for key in data:
				if key not in onlyfiles:
					#deleted
					if not data[key][0][1]=='deleted':
						data[key].insert(0,[get_current_time(),'deleted'])
			json.dump(data,digest_file,indent=4)
			#need to deal with subdirectories
	if len(subdirectories)>0:
		for sub_dir in subdirectories:
			generate_Json_for_dir(directory+'/'+sub_dir)
		    	
				




def sync_between_dir(dir1,dir2):
	dir1_files=[ f for f in listdir(dir1) if isfile(join(dir1,f)) and not f.startswith('.')]
	dir2_files=[ f for f in listdir(dir2) if isfile(join(dir2,f)) and not f.startswith('.')]

	subdirectories1=[d for d in listdir(dir1) if d not in dir1_files and not d.startswith('.')]
	subdirectories2=[d for d in listdir(dir2) if d not in dir2_files and not d.startswith('.')]
	#deal with sub directory
	if not exists(abspath(dir1)+'/'+'.sync'):
		with open(abspath(dir1)+'/'+'.sync','w') as create1:
			json.dump(dict(),create1)
	if not exists(abspath(dir2)+'/'+'.sync'):
		with open(abspath(dir2)+'/'+'.sync','w') as create2:
			json.dump(dict(),create2)

	with open(abspath(dir1)+'/'+'.sync', 'r') as f1_read:
		data1=json.load(f1_read)
	with open(abspath(dir2)+'/'+'.sync','r') as f2_read:
		data2=json.load(f2_read)
	with open(abspath(dir2)+'/'+'.sync','w') as f2_write:
		for f in dir1_files:
			#to be decided ? deal with delete?
			if basename(f) not in data2:
				#new file , update digest and copy the file
				data_to_update={basename(f):data1[basename(f)]}
				data2.update(data_to_update)
				shutil.copy(abspath(dir1)+'/'+basename(f),abspath(dir2))
			else:
				#not a new file,update or do nothing  
				#delete case?
				##########################
				#####DEAL WITH MERGE######
				##########################
				digest1=data1[basename(f)][0][1]
				digest2=data2[basename(f)][0][1]
				if digest2=="deleted":
					#deal with deletion
					delete=True
					for value in data1[basename(f)]:
						if value[1]=="deleted":
							#interesting case has been deleted then recreated,copy 1 to 2 then update 2's sync
							shutil.copy(abspath(dir1)+'/'+basename(f),abspath(dir2))
							value=data1[basename(f)][0]
							data2[basename(f)].insert(0,value)
							delete=False
							break
					if delete:
						#normal case,delete 1's file
						remove(abspath(dir1)+'/'+basename(f))
						data1[basename(f)].insert(0,[get_current_time(),'deleted'])

				else:
					if digest1==digest2:
						#same digest file
						time1= datetime.datetime.strptime(data1[basename(f)][0][0], '%Y-%m-%d %H:%M:%S %z')
						time2=datetime.datetime.strptime(data2[basename(f)][0][0], '%Y-%m-%d %H:%M:%S %z')
						if time1<time2:
							#1 is earlier,copy 1's sync to 2
							value=data1[basename(f)][0]
							data2[basename(f)].insert(0,value)
						elif time1>time2:
							#2 is earlier,copy 2's sync to 1
							value=data2[basename(f)][0]
							data1[basename(f)].insert(0,value)
						else:
							#same nothing to update
							pass
					else:
						#digest1 not equal digest2
						need_to_copy=True
						for value in data2[basename(f)]:
							if digest1==value[1]:
								#file 1 matches a old version in 2,copy 2 to 1 & update .sync
								shutil.copy(abspath(dir2)+'/'+basename(f),abspath(dir1))
								need_to_copy=False
								value=data2[basename(f)][0]
								data1[basename(f)].insert(0,value)
								break
						if need_to_copy:
							for value in data1[basename(f)]:
								if digest2==value[1]:
									#file 2 matches a old version in 1,copy 1 to 2 & update .sync
									shutil.copy(abspath(dir1)+'/'+basename(f),abspath(dir2))
									value=data1[basename(f)][0]
									data2[basename(f)].insert(0,value)
									need_to_copy=False
									break
						if need_to_copy:
							#use the modification time to identify the most recent version
							time1= datetime.datetime.strptime(data1[basename(f)][0][0], '%Y-%m-%d %H:%M:%S %z')
							time2=datetime.datetime.strptime(data2[basename(f)][0][0], '%Y-%m-%d %H:%M:%S %z')
							if time1<time2:
								#2 is most recent copy 2 to 1
								shutil.copy(abspath(dir2)+'/'+basename(f),abspath(dir1))
								value=data2[basename(f)][0]
								data1[basename(f)].insert(0,value)
							elif time1>time2:
								#1 is most recent copy 1 to 2
								value=data1[basename(f)][0]
								data2[basename(f)].insert(0,value)
								shutil.copy(abspath(dir1)+'/'+basename(f),abspath(dir2))
		json.dump(data2,f2_write,indent=4)

	with open(abspath(dir1)+'/'+'.sync', 'w') as f1_write:
		for f in dir2_files:
			#to be decided ? deal with delete?
			if basename(f) not in data1:
				data_to_update={basename(f):data2[basename(f)]}
				data1.update(data_to_update)
				shutil.copy(abspath(dir2)+'/'+basename(f),abspath(dir1))
			else:
				#deal with deletion
				digest1=data1[basename(f)][0][1]
				digest2=data2[basename(f)][0][1]
				if digest1=="deleted":
					#deal with deletion
					delete=True
					for value in data2[basename(f)]:
						if value[1]=="deleted":
							#interesting case has been deleted then recreated,copy 1 to 2 then update 2's sync
							shutil.copy(abspath(dir2)+'/'+basename(f),abspath(dir1))
							value=data2[basename(f)][0]
							data1[basename(f)].insert(0,value)
							delete=False
							break
					if delete:
						#normal case,delete 1's file
						remove(abspath(dir2)+'/'+basename(f))
						with open(abspath(dir2)+'/'+'.sync','w') as f2_write:
							data2[basename(f)].insert(0,[get_current_time(),'deleted'])
							json.dump(data2,f2_write,indent=4)



		json.dump(data1,f1_write,indent=4)
	if len(subdirectories1)>0:
		for sub_dir in subdirectories1:
			if not exists(dir2+'/'+sub_dir):
				makedirs(dir2+'/'+sub_dir)

			sync_between_dir(dir1+'/'+sub_dir,dir2+'/'+sub_dir)

	if len(subdirectories2)>0:
		for sub_dir in subdirectories2:
			if not exists(dir1+'/'+sub_dir):
				makedirs(dir1+'/'+sub_dir)
			sync_between_dir(dir2+'/'+sub_dir,dir1+'/'+sub_dir)






		


		

			
	

def main(argv):
	check_num_of_argu(argv)
	if check_directory(argv[1]) and check_directory(argv[2]):
		generate_Json_for_dir(argv[1])
		generate_Json_for_dir(argv[2])
		#perform sync
		sync_between_dir(argv[1],argv[2])
	elif check_directory(argv[1]) and not check_directory(argv[2]):
		#1 is dir 2 is not
		#create dir for 2
		makedirs(argv[2])
		generate_Json_for_dir(argv[1])
		generate_Json_for_dir(argv[2])
		#perform sync
		sync_between_dir(argv[1],argv[2])
		
	elif not check_directory(argv[1]) and check_directory(argv[2]):
		#1 is not dir 2 is
		#create dir for 1
		makedirs(argv[1])
		generate_Json_for_dir(argv[1])
		generate_Json_for_dir(argv[2])
		#perform sync
		sync_between_dir(argv[1],argv[2])
	else:
		#neither are dir,
		print('Error:neither of them are directories')
		sys.exit(0)
	
	
if __name__ == '__main__':
	main(sys.argv)