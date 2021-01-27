import sys
import os
import random
import string
import re
import shutil
import time
import argparse
from datetime import datetime
from tempfile import mkstemp

# is this going to be a debugging testbed with fixed nodeIDs?
# leave this as False, unless you want your nodes to have 
# statically defined nodeIds to help debugging
DEBUG_TESTBED = False
# public address of the server hosting the containers
# this can be the IP address of your EC2 instance, or
# a DNS domain name bound to it
SERVER_ADDRESS = 'trial.edgevpn.io'
# domain name of XMPP server
# This can be the same as SERVER_ADDRESS (if you have a DNS entry mapped to your instance), 
# or openfire.local (if you don't have DNS mapped and use an IP address)
XMPP_DOMAIN = 'trial.edgevpn.io'
# Password length
RANDOM_STRING_LENGTH = 16
# Name of MySQL user
MYSQL_USER = 'root'
# IP address of MySQL server
MYSQL_IP = '172.17.0.2'
# Name of turn and openfire MySQL databases
MYSQL_TURN_DB = 'turnserver'
MYSQL_OPENFIRE_DB = 'openfire'
# Name of turn realm for users
TURN_REALM = 'local'

# Name of MySQL container
MYSQL_CONTAINER = 'evio-mysql'
# Name of turn server container
TURN_CONTAINER = 'evio-coturn'
# Configuration generation script
CONFIG_GEN_SCRIPT = 'docker-config-openfire-turn.sh'

# File with configuration template for Evio config
CONFIG_TEMPLATE = 'config-gen-template.json'
# File with configuration template for Evio config - with fixed nodeId for testing
CONFIG_TEMPLATE_NODEID = 'config-gen-template-nodeid.json'
# Prefix and postfix for generated configuration files
CONFIG_TEMPLATE_OUT_PRE = 'config-'
CONFIG_TEMPLATE_OUT_POS = '.json'

# Postfix for sql and turn files
# MySQL statements for openfire db
OF_SQL_TEMPLATE_OUT_POS = '_of.sql'
# Bash script to load MySQL statements for openfire db
OF_SQL_SCRIPT_POS = '_of.sh'
# Bash script to run turnadmin commands for coturn
TURNADMIN_TEMPLATE_OUT_POS = '_turnadmin.sh'

# Pattern-matching in the json config file - these are substituted by sed
SERVER_ADDRESS_STRING = 'SERVER_ADDRESS'
XMPP_DOMAIN_STRING = 'XMPP_DOMAIN'
XMPP_USER_STRING = 'XMPP_USER'
XMPP_PASSWORD_STRING = 'XMPP_PASSWORD'
TURN_USER_STRING = 'TURN_USER'
TURN_PASSWORD_STRING = 'TURN_PASSWORD'
NODE_IP_STRING = 'NODE_IP'
NODE_BASE_IP_STRING = 'NODE_BASE_IP'
NODE_ID_STRING = 'XYZ'
OVERLAY_ID_STRING = 'OVERLAY_ID'

def int_to_three_char(i):
    if i>= 1000:
        print ("Error: " + str(i) + " greater than 1000")
        exit
    if i >= 100:
        return str(i)
    if i>= 10:
        return '0' + str(i)
    return '00' + str(i)

def sed(pattern, replace, source, dest=None, count=0):
    """Reads a source file and writes the destination file.

    In each line, replaces pattern with replace.

    Args:
        pattern (str): pattern to match (can be re.pattern)
        replace (str): replacement str
        source  (str): input filename
        count (int): number of occurrences to replace
        dest (str):   destination filename, if not given, source will be over written.
    """

    fin = open(source, 'r')
    num_replaced = count

    if dest:
        fout = open(dest, 'w')
    else:
        fd, name = mkstemp()
        fout = open(name, 'w')

    for line in fin:
        out = re.sub(pattern, replace, line)
        fout.write(out)

        if out != line:
            num_replaced += 1
        if count and num_replaced > count:
            break
    try:
        fout.writelines(fin.readlines())
    except Exception as E:
        raise E

    fin.close()
    fout.close()

    if not dest:
        shutil.move(name, source)



class ConfigGen():
    def __init__(self, mysql_password, requestor_email, project_name, base_IP, overlay_id, num_accounts, num_nodes):
        # MySQL password
        self.mysql_password = mysql_password
        # email of the person requesting trial
        self.requestor_email = requestor_email
        # name of project - used to derive group name, and user names
        self.project_name = project_name
        # base IP address for Evio nodes - just the first three octets, e.g. 10.10.100
        self.base_IP = base_IP + '.0'
        self.email = requestor_email
        # self.username is the username assigned to a given config. file, and may repeat
        # self.username_unique does not repeat - one per unique num_accounts
        self.username = []
        self.username_unique = []
        self.password = []
        self.password_unique = []
        self.IP = []
        self.overlay_id = overlay_id
        self.num_nodes = num_nodes
        self.num_accounts = num_accounts
        pos = 0
        for i in range(0,self.num_accounts):
            userstr = project_name + "_node" + str(i+1)
            self.username_unique.insert(i, userstr)
            letters = string.ascii_lowercase
            passwordstr = ''.join(random.choice(letters) for k in range(RANDOM_STRING_LENGTH))
            self.password_unique.insert(i, passwordstr)
            for j in range(0,(self.num_nodes//self.num_accounts)):
                self.username.insert(pos, userstr)
                self.password.insert(pos, passwordstr)
                ipstr = base_IP + "." + str(pos+1)
                self.IP.insert(pos, ipstr)
                pos = pos+1

        # for i in range(0,NUM_NODES):
            # node IDs and IP addresses start from 1, not zero, e.g. project_node1 is x.x.x.1
            # ipstr = base_IP + "." + str(i+1)
            # self.IP.insert(i, ipstr)
            # userstr = project_name + "_node" + str(i+1) 
            # self.username.insert(i, userstr) 
            # letters = string.ascii_lowercase
            # passwordstr = ''.join(random.choice(letters) for i in range(RANDOM_STRING_LENGTH))
            # self.password.insert(i, passwordstr)

    # Write Evio config-00x.json configuration files
    # builds on sed-like Python function
    def WriteJson(self):
        for i in range(0,self.num_nodes):
            # print(XMPP_USER_STRING + " : " + self.username[i] + " , " + XMPP_PASSWORD_STRING + " : " + self.password[i])
            node_config = CONFIG_TEMPLATE_OUT_PRE + int_to_three_char(i+1) + CONFIG_TEMPLATE_OUT_POS
            # print (node_config)
            # This does a copy from template to node-specific node_config, starting from _node1
            # The config template is a level up in the file system
            if DEBUG_TESTBED == True:
                config_template_path = "../" + CONFIG_TEMPLATE_NODEID
            else:
                config_template_path = "../" + CONFIG_TEMPLATE
            sed (XMPP_USER_STRING, self.username[i], config_template_path, node_config)
            # Now sed in-place node_config
            sed (SERVER_ADDRESS_STRING, SERVER_ADDRESS, node_config)
            sed (XMPP_DOMAIN_STRING, XMPP_DOMAIN, node_config)
            sed (XMPP_PASSWORD_STRING, self.password[i], node_config)
            sed (TURN_USER_STRING, self.username[i], node_config)
            sed (TURN_PASSWORD_STRING, self.password[i], node_config)
            sed (NODE_BASE_IP_STRING, self.base_IP, node_config)
            sed (NODE_IP_STRING, self.IP[i], node_config)
            sed (OVERLAY_ID_STRING, self.overlay_id, node_config)
            if DEBUG_TESTBED == True:
                sed (NODE_ID_STRING, int_to_three_char(i+1), node_config)

    # Write MySQL statements to populate Openfire tables with users and groups
    def WriteOfSQL(self):
        # start from an empty file
        f = open(self.project_name + OF_SQL_TEMPLATE_OUT_POS, "w")
        f.close()
        # now append lines
        f = open(self.project_name + OF_SQL_TEMPLATE_OUT_POS, "a")
        for i in range(0,self.num_accounts):
            # get current timestamp in format used by table (miliseconds)
            now = time.time() * 1000
            timestamp = str(round(now))
            add_user_str = "INSERT INTO ofUser (username, email, iterations, plainPassword, creationDate, modificationDate) VALUES ('" + self.username_unique[i] + "', '" + self.email + "', 4096, '" + self.password_unique[i] + "', " + timestamp + ", " + timestamp + ");\n" 
            f.write(add_user_str)
        add_group_str = "INSERT INTO ofGroup (groupName) VALUES ('" + self.project_name + "');\n"
        f.write(add_group_str)
        for i in range(0,self.num_accounts):
            add_user_to_group_str = "INSERT INTO ofGroupUser (groupName, username, administrator) VALUES ('" + self.project_name + "', '" + self.username_unique[i] + "', 0);\n"
            f.write(add_user_to_group_str)
        add_group_prop_str = "INSERT INTO ofGroupProp (groupName, name, propValue) VALUES ('" + self.project_name + "', 'sharedRoster.displayName', '" + self.project_name + "');\n"
        f.write(add_group_prop_str)
        add_group_prop_str = "INSERT INTO ofGroupProp (groupName, name, propValue) VALUES ('" + self.project_name + "', 'sharedRoster.groupList', '');\n"
        f.write(add_group_prop_str)
        add_group_prop_str = "INSERT INTO ofGroupProp (groupName, name, propValue) VALUES ('" + self.project_name + "', 'sharedRoster.showInRoster', 'onlyGroup');\n"
        f.write(add_group_prop_str)
        f.close()

    # Write a script to load OfSQL statements into database
    def WriteOfSQLScript(self):
        # start from an empty file
        of_sql_file = self.project_name + OF_SQL_TEMPLATE_OUT_POS
        of_script_file = self.project_name + OF_SQL_SCRIPT_POS
        f = open(of_script_file, "w")
        f.close()
        # now append lines
        f = open(of_script_file, "a")
        bash_str = "#!/bin/sh\n\n"
        f.write(bash_str)
        bash_str = "mysql -u " + MYSQL_USER + " --password=" + self.mysql_password + " "  + MYSQL_OPENFIRE_DB + " < /" + of_sql_file + "\n"
        f.write(bash_str)
        f.close()

    # Write turnadmin commands to populate turnserver tables with users 
    def WriteTurnadmin(self):
        f = open(self.project_name + TURNADMIN_TEMPLATE_OUT_POS, "w")
        f.close()
        f = open(self.project_name + TURNADMIN_TEMPLATE_OUT_POS, "a")
        bash_str = "#!/bin/sh\n\n"
        f.write(bash_str)
        for i in range(0,self.num_accounts):
            add_turn_user_str = "turnadmin --mysql-userdb \"host=" + MYSQL_IP + " dbname=" + MYSQL_TURN_DB + " user=" + MYSQL_USER + " password=" + self.mysql_password +" connect_timeout=30 read_timeout=30\" -a -r " + TURN_REALM + " -u " + self.username_unique[i] + " -p " + self.password_unique[i] +"\n"
            f.write(add_turn_user_str)
        f.close()

    # Write configuration scripts for Docker containers
    def WriteDockerScripts(self):
        f = open(CONFIG_GEN_SCRIPT, "w")
        f.close()
        f = open(CONFIG_GEN_SCRIPT, "a")
        bash_str = "#!/bin/sh\n\n"
        f.write(bash_str)

        # Copy MySQL file to container
        of_sql_file = self.project_name + OF_SQL_TEMPLATE_OUT_POS
        bash_str = "docker cp " + of_sql_file + " " + MYSQL_CONTAINER + ":/" +  of_sql_file + "\n"
        f.write(bash_str)

        # Copy MySQL script to container, make it executable
        of_script_file = self.project_name + OF_SQL_SCRIPT_POS
        bash_str = "docker cp " + of_script_file + " " + MYSQL_CONTAINER + ":/" + of_script_file + "\n"
        f.write(bash_str)
        bash_str = "docker exec -it " + MYSQL_CONTAINER + " chmod 755 /" + of_script_file + "\n"
        f.write(bash_str)

        # Copy turn script to container, make it executable
        turn_script_file = self.project_name + TURNADMIN_TEMPLATE_OUT_POS
        bash_str = "docker cp " + turn_script_file + " " + TURN_CONTAINER + ":/" + turn_script_file + "\n"
        f.write(bash_str)
        bash_str = "docker exec -it " + TURN_CONTAINER + " chmod 755 /" + turn_script_file + "\n"
        f.write(bash_str)

        # Execute scripts
        bash_str = "docker exec -it " + MYSQL_CONTAINER + " /" + of_script_file + "\n"
        f.write(bash_str)
        bash_str = "docker exec -it " + TURN_CONTAINER + " /" + turn_script_file + "\n"
        f.write(bash_str)

        # Remove scripts - todo

        f.close()



if __name__ == "__main__":


    parser = argparse.ArgumentParser()
    parser.add_argument('--sqlpass', required=True, help='Password for MySQL root user', type=ascii)
    parser.add_argument('--email', required=True, help='Email associated with users to be created in MySQL database', type=ascii)
    parser.add_argument('--evioname', required=True, help='Name of the Evio network - limited to 7 characters: lower/uppercase letters, numbers, and special character _, e.g. ProjX_1', type=ascii)
    parser.add_argument('--baseip', required=True, help='Base IP address range, e.g. 10.10.100', type=ascii)
    parser.add_argument('--numnodes', required=True, help='Number of nodes to be created - maximum of 250', type=int)
    parser.add_argument('--numacct', required=True, help='Number of XMPP/TURN accounts to be created - must divide numnodes', type=int)

    args = parser.parse_args()
    argdict = vars(args)

    evioname = argdict['evioname']
    evioname_clean = evioname[1:len(evioname)-1]

    if len(evioname_clean) > 7:
        print('--evioname longer than 7 characters')
        exit()

    if argdict['numacct'] > argdict['numnodes']:
        print('--numacct cannot be greater than --numnodes')
        exit()

    if argdict['numnodes'] > 250:
        print('--numnodes cannot be greater than 250')
        exit()

    if argdict['numnodes'] % argdict['numacct']:
        print('--numacct must divide --numnodes')
        exit()

    baseip = argdict['baseip']
    baseip_clean = baseip[1:len(baseip)-1]

    ip_split = baseip_clean.split('.')
    first_byte = ip_split[0]
    second_byte = ip_split[1]
    third_byte = ip_split[2]

    if len(ip_split) != 3:
        print('--baseip should be top 3 bytes of base IP address, as in 10.10.100')
        exit()

    if first_byte not in {"10", "192", "172"}:
        print('--baseip first byte needs to be a private address: 10, 192, 172')
        exit()

    if (int(second_byte) < 1) or (int(second_byte) > 254):
        print('--baseip second byte must be a number between 1 and 254')
        exit()

    if (int(third_byte) < 1) or (int(third_byte) > 254):
        print('--baseip third byte must be a number between 1 and 254')
        exit()

    path = evioname_clean 
    try:
        os.mkdir(path)
    except OSError:
        print ("Creation of the directory %s failed; aborting" % path)
        exit()

    sqlpass = argdict['sqlpass']
    sqlpass_clean = sqlpass[1:len(sqlpass)-1]

    email = argdict['email']
    email_clean = email[1:len(email)-1]

    print ("Output files will be stored in the directory %s " % path)
    os.chdir(path)
    myConfigGen = ConfigGen(sqlpass_clean, email_clean, evioname_clean, baseip_clean, evioname_clean, argdict['numacct'], argdict['numnodes'])
    myConfigGen.WriteJson()
    myConfigGen.WriteOfSQL()
    myConfigGen.WriteTurnadmin()
    myConfigGen.WriteOfSQLScript()
    myConfigGen.WriteDockerScripts()
    print("Configuration files and scripts to configure MySQL have been generated.")
    print("Before deploying Evio nodes, you must load the new XMPP/TURN accounts into MySQL by running:")
    print("cd " + path)
    print("chmod 755 *.sh")
    print("./docker-config-openfire-turn.sh")

