import java.util.ArrayList;
import spark._
import SparkContext._
import javro.scala_arr
import javro.JAvroInter
import org.apache.hadoop.io._
import org.apache.avro.generic.GenericData;
import org.apache.avro.generic.GenericDatumReader;
import org.apache.avro.generic.GenericDatumWriter;
import org.apache.avro.generic.GenericRecord;

/**
*  converts featureVec from string format into FeatureVec class
**/
def formatCompressedFeatureVec(input: String): FeatureVec={
        var vector = input.split(" ")
        var featureVec = new FeatureVec()
        featureVec.vec_indices = new Array[Int](vector.length-1)
        featureVec.vec_weights = new Array[Int](vector.length-1)

        var first = true
        var num = 0
        var weight = 0
        var count = 0
        for (elem <- vector){
                if (first){
                        featureVec.tag = Integer.parseInt(elem)
                        first = false
                }
                else {
                        num = Integer.parseInt(elem.substring(0, elem.indexOf(':')))
                        weight = Integer.parseInt(elem.substring(elem.indexOf(':')+1, elem.length))
                        featureVec.vec_indices(count) = num
                        featureVec.vec_weights(count) = weight
                        count += 1
                }
        }
        return featureVec
}

def formatFeatureVec(input: String): FeatureVec={
        var vector = input.split(" ")
        var featureVec = new FeatureVec()
        featureVec.vec_weights = new Array[Double](vector.length-1)

        var first = true
        var num = 0
        var weight = 0.0
        var count = 0
        for (elem <- vector){
                if (first){
                        featureVec.tag = Integer.parseInt(elem)
                        first = false
                }
                else {
                        weight = java.lang.Double.parseDouble((elem.substring(elem.indexOf(':')+1, elem.length)))
                        featureVec.vec_weights(count) = weight
                        count += 1
                }
        }
        return featureVec
}

/**
*  formatting of the input data can be done here
*  note that the input types may have to be adjusted
**/
def formatInputItem(input: String): FeatureVec={
        return formatFeatureVec(input)
}

/**
 * performs a dot product between a compressed model vector and a
 * compressed featureVec vector stored in the FeatureVec class
**/

/**
def custom_dot_both_compressed(model: ArrayList[Float], featureVec: FeatureVec): Double ={
    var featureVec_indices = featureVec.vec_indices
    var featureVec_weights = featureVec.vec_weights
    var total =0.0
    var featureVec_index = 0.0
    var featureVec_weight = 0.0
    var model_index = -1.0
    var model_weight =0.0
    var model_index_counter = -2 
    var i = 0

    //for (i <- Range(0, featureVec_indices.length)){
    while (i < featureVec_indices.length){
            featureVec_index = featureVec_indices(i)
            while (model_index < featureVec_index && model_index_counter+2 < model.size){
                    model_index_counter += 2
                    model_index = model.get(model_index_counter)
            }
            if (model_index == featureVec_index){
                    featureVec_weight = featureVec_weights(i)
                    model_weight = model.get(model_index_counter+1)
                    total += featureVec_weight * model_weight
            }
	i += 1
    }
    return total
}
**/

    def custom_dot_uncompressed(model:Array[Double], featureVec:FeatureVec): Double = {
        var featureVec_weights = featureVec.vec_weights
        var total =0.0
        var featureVec_weight = 0.0
        var model_weight = model(0)
        var i = 0
        while (i < featureVec_weights.length){
            featureVec_weight = featureVec_weights(i)
            total += featureVec_weight * model(i+1)
            i += 1
        }

        return total*model_weight
    }

def readVecs(filename: String): Array[Array[Array[Double]]]= {
	var f_in: FileInputStream = new FileInputStream(filename)
	var obj_in: ObjectInputStream = new ObjectInputStream(f_in)
	var modelMatrix: Array[Array[Array[Double]]] = obj_in.readObject().asInstanceOf[Array[Array[Array[Double]]]]
	return modelMatrix
}

def run(data_filename: String, model_filename:String, DIM: Int,
                        num_subsamples:Int, num_bootstraps:Int, subsample_len_exp:Double):Double={

    // probably want to set parallelism to num_nodes * num_cores/node * 2 (or 3)
    val NUM_TASKS = "16"
    System.setProperty("spark.default.parallelism", NUM_TASKS)
    System.setProperty("spark.serializer", "spark.KryoSerializer")
    System.setProperty("spark.kryo.registrator", "MyRegistrator")

    // SOURCE_LOC is set to the file_path of the jar containing the necessary files in /asp/jit/scala_module.py
    // DEPEND_LOC is set to the file_path of the jar containing the necessary dependencies for the BLB app
    val sc = new SparkContext(System.getenv("MASTER"), "Blb", "/root/spark", List(System.getenv("SOURCE_LOC"),
        System.getenv("DEPEND_LOC")))
    val bnum_bootstraps = sc.broadcast(num_bootstraps)
    val bsubsample_len_exp = sc.broadcast(subsample_len_exp)
    val bnum_subsamples = sc.broadcast(num_subsamples)

    val distData = sc.sequenceFile[Int, String](data_filename)

	/**
    val reader =(new JAvroInter("res.avro", "args.avro")).readModel(model_filename)
    var models_arr = List[java.util.ArrayList[Float]]()
    while (reader.hasNext()){
        models_arr = models_arr :+ new ArrayList(reader.next().get(1).asInstanceOf[org.apache.avro.generic.GenericData.Array[Float]].asInstanceOf[java.util.List[Float]])
   }
	**/
	
	val models_arr: Array[Array[Array[Double]]] = readModelsVec(model_filename)
    val models = sc.broadcast(models_arr)

    val data_count = distData.count().asInstanceOf[Int]
    val broadcast_data_count = sc.broadcast(data_count)
    val rand_prob = sc.broadcast(math.pow(data_count, subsample_len_exp)/data_count)

    var subsamp_estimates = distData.flatMap(item =>{
        val gen = new java.util.Random()
        var subsamp_count = 1
        var outputs = List[(Int, FeatureVec)]()
        var prob =0.0
        val funcs = new run_outer_data()

        //choose subsamples and replicate them
        for (i <- Range(0, bnum_subsamples.value)){
                prob = gen.nextDouble()
                if (prob < rand_prob.value){
                        for (i <- Range((subsamp_count-1) * bnum_bootstraps.value , subsamp_count*bnum_bootstraps.value)){
                                outputs ::= (i, funcs.formatInputItem(item._2))
                        }
                }
                subsamp_count += 1
        }
        outputs
    }).groupByKey().map(subsamp => {
        val funcs = new run_outer_data()
        var btstrap_vec = subsamp._2.toIndexedSeq

        val gen = new java.util.Random()
        val btstrap_len = btstrap_vec.size
        var subsamp_weights = new Array[Int](btstrap_vec.size)

        for (i <- Range(0, broadcast_data_count.value)){
                subsamp_weights(gen.nextInt(btstrap_len)) += 1
        }

        //for (temp <- btstrap_vec zip subsamp_weights)
        for (i <- Range(0, subsamp_weights.length)){
                btstrap_vec(i).weight = subsamp_weights(i)
        }

        val btstrap_data = new BootstrapData()
        btstrap_data.data = btstrap_vec.toList
        btstrap_data.models = models.value
        val est = funcs.compute_estimate(btstrap_data)
        val subsamp_id = subsamp._1/bnum_bootstraps.value + 1
        (subsamp_id, est)

    }).groupByKey().map(bootstrap_estimates =>{
        val funcs = new run_outer_data()
        funcs.reduce_bootstraps(bootstrap_estimates._2.toList)
    }).collect()

    var result = average(subsamp_estimates)
    return result
}

