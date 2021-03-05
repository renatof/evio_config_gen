#!/bin/bash

# Replace with the password you want for your MySQL server
MYSQL_ROOT_PASSWORD=$MYSQL_ROOT_PASSWORD
# Replace with the AWS instance's public IP address
AWS_SERVER_IP=$AWS_SERVER_IP

echo "Setting up Evio bootstrapping node with XMPP, TURN, and MySQL containers"

echo "Installing Docker..."

curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu bionic stable"
sudo apt-get update -y
sudo apt-get install -y openvswitch-switch \
                        python3 python3-pip python3-venv \
                        apt-transport-https \
                        ca-certificates \
                        curl git \
                        software-properties-common \
                        containerd.io \
                        docker-ce-cli \
                        docker-ce \
                        docker-compose

sudo groupadd -f docker
sudo usermod -a -G docker $USER
sudo chown $USER:$USER /var/run/docker.sock

echo "Setting Up coturn conf..."

mkdir coturn
cd coturn

echo "realm=local" > turnserver.conf
echo "fingerprint" >> turnserver.conf
echo "external-ip=$AWS_SERVER_IP" >> turnserver.conf
echo "listening-port=3478" >> turnserver.conf
echo "min-port=49160" >> turnserver.conf
echo "max-port=59200" >> turnserver.conf
echo "lt-cred-mech" >> turnserver.conf
echo "mysql-userdb=\"host=db dbname=turnserver user=root password=$MYSQL_ROOT_PASSWORD connect_timeout=300 read_timeout=30\"" >> turnserver.conf

cd ./..

echo "Starting Coturn, Mysql and Openfire..."

docker-compose up -d

echo "Waiting for Coturn, Mysql and Openfire..."
sleep 40

echo "Adding XMPP and TURN databases..."
sudo docker exec -it evio-mysql mysql -u root --password=$MYSQL_ROOT_PASSWORD -e "CREATE DATABASE openfire;"
sudo docker exec -it evio-mysql mysql -u root --password=$MYSQL_ROOT_PASSWORD -e "CREATE DATABASE turnserver;"

echo "Copying and loading Openfire schema to MySQL..."
sudo docker cp evio-openfire:/usr/share/openfire/resources/database/openfire_mysql.sql openfire_mysql.sql 
sudo docker cp openfire_mysql.sql evio-mysql:/openfire_mysql.sql
sudo docker exec -it evio-mysql mysql -u root --password=$MYSQL_ROOT_PASSWORD openfire -e "source /openfire_mysql.sql"

echo "Setting up TURN server schema for MySQL..."

sudo docker cp evio-coturn:/usr/share/turnserver/schema.sql turnserver.sql 
sudo docker cp turnserver.sql evio-mysql:/turnserver.sql
sudo docker exec -it evio-mysql mysql -u root --password=$MYSQL_ROOT_PASSWORD turnserver -e "source /turnserver.sql"

echo "Setting up db name in coturn's /etc/hosts..."
MYSQL_IP=`docker inspect evio-mysql|grep IPAddress|tail -1|awk '{print $2}'|sed 's/,//'|sed 's/"//'|sed 's/"//'`
echo "$MYSQL_IP db" > coturn-hosts
sudo docker cp coturn-hosts evio-coturn:/tmp/coturn-hosts
sudo docker exec -it evio-coturn sh -c 'cat /tmp/coturn-hosts >> /etc/hosts'

echo "Now you need to perform the initial setup of Openfire server"
echo "------------------------------------------------------------"
echo "Insecure method: Cleartext http over the Internet! Use at your own risk:"
echo "  using your browser, go to http://$AWS_SERVER_IP:9090"
echo "You are encouraged to connect via an ssh tunnel"
echo "  open a new terminal on your client and ssh to this instance with your key:"
echo "  ssh -i your_aws_key.pem -L 127.0.0.1:9090:$AWS_SERVER_IP:9090 ubuntu@$AWS_SERVER_IP"
echo "  using your browser, go to http://127.0.0.1:9090"
echo "------------------------------------------------------------"
echo "Select your language; click Continue"
echo "Set XMPP Domain Name, Server Host Name as follows:"
echo "  If you don't have a DNS name for your instance: use openfire.local for both"
echo "  If you have a DNS name mapped to your instance, use the FQDN DNS name for both"
echo "  For the docker-compose based deployment : use evio-openfire for both"
echo "Click Continue"
echo "Select "Standard database connection" (which is not the default option), click Continue"
echo "In "Pick Database": select MySQL from drop down"
echo "replace Database URL with the following string to connect to your other container:"
echo "  jdbc:mysql://db:3306/openfire"
echo "set username: root"
echo "set password: $MYSQL_ROOT_PASSWORD"
echo "Profile settings: Default"
echo "Set your admin email and password for Openfire"
echo "  you will use this password you need to login back again as "admin" to http://$AWS_SERVER_IP:9090"
echo "------------------------------------------------------------"
echo "*AFTER* you are done with all the steps above, press Enter to continue..."

read -p "Press enter to continue"

echo "Configuring Openfire with plain password storage..."
echo "This is needed by Evio account creation scripts"
sudo docker exec -it evio-mysql mysql -u root --password=$MYSQL_ROOT_PASSWORD openfire -e "INSERT INTO ofProperty (name, propValue) VALUES ('user.usePlainPassword','true');"

echo "Done!"
