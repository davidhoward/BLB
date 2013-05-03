#!/bin/bash

#export APP=email
export APP=multimedia
#export APP=ngrams
echo "export APP=$APP" >> /root/.bash_profile

#get general asp framework and blb specializer
cd ~
#git clone git://github.com/shoaibkamil/asp.git
git clone git://github.com/pbirsinger/aspNew.git
mv aspNew/ asp/
git clone git://github.com/davidhoward/BLB.git
git checkout $APP


#compile spark
cd /root/spark
# git pull
#sbt/sbt compile
# sbt/sbt package 
sbt/sbt assembly

echo 'SPARK_JAVA_OPTS+=" -Dspark.storage.blockManagerHeartBeatMs=120000"' >> /root/spark/conf/spark-env.sh
echo 'export SPARK_JAVA_OPTS' >> /root/spark/conf/spark-env.sh
~/spark-ec2/copy-dir /root/spark

#install codepy and numpy
cd /root
mkdir asp_extra
cd asp_extra
wget http://pypi.python.org/packages/source/c/codepy/codepy-2012.1.2.tar.gz#md5=992482e56aa3f5351a08e4c39572bc3a
tar -zxvf codepy-2012.1.2.tar.gz
cd codepy-2012.1.2
python setup.py build
python setup.py install
yum -y install numpy

#install apache avro data serialization for python and java
cd /root
mkdir avro
cd avro
wget http://apache.osuosl.org/avro/avro-1.6.3/py/avro-1.6.3.tar.gz
tar -zxvf avro-1.6.3.tar.gz
cd avro-1.6.3
python setup.py build
python setup.py install

cd /root/avro
mkdir java_avro
cd java_avro
#wget http://www.trieuvan.com/apache/avro/avro-1.6.3/java/avro-1.6.3.jar
wget http://www.bizdirusa.com/mirrors/apache/avro/avro-1.7.4/java/avro-1.7.4.jar
unzip avro-1.7.4.jar
mv org /root/avro

#install jackson (java json processor)
cd /root/avro
#wget http://jackson.codehaus.org/1.9.6/jackson-all-1.9.6.jar
wget http://jackson.codehaus.org/1.9.11/jackson-all-1.9.11.jar
unzip jackson-all-1.9.11.jar

#make sure scala is on PATH
echo "export PATH=$PATH:/root/scala-2.9.2/bin" >> /root/.bash_profile

#point CLASSPATH to spark, avro,etc
echo "export CLASSPATH=$CLASSPATH:/root/:.:/root/avro:/root/BLB/distributed:/root/BLB/distributed/apps/$APP/:/root/spark/core/target/*" >> /root/.bash_profile

echo "export NUM_SLAVE_NODES=$(~/ephemeral-hdfs/bin/hadoop dfsadmin -report | grep "Name:" | wc -l)" >> /root/.bash_profile
echo "export NUM_CORES_PER_NODE=$(nproc)" >> /root/.bash_profile

#store MASTER node address
echo "export MASTER=spark://$(curl -s http://169.254.169.254/latest/meta-data/public-hostname):7077" >> /root/.bash_profile
source /root/.bash_profile

mkdir -p /mnt/test_examples/models
mkdir /mnt/test_examples/data

if [ $APP == "multimedia" ] ; then
	cd /mnt/test_examples/models
	wget https://s3.amazonaws.com/icsi_blb/e1-15double.model.java.gz
	gunzip *.gz 

	cd /mnt/test_examples/data
	#wget https://s3.amazonaws.com/icsi_blb/500e1-15.dat.gz
	#wget https://s3.amazonaws.com/icsi_blb/20percente1-15.dat.gz
	wget https://s3.amazonaws.com/icsi_blb/40percentE1-15.dat.gz
	#wget https://s3.amazonaws.com/icsi_blb/e1-15.dat.gz
	gunzip *.gz

elif [ $APP = "email" ]; then
	cd /mnt/test_examples/models
	wget https://s3.amazonaws.com/1.2milemails/emails.model.java

	cd /mnt/test_examples/data
	#wget https://s3.amazonaws.com/halfmilEmail/seq113ktest
	#wget https://s3.amazonaws.com/halfmilEmail/seq250ktest
	#wget https://s3.amazonaws.com/entire_corpus/seq_test
	wget https://s3.amazonaws.com/1.2milemails/1.2milemailstest.dat.gz
	gunzip *.gz

	REPL_FACTOR=50
	for (( k=0; k<=$REPL_FACTOR; k++));do
		cat 1.2milemailstest.dat >> $REPL_FACTORemails.dat
	done 

elif [ $APP = "ngrams" ]; then
	cd /mnt/test_examples/data
	wget https://s3.amazonaws.com/ngrams_blb/10_percent_cleaned_blb.seq
fi

#/root/ephemeral-hdfs/bin/hadoop dfs -rmr /test_examples
/root/ephemeral-hdfs/bin/hadoop dfs -put /mnt/test_examples /
#/root/spark-ec2/copy-dir /mnt/test_examples/

#compile some java/scala files and send to slave nodes
cd /root/asp/asp/avro_inter
scalac scala_lib.scala
javac JAvroInter.java

cp -r /root/asp/asp/avro_inter/* /root/avro
/root/spark-ec2/copy-dir /root/avro

#add permissions, and compile another scala file
cd /root/BLB/distributed/apps/$APP/
scalac *.scala
cd /root/BLB/distributed/
scalac kryoreg.scala

mkdir /root/BLB/distributed/dependencies 
chmod +x /root/BLB/distributed/make_dependency_jar /root/asp/asp/jit/make_source_jar /root/BLB/run_dist_tests.sh



