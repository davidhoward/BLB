!/bin/bash

git clone git://github.com/pbirsinger/asp.git
#git clone git://github.com/pbirsinger/SPARK_BLB.git
git clone git://github.com/davidhoward/BLB.git

cd /root/spark
sbt/sbt assembly

cd /root
mkdir asp_extra
cd asp_extra
wget http://pypi.python.org/packages/source/c/codepy/codepy-2012.1.2.tar.gz#md5=992482e56aa3f5351a08e4c39572bc3a
tar -zxvf codepy-2012.1.2.tar.gz
cd codepy-2012.1.2
python setup.py build
python setup.py install
yum -y install numpy

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

cd ..

wget http://jackson.codehaus.org/1.9.6/jackson-all-1.9.6.jar
unzip jackson-all-1.9.6.jar

echo "export CLASSPATH=\$CLASSPATH:.:/root/avro:/root/BLB/distr_support:/root/spark/core/target/spark-core-assembly-0.4-SNAPSHOT.jar" >> /root/.bash_profile
echo "export MASTER=master@$(curl -s http://169.254.169.254/latest/meta-data/public-hostname):5050" >> /root/.bash_profile
source /root/.bash_profile

mkdir /root/models
cd /root/models
wget https://s3.amazonaws.com/halfmilEmai l/comp113kmodel.avro
wget https://s3.amazonaws.com/halfmilEmail/comp250kmodel.avro
/root/mesos-ec2/copy-dir /root/models

cd /root/asp/asp/avro_inter
scalac scala_lib.scala
javac -d ../avro_inter/ JAvroInter.java

cp -r /root/asp/asp/avro_inter/* /root/avro
/root/mesos-ec2/copy-dir /root/avro


cd /root/BLB/
chmod +x run_dist_tests.sh
scalac -d distr_support/ distr_support/custom_data.scala

chmod +x /root/BLB/distr_support/make_dependency_jar
chmod +x /root/asp/asp/jit/make_source_jar




