import asyncio
import mythic
import pexpect
import time
import re
import os
import threading
import json
import ast
import math
import hashlib
from datetime import date, datetime
from mythic import mythic_rest
from termcolor import colored
import socket
import subprocess
from multiprocessing import Process
import shutil



running_callbacks = []

async def scripting():
    # sample login
    pwd = "bubiman10"
    cmd = "../mythic-cli config get MYTHIC_ADMIN_USER"
    with_password = "echo {} | sudo -S {}".format(pwd, cmd)
    p = subprocess.Popen(with_password, shell=True, stdout=subprocess.PIPE)
    out, err = p.communicate()
    admin_user = out.decode().split("=")[1].strip()

    cmd = "../mythic-cli config get MYTHIC_ADMIN_PASSWORD"
    with_password = "echo {} | sudo -S {}".format(pwd, cmd)
    p = subprocess.Popen(with_password, shell=True, stdout=subprocess.PIPE)
    out, err = p.communicate()
    admin_password = out.decode().split("=")[1].strip()

    print(admin_user + "\n" + admin_password)

    global mythic_instance
    mythic_instance = mythic_rest.Mythic(
        username=admin_user,
        password=admin_password,
        server_ip=socket.gethostbyname(socket.gethostname()),
        server_port="7443",
        ssl=True,
        global_timeout=-1,
    )
    print("[+] Logging into Mythic")
    await mythic_instance.login()
    await mythic_instance.set_or_create_apitoken()
    print("[+] Listening for new responses")
    await mythic_instance.listen_for_new_responses(handle_resp)
    print("[+] Listening for new tasks")
    await mythic_instance.listen_for_new_tasks(handle_task)


    file_name = "topology/"
    if os.path.exists(file_name):
        shutil.rmtree(file_name)
    
    
async def handle_resp(token, message):

    # # just print out the entire message so you can see what you get
    # await mythic_rest.json_print(message)
    # # just print the name of the command that resulted in this response
    # print(message.task.command.cmd)
    # # just print the actual response data that came back
    # print(message.response)

    global running_callbacks

    if message.task.command.cmd == "tunnel":
        print("TUNNEL REQUEST")
        tunnel(message)

    if message.task.command.cmd == "trace":
        trace(message)
        
    if message.task.command.cmd == "code":
        await code(message)

        
async def handle_task(mythic, message):
    #print(message)
    # await mythic_rest.json_print(message)

    if message.command.cmd == "parallel" and message.status == "completed":
        await parallel(message)


def virtual_topology(public_ip):
    print("[+] Creating virtual topology of {}".format(public_ip))

    try:
        file_name = "topology/hosts/" + public_ip
        hosts_file = open(file_name)
    except:
        print(colored("Unable to open " + file_name, "red"))
    hosts = hosts_file.read().split()
    topo = {}
    x = [0]
    done = set()
    traces = {}

    for h1 in hosts:
        for h2 in hosts:
            if h1 != h2:
                traces[h1+h2] = []
                if get_answer_from_dest(public_ip, h1, h2):
                    add_routers(topo, h1, h2, x, alias, traces, 100, False)
                




def get_answer_from_dest(public_ip, host1, host2):
    count = len(open("traceroutes/" + public_ip + "/" + host1 + "-" + host2).readlines())
    if count <= 30:
        return True
    else:
        return False

def add_all_routers(topo, public_ip, host1, host2, blocking_case):
    f = open("topology/traceroutes/{}/{}-{}".format(public_ip, host1, host2, "r"))
    lines = f.readlines()
    scr = None
    dst = None
    for i in range(1, len(lines)-1):
        src = get_router(lines[i])
        dst = get_router(lines[i+1])
    

    


def get_router(trace):
    i = 1
    while  i <= 3 and trace[i]=='*':
        i=i+1
    if i > 3:
        return 'A'
    else:
        return trace.split()[1]




def add_routers(topo, host1, host2, x, alias, traces, max_iter, blocking_case):
    with open("traceroute/"+host1+host2) as trace:
        lines = trace.readlines()        
        src = None
        dst = None
        if max_iter == 100:
            num_lines = len(lines)
            max_iter = num_lines -2 #skip first and last line (don't consider hosts)
        if max_iter == 1: # Only add the router to the virtual topo and return it
            dst = find_router(lines[1].split(), alias)
            if dst not in topo:
                topo[dst] = ('R', set())
                if not blocking_case:
                    traces[host1+host2].append(dst)
        for i in range(1, max_iter):
            src = find_router(lines[i].split(), alias)
            dst = find_router(lines[i+1].split(), alias)
            (src,dst) = add_link(topo,(src,dst) ,x ,i)
            if not blocking_case:
                if i==1:
                    traces[host1+host2].append(src)
                traces[host1+host2].append(dst)
    return dst   





def nmap(args, address):
    print("[+] Starting Nmap scan")
    nmap = pexpect.spawnu("bash")
    nmap.logfile = open("./nmap_" + address + ".log", "w")
    nmap.sendline("nmap " + args)
    nmap.expect("scanned")
    print("[+] Nmap Done")


def tunnel(message):
    if "keylog" in message.response:
        print("WE DONT HAVE THE PASSWORD")

    else:
        # params = message.response.split(";")
        # address = params[0]
        # psw = params[1]
        # args = params[2]

        # print("SSH: " + address)
        # print("Local Sudo Password: " + local_psw)
        # print("Remote Sudo Password: " + psw)
        # print(args)

        # psw = "bubiman10"

        # child = pexpect.spawnu("bash")
        # child.logfile = open("./log.log", "w")
        # child.expect(".*@")
        # child.sendline("sshuttle -r " + address + " 0/0")
        # child.expect(".*assword")
        # child.sendline(local_psw)
        # child.expect(".*onnected")

        # p = pexpect.spawnu("bash")
        # p.logfile_read = open("./log2.log", "w")
        # p.sendline("curl ipv4.icanhazip.com")
        # time.sleep(1)
        # p.expect(".*\.")

        # address_file = open("./log2.log", "r")
        # text = str(address_file.readlines())
        # pattern = re.compile(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})')
        # ip = pattern.findall(text)[0]

        # os.remove("./log.log")
        # os.remove("./log2.log")

        # thread = threading.Thread(target=nmap, args=(args, address.split("@")[1]), daemon=True)
        # thread.start()


        params = message.response.split(";")
        user = params[0].split("@")[0].strip()
        address = params[0].split("@")[1].strip()
        psw = params[1]
        command = params[2]

        print("Running {}".format(command))

        def sshuttle():
            cmd = "sshuttle -r {}@{} --dns -x {} 0/0".format(user, address, address)

            child = pexpect.spawnu("bash")
            child.logfile = open("./bash.log", "w")
            child.expect(".*@")
            child.sendline(cmd)
            child.expect(".*assword")
            child.sendline("bubiman10")
            child.expect(".*onnected")

        process = Process(target=sshuttle)
        process.start()

        p = subprocess.Popen(command, shell=True, stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        stdout, stderr= p.communicate()

        now = datetime.now()


        file_name = "./tunnel_log_[{}].log".format(str(now.strftime("%d-%m-%Y-%H:%M:%S")))
        try:
            f = open(file_name, "w+")
            f.write(stdout.decode())
        except Exception as e:
            print(e)


        process.kill()




def trace(message):
    print("[+] Creating config file")
    config = open(os.path.expanduser("~") + "/.ssh/config", "w")

    params = message.response.split(";")

    list = message.response.split(" --> ")
    char = "A"
    for node in list:
        hostname = node.split(";")[0].split("@")[1]
        user = node.split(";")[0].split("@")[0]
        config.write("Host " + char + "\n")
        config.write("\tHostname " + hostname + "\n")
        config.write("\tUser " + user + "\n")
        if char != "A":
            config.write("\tProxyCommand ssh -W %h:%p " + chr(ord(char) - 1) + "\n")
        char = chr(ord(char) +1)


async def code(message):
    # await mythic_rest.json_print(message)
    if "Password found" in message.response:
        print(colored("\t - Password found, stopping agents", "green"))
        for c in running_callbacks:
            if c.active and c.id != message.task.callback.id:
                task = mythic_rest.Task(callback=c, command="stop", params="parallel")
                submit = await mythic_instance.create_task(task, return_on="submitted")


    call = mythic_rest.Callback(id=message.task.callback.id)
    response_callback = await mythic_instance.get_one_callback(call)
    public_ip = response_callback.response.ip.split("/")[0]
    private_ip = response_callback.response.ip.split("/")[1]

    if "traceroute" in message.response:

        file_name = "topology/hosts/" + public_ip
        try:
            os.makedirs(os.path.dirname(file_name), exist_ok=True)            
        except Exception as e:
            print(e)
        f = open(file_name, "a+")
        f.write(private_ip + " ")
        f.flush()
        f.close()
       
        file_name = "topology/distances/" + public_ip + "/" + private_ip
        try:
            os.makedirs(os.path.dirname(file_name), exist_ok=True)            
        except Exception as e:
            print(e)

        f = open(file_name, "w+")
        sub = message.response
        while sub.find("Distance to ") != -1:
            dest_ip_start = sub.find("Distance to ") + 12
            dest_ip_end = sub.find(" = ")
            dest_ip = sub[dest_ip_start:dest_ip_end]
            hop_start = dest_ip_end + 3
            hop_end = hop_start + 10
            hop = sub[hop_start:hop_end].strip().split("\n")[0]
            f.write(dest_ip + " " + str(hop))
            sub = sub[dest_ip_end:]
        f.flush()
        f.close()

        sub = message.response
        while sub.find("traceroute to ") != -1:
            dest_ip_start = sub.find("traceroute to ") + 14
            dest_ip_end = sub.find("hops")
            dest_ip = sub[dest_ip_start : dest_ip_end].strip().split(" ")[0]
            file_name = "topology/traceroutes/" + response_callback.response.ip.split("/")[0] + "/" + response_callback.response.ip.split("/")[1] + "-" + dest_ip
            try:
                os.makedirs(os.path.dirname(file_name), exist_ok=True)            
            except Exception as e:
                print(e)

            f = open(file_name, "w+")
            next_trace = sub[dest_ip_start:].find("traceroute to ")
            if next_trace != -1:
                f.write(sub[dest_ip_start - 14 : next_trace])
            else:
                f.write(sub[dest_ip_start - 14:])
        
            sub = sub[dest_ip_start:]
        
    else:
        file_name = "parallel_" + message.task.original_params.split(";;;")[2]
        try:
            f = open(file_name, "a+")
            f.write("Callback: {}, IP: {} \n{}\n".format(message.task.callback.id, response_callback.response.ip, message.response))
            f.flush()
            f.close()
        except:
            print(colored("Unable to write on {}".format(file_name), "red"))


    for c in running_callbacks:
        if c.ip == response_callback.response.ip:
            running_callbacks.remove(c)

    if running_callbacks == []:
        print("[+] Gathering phase finished, creating virtual topology...")
        virtual_topology(public_ip)





async def parallel(message):

    global workers
    global distributed_parameters
    distributed_parameters = []        

    parameters = message.original_params.split()
    print(colored("\nNew task: {}".format(parameters), "blue"))

    additional=""

    if len(parameters) > 2:
        try:
            additional = ast.literal_eval(parameters[2])
        except:
            additional = parameters[2]
    
    resp = await mythic_instance.get_all_callbacks()

    total_code = ""
    code_path = "../Payload_Types/kayn/shared/" + parameters[0]

    try:
        workers = int(parameters[1])
    except Exception as e:
        print(colored("\t Failed to get workers number - {}".format(e), "red"))
        raise Exception("\t - Failed to get workers number - {}".format(e))
        return

    if workers == 0:
        for c in resp.response:
            if c.active:
                workers += 1
        print(colored("\t - Workers automatically set to {}".format(workers), "green"))

    try:
        total_code += open(code_path, "r").read() + "\n"
        
    except Exception as e:
        print(colored("\t - Failed to open {}".format(parameters[0]), "red"))
        return

    index = total_code.index("def worker(")
    worker_code = total_code[index:]
    preliminary_code = total_code[:index]


    exec(str(preliminary_code))

    try:
        if "async def initialize" in preliminary_code:
            if additional != "":
                await eval("initialize(additional)")
            else:
                await eval("initialize()")
        elif additional != "":
            eval("initialize(additional)")
        else:
            eval("initialize()")
    except Exception as e:
        print(e)


    now = datetime.now()
    i=0
    global running_callbacks
    while i < workers:
        for c in resp.response:
            if c.active:
                task = mythic_rest.Task(callback=c, command="code", params="{};;;{};;;{}".format(worker_code, distributed_parameters[i], now))
                submit = await mythic_instance.create_task(task, return_on="submitted")
                if c not in running_callbacks:
                    running_callbacks.append(c)
                i += 1
            if i == workers:
                break

async def main():
    global local_psw
    # local_psw = input("Insert local sudo password: ")
    local_psw = "bubiman10"
    await scripting()
    try:
        while True:
            pending = asyncio.all_tasks()
            plist = []
            for p in pending:
                if p._coro.__name__ != "main" and p._state == "PENDING":
                    plist.append(p)
            if len(plist) == 0:
                exit(0)
            else:
                await asyncio.gather(*plist)
    except KeyboardInterrupt:
        pending = asyncio.all_tasks()
        for t in pending:
            t.cancel()

loop = asyncio.get_event_loop()
loop.run_until_complete(main())