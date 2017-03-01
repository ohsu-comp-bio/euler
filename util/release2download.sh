
# based on https://discuss.icgc.org/t/handoff-between-dcc-release-and-dcc-download/125/9

# Update download server data
# For a release directory layout refer to the download server documentation: https://github.com/icgc-dcc/dcc-download/tree/develop/dcc-download-server#directories-layout

# dcc-release populated
SOURCE_HDFS_PATH=/dcc-release/work-icgc312-download
# dcc-download path
TARGET_HDFS_PATH=/bwalsh-release
# new release number
RELEASE_NUMBER=97


# setup ensure target exists
hdfs dfs -test -d $TARGET_HDFS_PATH && echo 'dir exists '$TARGET_HDFS_PATH || hdfs dfs -mkdir -p $TARGET_HDFS_PATH
hdfs dfs -test -d $TARGET_HDFS_PATH/download/release_$RELEASE_NUMBER && echo 'dir exists '$TARGET_HDFS_PATH/download/release_$RELEASE_NUMBER || hdfs dfs -mkdir -p $TARGET_HDFS_PATH/download/release_$RELEASE_NUMBER


# Used by dcc-download-import
# setup ensure target exists
hdfs dfs -test -d $TARGET_HDFS_PATH/es_export && echo 'dir exists '$TARGET_HDFS_PATH'/export/es_export' || hdfs dfs -mkdir -p $TARGET_HDFS_PATH/es_export
# First, update Elasticsearch export archives:
# backup our existing es index dir, if it exists
hdfs dfs -test -d $TARGET_HDFS_PATH/es_export  && hdfs dfs -mv $TARGET_HDFS_PATH/es_export $TARGET_HDFS_PATH/es_export.bak
# mv new es index dir
hdfs dfs -mv $SOURCE_HDFS_PATH/es_export $TARGET_HDFS_PATH/es_export
# remove our backup
hdfs dfs -rm -r -skipTrash $TARGET_HDFS_PATH/es_export.bak



# Secondly, move release clinical download files and prepare the standard directory layout:
hdfs dfs -mv $SOURCE_HDFS_PATH/export/* $TARGET_HDFS_PATH/download/release_$RELEASE_NUMBER
hdfs dfs -mkdir $TARGET_HDFS_PATH/download/release_$RELEASE_NUMBER/{projects_files,summary_files}
hdfs dfs -mv $SOURCE_HDFS_PATH/simple_somatic_mutation.aggregated.vcf.gz $TARGET_HDFS_PATH/download/release_$RELEASE_NUMBER/summary_files

# Next, update/add README.txt files:
echo 'TEST ROOT README RELEASE:'$RELEASE_NUMBER > /tmp/README.txt
hdfs dfs -put -f /tmp/README.txt $TARGET_HDFS_PATH/download/README.txt

echo 'TEST RELEASE README RELEASE:'$RELEASE_NUMBER > /tmp/README.txt
hdfs dfs -put /tmp/README.txt $TARGET_HDFS_PATH/download/release_$RELEASE_NUMBER/README.txt

echo 'TEST PROJECT FILES README RELEASE:'$RELEASE_NUMBER > /tmp/README.txt
hdfs dfs -put /tmp/README.txt $TARGET_HDFS_PATH/download/release_$RELEASE_NUMBER/projects_files/README.txt



# Lastly, trigger the download server to load the latest release files in memory:
# execute this from the same server dcc-download installed in
# see
# download.server:
#   adminUser: xxxx
#   adminPassword: yyyy
DOWNLOAD_SERVER=localhost:9092
DOWNLOAD_ADMIN_CREDENTIALS=xxxx:yyyy
curl -k -XPUT http://$DOWNLOAD_SERVER/srv-info/release/release_$RELEASE_NUMBER -u $DOWNLOAD_ADMIN_CREDENTIALS
