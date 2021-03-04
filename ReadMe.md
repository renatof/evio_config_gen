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

