#!/usr/bin/python
import pexpect
import os
import pdb
import time
import re
import telnetlib

class MyTelnet(telnetlib.Telnet, object):
    def write(self,cmd):
        #Telnet.write(self, cmd.encode("ascii"))
        super(MyTelnet, self).write(cmd.encode("ascii"))

class BootSunstone(object):
    def __init__(self):
        self.server_name = ""
        self.server_user = ""
        self.server_pass = ""
        self.image_path  = ""
        self.user_dir    = ""
        self.virbr0_ip   = ""
        self.prompt      = "abcd1234#"

    def die(child, errstr):
        print errstr
        print child.before, child.after
        child.terminate()
        exit(1)

    def ssh_command (self, user, host, password):

        """This runs a command on the remote host."""
        print "INFO: Logging into", host

        ssh_newkey = 'Are you sure you want to continue connecting'
        child = pexpect.spawn('ssh %s@%s'%(user, host))
        child.logfile = open("/tmp/mylog", "w")
        child.delaybeforesend = 2
        #child.interact()
        i = child.expect([pexpect.TIMEOUT, 'password:', ssh_newkey])
        child.logfile_read = open("/tmp/simlaunch.log", "w")
        if i == 0: # Timeout
            self.die(child, 'ERROR!\nSSH timed out. Here is what SSH said:')
            return None
        if i == 2: # SSH does not have the public key. Just accept it.
            child.sendline ('yes')
            child.expect ('password: ')
            i = child.expect([pexpect.TIMEOUT, 'password: '])
            if i == 0: # Timeout
                self.die(child, 'ERROR!\nSSH timed out. Here is what SSH said:')
                return None
        if i == 1:
            child.sendline(password)
            child.expect(['Last login', '@', '#'])
            print self.user_dir
            child.sendline('')
            child.sendline('')
            child.sendline('export PS1="{}"'.format(self.prompt))
            child.flush()
            child.sendline('export PS1="{}"'.format(self.prompt))        
            child.expect(self.prompt)
            print "INFO: Removing old directories"
            cmd = 'rm -rf %s' % (self.user_dir)
            child.sendline(cmd)
            child.expect(self.prompt)
            print "INFO: Creating relevant directories"
            cmd = 'mkdir %s' % (self.user_dir)
            child.sendline(cmd)
            child.expect(self.prompt)
            cmd = 'cd %s' % (self.user_dir)
            child.sendline(cmd)
            child.expect(self.prompt)
            return child

    def launch_sim(self,child):
        print "INFO: Creating environment"
        cmd = 'source /auto/edatools/oicad/tools/vxr2_user/alpha/setup.sh'
        child.sendline(cmd)
        child.expect('INFO')
        print "INFO: Cleaning old sessions"
        child.sendline('sim end')
        child.expect(self.prompt)
        child.sendline('sim clean')
        child.expect(self.prompt)
        print "INFO: Creating sim-config "
        child.sendline('sim xrv9k')
        child.expect('xml')
        cmd = "sed -i -e \'s@PATH_TO_IMAGE@"+ self.user_dir + "/xrv9k-mini-x.iso" + "@g\' sim-config.xml"
        #pdb.set_trace()
        child.sendline(cmd)
        child.expect(self.prompt)
        #child.interact()
        pattern = 'Bridge name="virbr0"'
        cmd = "sed '/%s/{n;d;}' sim-config.xml | tac | sed '/%s/{n;d;}' | tac > sim-config.xml_new" %(pattern, pattern)
        child.sendline(cmd)
        child.expect(self.prompt)
        cmd = 'unalias cp'
        child.sendline(cmd)
        child.expect(self.prompt)
        cmd = 'cp sim-config.xml_new sim-config.xml'
        child.sendline(cmd)
        child.expect(self.prompt)
        #get virbr0 ip
        cmd = "ifconfig virbr0"
        child.flush()
        child.sendline(cmd)
        child.sendline("echo Wxyz1234")
        child.expect('Wxyz1234')
        output = child.before
        print "output %s" % (output)
        pat = re.compile(r"inet addr:(\d+\.\d+\.\d+\.\d+)")
        if pat.search(output):
            self.virbr0_ip = pat.search(output).group(1)
            print "INFO: virbr0 ip %s" %(self.virbr0_ip)
        else:
            print "ERROR: No virbr0 ip found for machine with ifconfig"
            exit(-1)
        print "INFO: Launching sim"
        cmd = "sim -n"
        child.sendline(cmd)
        child.expect('INFO')
        print "INFO: Waiting for sim to get ready"
        time.sleep(1000)
        cmd = "cat %s/p0gen0pc0/PortVector.txt | grep \'Submit\|serial0\'" %(self.user_dir)
        child.flush()
        child.sendline(cmd)
        child.sendline("echo Wxyz1234")
        child.expect('Wxyz1234')
        output = child.before
        ip_pat = re.compile("HostSubmit (\d+.\d+.\d*.\d*)")
        if ip_pat.search(output):
            ip = ip_pat.search(output).group(1)
        else:
            print "ERROR! IP not found "
            print output
            exit(-1)
        port_pat = re.compile("serial0 (\d+)")
        if port_pat.search(output):
            port = port_pat.search(output).group(1)
        else:
            print "ERROR! XR Port not found"
            print output
            exit(-1)
        return ip,port

    def copy_to_server(self, bootInfo):
        self.server_name = bootInfo['machine']
        self.server_user = bootInfo['username']
        self.server_pass = bootInfo['password']
        self.image_path  = bootInfo['image_path']
        self.user_dir    = bootInfo['user_dir']
        ssh_newkey = 'Are you sure you want to continue connecting'
        child = self.ssh_command (self.server_user, self.server_name, self.server_pass)
        child.expect(self.prompt)
        try:
            print "INFO:Copying image to remote server"
            command = "scp %s %s@%s:%s" % (self.image_path, self.server_user, self.server_name, self.user_dir)
            print command
            #child.interact()
            child.sendline(command)
            i = child.expect([pexpect.TIMEOUT, 'password:', ssh_newkey], timeout=9000)
            if i == 0: # Timeout
                self.die(child, 'ERROR!\nSSH timed out. Here is what SSH said:')
                return None
            if i == 2: # SSH does not have the public key. Just accept it.
                child.sendline ('yes')
                child.expect ('password: ')
                i = child.expect([pexpect.TIMEOUT, 'password: '])
                if i == 0: # Timeout
                    self.die(child, 'ERROR!\nSSH timed out. Here is what SSH said:')
                    return None
            if i == 1:
                child.sendline(self.server_pass)
                child.expect(self.prompt, timeout=9000)
        except Exception as e:
            print "ERROR! Something went wrong"
            print e
        return child


    def connect_telnet(self, ip, port):
        print "INFO: Setting up username password "
        tn = MyTelnet(ip, port, 5)
        tn.set_debuglevel(1)
        tn.write("\r\n")
        i = tn.expect(['Press RETURN to get started', 'Enter root-system username:'])
        if i[0] == 0:
            tn.write("\r\n")
            tn.read_until('Enter root-system username:')
            tn.write('root' + "\n")
        else:
            tn.write('root' + "\n")
        tn.read_until('Enter secret:')
        tn.write('lab' + "\n")
        tn.read_until('Enter secret again:')
        tn.write('lab' + "\n")
        tn.close
        print "INFO: Password set done"

    def config_setup(self, ip, port):
        print "INFO: Setting up dhcp config "
        tn = MyTelnet(ip, port, 5)
        tn.set_debuglevel(3)
        tn.write("\r\n")
        tn.read_until("Username:")
        tn.write('root' + "\n")
        tn.read_until("Password:")
        tn.write('lab' + "\n\n")
        time.sleep(3)
        tn.read_until('ios')
        tn.write('conf t' + "\n")
        tn.write('logging console disable' + "\n")
        tn.write('commit' +"\n")
        tn.write('interface MgmtEth 0/RP0/CPU0/0' + "\n")
        tn.write('ipv4 address dhcp' + "\n")
        tn.write('no shut' + "\n")
        tn.write('commit' + "\n")
        tn.write('exit' + "\n")
        tn.write('exit' + "\n")
        tn.write('conf t' + "\n")
        tn.write('router static' + "\n")
        tn.write('address-family ipv4 unicast' + "\n")
        #TODO get this form ucs virbr0
        tn.write('0.0.0.0/0 MgmtEth 0/RP0/CPU0/0 ' + self.virbr0_ip + "\n")
        tn.write('commit' + "\n")
        tn.write('exit' + "\n")
        tn.write('exit' + "\n")
        tn.write('exit' + "\n")
        tn.close
        print "INFO: config set done"

    def copy_packages_to_disk(self, ip, port, src_dir, dest_dir):
        print "INFO: Copying packages to disk "
        tn = MyTelnet(ip, port, 5)
        tn.set_debuglevel(5)
        tn.write("\r\n\n\n")
        tn.read_until('ios')
        tn.write('run' + "\r\n\n")
        tn.write('mkdir ' + dest_dir + "\n")
        tn.write('ip netns exec tpnns bash' + "\r\n\n") 
        tn.write(src_dir + "\r\n")
        tn.write(dest_dir + "\r\n")
        cmd = 'scp -r ' + self.server_user + '@' + self.virbr0_ip + ':' + src_dir + '/* ' +dest_dir
        print cmd
        tn.write(cmd + "\r\n")
        tn.read_until('password:')
        tn.write(self.server_pass + "\n")
        tn.read_until('node')
        tn.write('exit' + "\r\n")
        tn.write('exit' + "\r\n")
        tn.close
