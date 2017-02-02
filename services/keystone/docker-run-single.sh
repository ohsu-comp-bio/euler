docker run --env-file $PWD/../../.env -v $PWD/../../.db:/db --network host --add-host controller:127.0.0.1 --hostname controller --name keystone -d keystone
