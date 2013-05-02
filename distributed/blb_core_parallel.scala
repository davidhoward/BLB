import java.util.ArrayList;
import spark._
import SparkContext._
import scala.io._
import java.io._
import org.apache.hadoop.io._
import scala.collection.mutable.PriorityQueue
import scala.collection.JavaConversions._
import scala.collection.mutable.ListBuffer


def run(filenames: scala_arr[org.apache.avro.util.Utf8], NUM_TASKS: String, DIM: Int, numSubsamples:Int, numBootstraps:Int, subsampleLenExp:Double):java.util.List[Double]={

    System.setProperty("spark.default.parallelism", NUM_TASKS)
    System.setProperty("spark.serializer", "spark.KryoSerializer")
    System.setProperty("spark.rdd.compress", "true")
    System.setProperty("spark.kryo.registrator", "MyRegistrator")
    System.setProperty("spark.storage.StorageLevel", "MEMORY_ONLY_SER")
    System.setProperty("spark.kryoserializer.buffer.mb", "64")

    // SOURCE_LOC is set to the file_path of the jar containing the necessary files in /asp/jit/scala_module.py
    // DEPEND_LOC is set to the file_path of the jar containing the necessary dependencies for the BLB app
    val sc = new SparkContext(System.getenv("MASTER"), "Blb", "/root/spark", List(System.getenv("SOURCE_LOC"), System.getenv("DEPEND_LOC")))
    val bnumBootstraps = sc.broadcast(numBootstraps)
    val bnumSubsamples = sc.broadcast(numSubsamples)

    var dataFilename = filenames.apply(0)
    val distData = sc.textFile(dataFilename.toString())

    //put in try catch block ?
    var modelFilename = filenames.apply(1)
    val modelsArr = HelperFuncs.readModels(modelFilename.toString())
    val models = sc.broadcast(modelsArr)

    val dataCount = distData.count().asInstanceOf[Int]
    val broadcastDataCount = sc.broadcast(dataCount)
    val rand_prob = sc.broadcast(math.pow(dataCount, subsampleLenExp)/dataCount)

    var subsamp_estimates = distData.flatMap(item =>{
        val gen = new java.util.Random()
        var subsampCount = 1
        var prob =0.0
        var outputs = List((0, HelperFuncs.formatInputItem(item))).drop(1)
        //choose subsamples and replicate them
        for (i <- Range(0, bnumSubsamples.value)){
                prob = gen.nextDouble()
                if (prob < rand_prob.value){
                        for (i <- Range((subsampCount-1) * bnumBootstraps.value , subsampCount*bnumBootstraps.value)){
                            outputs ::= (i, HelperFuncs.formatInputItem(item))
                        }
                }
                subsampCount += 1
        }
        outputs
    }).groupByKey().map(subsamp => {
        var btstrapVec = subsamp._2.toIndexedSeq

        val gen = new java.util.Random()
        val btstrapLen = btstrapVec.size
        var subsamp_weights = new Array[Int](btstrapVec.size)

        for (i <- Range(0, broadcastDataCount.value)){
                subsamp_weights(gen.nextInt(btstrapLen)) += 1
        }

        //for (temp <- btstrapVec zip subsamp_weights)
        for (i <- Range(0, subsamp_weights.length)){
                btstrapVec(i).weight = subsamp_weights(i)
        }

        val btstrapData = new BootstrapData()
        btstrapData.data = btstrapVec.toList
        btstrapData.models = models.value
        val est = compute_estimate(btstrapData)
        //val est = HelperFuncs.compute_estimate(btstrapVec.toArray)

        val subsamp_id = subsamp._1/bnumBootstraps.value + 1
        (subsamp_id, est)

    }).groupByKey().map(bootstrap_estimates =>{
        reduce_bootstraps(bootstrap_estimates._2.toArray)
    }).collect()

    var result_arr = average(subsamp_estimates)
    return HelperFuncs.formatOutput(result_arr)
}

