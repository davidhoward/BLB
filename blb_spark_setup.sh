#!/bin/bash

#get general asp framework and blb specializer
cd ~
#git clone git://github.com/shoaibkamil/asp.git
git clone git://github.com/pbirsinger/aspNew.git
mv aspNew/ asp/
git clone git://github.com/davidhoward/BLB.git

#compile spark
cd /root/spark
# git pull
# sbt/sbt compile
# sbt/sbt package 
sbt/sbt assembly

#SPARK_JAR=$(sbt/sbt assembly | grep "Packaging" | sed 's/ .* \(\/.*\) .../\1/' | sed 's/\[.*\]/ /')
#sbt/sbt package  ??
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

cd ..
mkdir java_avro
cd java_avro
#wget http://www.trieuvan.com/apache/avro/avro-1.6.3/java/avro-1.6.3.jar
wget http://www.bizdirusa.com/mirrors/apache/avro/avro-1.7.4/java/avro-1.7.4.jar
unzip avro-1.7.4.jar
mv org /root/avro

#install jackson (java json processor)
cd ..
#wget http://jackson.codehaus.org/1.9.6/jackson-all-1.9.6.jar
wget http://jackson.codehaus.org/1.9.11/jackson-all-1.9.11.jar
unzip jackson-all-1.9.6.jar

#make sure scala is on PATH
echo "export PATH=$PATH:/root/scala-2.9.2/bin" >> /root/.bash_profile

#point CLASSPATH to spark, avro,etc
#echo "export CLASSPATH=$CLASSPATH:.:/root/avro:/root/BLB/distr_support:/root/spark/core/target/spark-core-assembly-0.8.0-SNAPSHOT.jar" >> /root/.bash_profile
echo "export CLASSPATH=$CLASSPATH:/root/:.:/root/avro:/root/BLB/distr_support:/root/spark/core/target/spark-core-assembly-0.7.0.jar" >> /root/.bash_profile

#echo "export CLASSPATH=$CLASSPATH:.:/root/avro:/root/BLB/distr_support:$SPARK_JAR" >> /root/.bash_profile

#store MASTER node address
#echo "export MASTER=master@$(curl -s http://169.254.169.254/latest/meta-data/public-hostname):5050" >> /root/.bash_profile
echo "export MASTER=mesos://$(curl -s http://169.254.169.254/latest/meta-data/public-hostname):5050" >> /root/.bash_profile
source /root/.bash_profile

#download classifier models and data (for enron email example) from s3 and send to slave nodes
mkdir /root/test_examples
mkdir /root/test_examples/models
cd /root/test_examples/models

#wget https://s3.amazonaws.com/halfmilEmail/comp113kmodel.avro
#wget https://s3.amazonaws.com/halfmilEmail/comp250kmodel.avro
#wget https://s3.amazonaws.com/1.2milemails/model.avro
#wget https://s3.amazonaws.com/icsi_blb/e1-15double.model.java

mkdir /root/test_examples/data
cd /root/test_examples/data
#wget https://s3.amazonaws.com/halfmilEmail/seq113ktest
#wget https://s3.amazonaws.com/halfmilEmail/seq250ktest
#wget https://s3.amazonaws.com/entire_corpus/seq_test

mkdir -p /mnt/test_examples/data
cd /mnt/test_examples/data
wget https://s3.amazonaws.com/ngrams_blb/10_percent_cleaned_blb.seq

/root/spark-ec2/copy-dir /mnt/test_examples

#compile some java/scala files and send to slave nodes
cd /root/asp/asp/avro_inter
scalac scala_lib.scala
javac -d ../avro_inter/ JAvroInter.java

cp -r /root/asp/asp/avro_inter/* /root/avro
/root/spark-ec2/copy-dir /root/avro

#add permissions, and compile another scala file
cd /root/BLB/
chmod +x run_dist_tests.sh
scalac -d distr_support/ distr_support/custom_data.scala
scalac -d distr_support/ distr_support/kryoreg.scala

mkdir /root/BLB/distr_support/dependencies 
chmod +x /root/BLB/distr_support/make_dependency_jar
chmod +x /root/asp/asp/jit/make_source_jar




