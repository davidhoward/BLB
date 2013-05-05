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
        var formattedInputItem = HelperFuncs.formatInputItem(item)
        //var outputs = List((0, formattedInputItem)).drop(1)
        var outputs = Array.fill(bnumSubsamples.value * bnumBootstraps.value){ (0,formattedInputItem) }
        //choose subsamples and replicate them for each bootstrap
        var i = 0
        var j = 0
        var index = 0
        while (i < bnumSubsamples.value){
            prob = gen.nextDouble()
            if (prob < rand_prob.value){
                j = (subsampCount-1) * bnumBootstraps.value 
                while (j < subsampCount*bnumBootstraps.value) {
                //for (j <- Range((subsampCount-1) * bnumBootstraps.value , subsampCount*bnumBootstraps.value)){
                    //outputs ::= (j, formattedInputItem)
                    outputs(index) = (j, formattedInputItem)
                    index += 1
                    j += 1
                }
            }
            subsampCount += 1
            i+=1
        }
        //outputs
        //outputs.slice(0,index).toIndexedSeq
        outputs.slice(0,index).toSeq
        //outputs.toList
    }).groupByKey().map(bootstrap => {
        var btstrapVec = bootstrap._2.toArray

        val gen = new java.util.Random()
        val btstrapLen = btstrapVec.size
        var subsamp_weights = new Array[Int](btstrapVec.size)

        var i = 0
        while (i < broadcastDataCount.value){
            subsamp_weights(gen.nextInt(btstrapLen)) += 1
            i+=1
        }

        i = 0
        while (i < subsamp_weights.length){
            btstrapVec(i).weight = subsamp_weights(i)
            i+=1
        }

        val est = compute_estimate(btstrapVec, models.value)
        //val est = HelperFuncs.compute_estimate(btstrapVec)

        val subsamp_id = bootstrap._1/bnumBootstraps.value + 1
        (subsamp_id, est)

    }).groupByKey().map(bootstrap_estimates =>{
        reduce_bootstraps(bootstrap_estimates._2.toArray)
    }).collect()

    var result_arr = average(subsamp_estimates)
    return HelperFuncs.formatOutput(result_arr)
}

