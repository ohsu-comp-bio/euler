#!/bin/bash

if [ "$#" -ne 1 ]; then
    echo "Illegal number of parameters. Usage: $0 bd2k_admin_id"
    exit 1
fi

echo "BD2K admin: please be ready to enter passphrase for RSA key."
echo "BD2K admin: please be ready to enter your bd2k admin pass."
scp $1@exacloud.ohsu.edu:~/.bd2k/bd2k.db .

cmd1='source ~/openrc'
cmd2='openstack domain create bd2k'
docker exec keystone bash -c "$cmd1; $cmd2"

sleep 5

for pass_pair in $(sqlite3 bd2k.db "select * from users";)
do
    sleep 5

    user="$(cut -d '|' -f 1 <<< "$pass_pair")"
    pass="$(cut -d '|' -f 2 <<< "$pass_pair")"

    cmd2='openstack user create --password '$pass' --domain bd2k '$user
    docker exec keystone bash -c "$cmd1; $cmd2"

    sleep 5

    sql='select project_id from project_users where user_id="'$user'"'
    for project in $(sqlite3 bd2k.db "$sql";)
    do
        cmd2='openstack role add --project '$project' --user '$user' --user-domain bd2k member'
        echo docker exec keystone bash -c "$cmd1; $cmd2"
    done

done

rm -rf bd2k.db
