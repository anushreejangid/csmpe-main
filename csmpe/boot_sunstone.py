#!/usr/bin/python
import pexpect
import os
import pdb
import time
import re
class BootSunstone(object):
    def __init__(self):
        self.server_name = ""
        self.server_user = ""
        self.server_pass = ""
        self.image_path  = ""
        self.user_dir    = ""

    def ssh_command (self, user, host, password):

        """This runs a command on the remote host."""
        print "INFO: Logging into", host

        ssh_newkey = 'Are you sure you want to continue connecting'
        child = pexpect.spawn('ssh -l %s %s'%(user, host))
        child.logfile = open("/tmp/mylog", "w")
        child.delaybeforesend = 1
        #child.interact()
        i = child.expect([pexpect.TIMEOUT, ssh_newkey, 'password: '])
        child.logfile_read = open("/tmp/simlaunch.log", "w")
        if i == 0: # Timeout
            print('ERROR!')
            print('SSH could not login. Here is what SSH said:')
            print(child.before, child.after)
            return None
        if i == 1: # SSH does not have the public key. Just accept it.
            child.sendline ('yes')
            child.expect ('password: ')
            i = child.expect([pexpect.TIMEOUT, 'password: '])
            if i == 0: # Timeout
                print('ERROR!')
                print('SSH could not login. Here is what SSH said:')
                print(child.before, child.after)
                return None
        child.sendline(password)
        print(self.user_dir)
        print("INFO: Removing old directories")
        cmd = 'rm -rf %s' % (self.user_dir)
        child.sendline(cmd)
        child.expect('#')
        print("INFO: Creating relevant directories")
        cmd = 'mkdir %s' % (self.user_dir)
        child.sendline(cmd)
        child.expect('#')
        cmd = 'cd %s' % (self.user_dir)
        child.sendline(cmd)
        child.expect('#')
        return child

    def launch_sim(self,child):
        print("INFO: Creating environment")
        cmd = 'source /auto/edatools/oicad/tools/vxr2_user/alpha/setup.sh'
        child.sendline(cmd)
        child.expect('INFO')
        print("INFO: Cleaning old sessions")
        child.sendline('sim end')
        child.expect('#')
        child.sendline('sim clean')
        child.expect('#')
        print("INFO: Creating sim-config ")
        child.sendline('sim xrv9k')
        child.expect('xml')
        cmd = "sed -i -e \'s@PATH_TO_IMAGE@"+ self.user_dir + '/xrv9k-mini-x.iso' + "@g\' sim-config.xml"
        #pdb.set_trace()
        child.sendline(cmd)
        child.expect('#')
        pattern = 'Bridge name="virbr0"'
        cmd = "sed '/%s/{n;d;}' sim-config.xml | tac | sed '/%s/{n;d;}' | tac > sim-config.xml_new" %(pattern, pattern)
        child.sendline(cmd)
        child.expect('#')
        cmd = 'unalias cp'
        child.sendline(cmd)
        child.expect('#')
        cmd = 'cp sim-config.xml_new sim-config.xml'
        child.sendline(cmd)
        child.expect('#')
        print("INFO: Launching sim")
        cmd = "sim -n"
        child.sendline(cmd)
        child.expect('INFO')
        print("INFO: Waiting for sim to get ready")
        time.sleep(500)
        cmd = "cat %s/p0gen0pc0/PortVector.txt | grep \'Submit\|serial0\'" %(self.user_dir)
        child.flush()
        child.sendline(cmd)
        child.expect('#')
        output = child.before
        ip_pat = re.compile("HostSubmit (\d+.\d+.\d*.\d*)")
        if ip_pat.search(output):
            ip = ip_pat.search(output).group(1)
        else:
            print(output)
            exit(-1)
        port_pat = re.compile("serial0 (\d+)")
        if port_pat.search(output):
            port = port_pat.search(output).group(1)
        else:
            print(output)
            exit(-1)
        return ip,port

    def copy_to_server(self, bootInfo):
        self.server_name = bootInfo['machine']
        self.server_user = bootInfo['username']
        self.server_pass = bootInfo['password']
        self.image_path  = bootInfo['image_path']
        self.user_dir    = bootInfo['user_dir']
        child = self.ssh_command (self.server_user, self.server_name, self.server_pass)
        child.expect('#')
        try:
            print("INFO:Copying image to remote server")
            command = "scp %s %s@%s:%s" % (self.image_path, self.server_user, self.server_name, self.user_dir)
            #make sure in the above command that username and hostname are according to your server
            ch = pexpect.spawn(command)
            #child.log_file = open("log.txt",'w')
            #child.interact()
            i = ch.expect([".* password:", pexpect.EOF], timeout= 300)
            print(i)
            if i==0: # send password
                    ch.sendline(self.server_pass)
                    ch.expect(pexpect.EOF, timeout= 500)
            elif i==1:
                    print "Got the key or connection timeout"
                    pass

        except Exception as e:
            print "ERROR! Something went wrong"
            print e
        return child

    def connect_telnet(self, ip, port):
        print("INFO: Setting up username password ")
        tn = telnetlib.Telnet(ip, port, 5)
        tn.write("\r\n")
        tn.write('root' + "\r\n")
        tn.write('lab' + "\r\n")
        tn.write('lab' + "\r\n")
        tn.close
        print("INFO: Password set done")

    def config_setup(self, ip, port):
        print("INFO: Setting up dhcp config ")
        tn = telnetlib.Telnet(ip, port, 5)
        tn.write("\r\n")
        tn.write('root' + "\r\n")
        tn.write('lab' + "\r\n")
        tn.write('conf t' + "\r\n")
        tn.write('interface MgmtEth 0/RP0/CPU0/0' + "\r\n")
        tn.write('ipv4 address dhcp' + "\r\n")
        tn.write('no shut' + "\r\n")
        tn.write('commit' + "\r\n")
        tn.write('exit' + "\r\n")
        tn.write('exit' + "\r\n")
        tn.write('conf t' + "\r\n")
        tn.write('router static' + "\r\n")
        tn.write('address-family ipv4 unicast' + "\r\n")
        #TODO get this form ucs virbr0
        tn.write('0.0.0.0/0 MgmtEth 0/RP0/CPU0/0 192.168.122.1' + "\r\n")
        tn.write('commit' + "\r\n")
        tn.write('exit' + "\r\n")
        tn.write('exit' + "\r\n")
        tn.write('exit' + "\r\n")
        tn.close
        print("INFO: config set done")

