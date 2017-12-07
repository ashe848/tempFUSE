# tempFUSE
User space file system in python.

The file system starts with some real files from the source directory. 

The directory being worked with is the mount directory - this is where temporary files will be seen.

So the file system has two classes of files which are in the mount directory. One consists of real files from the source directory and the other of files which only exist in memory.

Any changes which happen to files in the mount directory which have been created only in memory (including creating or deleting files, or writing to files) only happen in the mount directory. However if the file was initially in the source directory then changes get passed back to that directory.

To run, start the user space file system in a terminal:

python tempFuse.py source mount

This terminal will show output that describes calls made to the file system and output gotten back in debug form.

Now work with the files in mount directory in a separate terminal using the usual commands.
