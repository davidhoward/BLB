!/bin/bash

#get general asp framework and blb specializer
git clone git://github.com/shoaibkamil/asp.git
git clone git://github.com/davidhoward/BLB.git

#compile spark
cd /root/spark
sbt/sbt assembly

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
wget http://www.trieuvan.com/apache/avro/avro-1.6.3/java/avro-1.6.3.jar
unzip avro-1.6.3.jar
mv org /root/avro

#install jackson (java json processor)
cd ..
wget http://jackson.codehaus.org/1.9.6/jackson-all-1.9.6.jar
unzip jackson-all-1.9.6.jar


#point classpath to spark, avro,etc
echo "export CLASSPATH=\$CLASSPATH:.:/root/avro:/root/BLB/distr_support:/root/spark/core/target/spark-core-assembly-0.4-SNAPSHOT.jar" >> /root/.bash_profile

#store MASTER node address
echo "export MASTER=master@$(curl -s http://169.254.169.254/latest/meta-data/public-hostname):5050" >> /root/.bash_profile
source /root/.bash_profile

#download classifier models and data (for enron email example) from s3 and send to slave nodes
mkdir /root/enron_example
mkdir /root/enron_example/models
cd /root/enron_example/models
wget https://s3.amazonaws.com/halfmilEmail/comp113kmodel.avro
wget https://s3.amazonaws.com/halfmilEmail/comp250kmodel.avro

mkdir /root/enron_example/data
cd /root/enron_example/data
wget https://s3.amazonaws.com/halfmilEmail/seq113ktest
wget https://s3.amazonaws.com/halfmilEmail/seq250ktest

/root/mesos-ec2/copy-dir /root/enron_example

#compile some java/scala files and send to slave nodes
cd /root/asp/asp/avro_inter
scalac scala_lib.scala
javac -d ../avro_inter/ JAvroInter.java

cp -r /root/asp/asp/avro_inter/* /root/avro
/root/mesos-ec2/copy-dir /root/avro

#add permissions, and compile another scala file
cd /root/BLB/
chmod +x run_dist_tests.sh
scalac -d distr_support/ distr_support/custom_data.scala

chmod +x /root/BLB/distr_support/make_dependency_jar
chmod +x /root/asp/asp/jit/make_source_jar




