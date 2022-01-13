# evio_config_gen

### Preflight check, Make sure you have 'sudo' privileges by:

	sudo -l

### Clone this deployment script for EVIO by:

	git clone https://github.com/renatof/evio_config_gen.git 

### change directory to Scripts directory:

	cd evio_config_gen

### Export Mysql root password in Environment Variable:

	export MYSQL_ROOT_PASSWORD="Enter mysql root password here"

### Export AWS SERVER browseable IP as Environment Variable:

	export AWS_SERVER_IP="Enter IP Here"

### Setup EVIO on any Debian/Ubuntu based OS by running :

	bash setup_evio_bootstrap_server_docker-compose.sh

### Create XMPP/TURN user accounts, and Evio configuration files

	export AWS_SERVER_IP="Enter IP Here"
	cd evio_config_gen
	vi generate_evio_config_trial.py

### Additional configuration

	- If you are using a numeric IP address without DNS configured, enter the AWS public IP address and set the 		XMPP_DOMAIN as openfire.local: SERVER_ADDRESS: AWS_SERVER_IP XMPP_DOMAIN: openfire.local

	- If you do have a valid public DNS mapping for your server, enter its fully qualified domain name (FQDN) for both: SERVER_ADDRESS: FQDN XMPP_DOMAIN: FQDN for e.g. ec2-18-101-100-231.us-...

### create a five test accounts and an overlay named Test1

	cd ~/evio-config-gen
	bash test_accounts_creation.sh

### Write the created accounts in the Database

	cd Test1
	chmod 755 *.sh
	./docker-config-openfire-turn.sh

### To (re) start services

	cd ~/evio-config-gen
	docker-compose down
	docker-compose up -d

### Follow the instructions on one of the following links

	--> Installation instruction of EdgeVPN on your local Machine:  https://edgevpn.io/install/
	--> Installation instructions of EdgeVPN with Docker: https://edgevpn.io/dockeredgevpn/