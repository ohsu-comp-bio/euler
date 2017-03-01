alias up="docker-compose -f docker-compose.yml -f docker-compose-development.yml -f docker-compose-openstack.yml up"
alias stop="docker-compose -f docker-compose.yml -f docker-compose-development.yml -f docker-compose-openstack.yml stop"
alias build="docker-compose -f docker-compose.yml -f docker-compose-development.yml -f docker-compose-openstack.yml  build"

execfunction() {
    docker exec -it $1 bash
}
alias exec=execfunction

recreatefunction() {
    stop $1 ; docker rm $1 ; docker rmi euler_$1 ; up -d $1
}
alias recreate=recreatefunction
