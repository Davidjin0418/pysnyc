# pysnyc
a synchronisation program to sync between two directories, using Python3.4

#How to use it
Use the command "python3 sync.py name_of_dir1 name_of_dir2" to sync between two directories

#How it works
Note: everything mentioned below applied to subdirectories as well.
It first generate a digest file for each directory, the digest file is in Json format. Basically the digest contains the 
digest value ( SHA256 value of the file content) and the last modification time.
Example format: 
{
  "file1_1.txt": [
    [
      "2015-08-26 12:03:44 +1200",
      "d6072668c069d40c27c3f982789b32e33f23575316ebbbc11359c49929ac8adc"
    ],
    [
      "2015-08-26 12:03:42 +1200",
      "a2ebea1d55e6059dfb7b8e8354e0233d501da9d968ad3686c49d6a443b9520a8"
    ]
  ],
  "file1_2.txt": [
    [
      "2015-08-26 12:03:42 +1200",
      "c62b8de531b861db068eac1129c2e3105ab337b225339420d2627c123c7eae04"
    ]
  ],
  "file2_1.txt": [
    [
      "2015-08-26 12:03:42 +1200",
      "3032e7474e22dd6f35c618045299165b0b42a9852576b7df52c1b22e3255b112"
    ]
] }
The sync process is based on this digest file
