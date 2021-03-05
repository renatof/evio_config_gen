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

### Export base IP address for Docker network

The docker compose deployment needs to create a docker network to bind the mysql/openfire containers too. Pick any address space that is available on your host (e.g. 172.16.238/24), but only use the first 3 bytes (separated by two dots, e.g. 172.16.238) when you configure this environment variable. The mysql container will bind to a static IP $EVIODB_DOCKER_NET.2 and openfire will bind to static IP $EVIODB_DOCKER_NET.3 - the coturn container binds to the host network, as it requires a large number of ports.

        export EVIODB_DOCKER_NET="172.16.238"

### Setup EVIO on any Debian/Ubuntu based OS by running :

	bash setup_evio_bootstrap_server_docker-compose.sh

