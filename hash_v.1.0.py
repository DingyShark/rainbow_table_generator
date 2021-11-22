#!/usr/bin/env python3
import sys
from argparse import ArgumentParser
import hashlib
import os.path
import time
from multiprocessing import Process, current_process, Queue


# Several hash types(other existing hash types can be added)
def hash_function(hash_type, object):
    hashed_file = {
        'sha256': hashlib.sha256(object).hexdigest(),
        'sha512': hashlib.sha512(object).hexdigest(),
        'md5': hashlib.md5(object).hexdigest()
    }
    if hash_type.lower() in hashed_file.keys():
        return hashed_file[hash_type.lower()]
    else:
        print('[!]  Wrong or non existing hash type')
        sys.exit(1)


# Get the CheckSum of the whole file
def hash_of_file(hash_type, path):
    with open(path, 'rb') as file:
        print('[+]  Hash of file:\n'+hash_function(hash_type, file.read()))


# Hashed passwords list generator
def read_file_with_passwds(start_index, end_index, queue, hash_type, input_path):
    print('[+]  Process: '+current_process().name+' Started')
    hash = []
    # Open file with passwords in plain text and read lines
    with open(input_path, 'r') as input_file:
        passwds = input_file.read().splitlines()
        # Making pair of Password:Hash(exmpl. qwerty:65e84be3...)
        for word in range(start_index, end_index):
            hash.append(passwds[word] + ':' + hash_function(hash_type, passwds[word].encode()) + '\n')
    # To read the file correctly while processing put our passwd:hash pair to queue
    queue.put(hash)
    print('[+]  Process: '+current_process().name + ' Finished')


# After creating list of passwd:hash pair write it in output file
def write_hashes_to_file(hash_list, output_path):
    with open(output_path, 'a') as output_file:
        for word in hash_list:
            output_file.write(word)


# Main function to create and start multiple processors to generate rainbow table
def processing_rainbow_generator(hash_type, input_path, output_path, count):
    # Check if file exists before writing in
    if os.path.exists(output_path):
        print('[!]  Output file cannot be used because it already exists')
        sys.exit(1)
    else:
        # Read the whole file to detect number of passwords
        with open(input_path, 'r') as file:
            file_len = len(file.readlines())

        # Arguments to get number of passwords for each process
        # For example, number of process: 5, number of passwords: 1000
        # 1000/5=200, 200 passwords for each process
        start_index, end_index = 0, 0

        # List of process
        procs = []
        q = Queue()

        # Creating number(count) of processes
        for i in range(count):
            end_index += file_len / count
            p = Process(target=read_file_with_passwds, args=(int(start_index), int(end_index), q, hash_type, input_path))
            procs.append(p)
            start_index += file_len / count

        # Starting processes
        for i in range(count):
            procs[i].start()

        # Writing passwd:hash pair to output file
        for i in range(count):
            # Get and write the value in queue
            write_hashes_to_file(q.get(), output_path)

        # Waiting for process to finish
        for i in range(count):
            procs[i].join()

        print('[+]  Rainbow table generated successfully')


if __name__ == '__main__':
    # Available arguments(in cmd type -h for help)
    parser = ArgumentParser()
    parser.add_argument('-s', '--hash', help="sha256/md5/sha512", default='', required=True)
    parser.add_argument('-w', '--word', help="Random string to get hash", default='')
    parser.add_argument('-f', '--file', help="/home/kali/somefile", default='')
    parser.add_argument('-i', '--input', help="Rainbow table generator input file: /home/kali/passwords.txt", default='')
    parser.add_argument('-o', '--output', help="Rainbow table generator output file: /home/kali/rainbow.txt(default rainbow_table.txt)", default='rainbow_table.txt')
    parser.add_argument('-p', '--procs', help="Rainbow table generator: Number of used processes(default 5)", type=int, default=5)
    args = parser.parse_args()

    # Hash of simple string
    if args.word is not '':
        print('[+]  Hash of word:\n'+hash_function(args.hash, args.word.encode()))
    # Hash of file
    elif args.file is not '':
        try:
            hash_of_file(args.hash, args.file)
        except FileNotFoundError:
            print('[!]  Not existing file or path')
    # Creating rainbow table(passwd:hash pair), options output and procs have default values
    elif args.input is not '' and args.output is not '':
        try:
            # Starting timer
            start = time.time()
            processing_rainbow_generator(args.hash, args.input, args.output, args.procs)
            stop = time.time()
            print('Time used: ', stop - start)
        except FileNotFoundError:
            print('[!]  Not existing file or path')
    else:
        print('[!]  No word, file or input file were given')
        sys.exit(1)

