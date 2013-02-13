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
*  converts email from string format into Email class
**/
def formatEmail(input: String): Email={
        var vector = input.split(" ")
        var email = new Email()
        email.vec_indices = new Array[Int](vector.length-1)
        email.vec_weights = new Array[Int](vector.length-1)

        var first = true
        var num = 0
        var weight = 0
        var count = 0
        for (elem <- vector){
                if (first){
                        email.tag = Integer.parseInt(elem)
                        first = false
                }
                else {
                        num = Integer.parseInt(elem.substring(0, elem.indexOf(':')))
                        weight = Integer.parseInt(elem.substring(elem.indexOf(':')+1, elem.length))
                        email.vec_indices(count) = num
                        email.vec_weights(count) = weight
                        count += 1
                }
        }
        return email
}

/**
*  formatting of the input data can be done here
*  note that the input types may have to be adjusted
**/
def formatInputItem(input: String): 
    Email={
        return formatEmail(input)
}

/**
 * performs a dot product between a compressed model vector and a
 * compressed email vector stored in the Email class
**/
def custom_dot(model: ArrayList[Float], email: Email): Double ={
    var email_indices = email.vec_indices
    var email_weights = email.vec_weights
    var total =0.0
    var email_index = 0.0
    var email_weight = 0.0
    var model_index = -1.0
    var model_weight =0.0
    var model_index_counter = -2 
    var i = 0

    //for (i <- Range(0, email_indices.length)){
    while (i < email_indices.length){
            email_index = email_indices(i)
            while (model_index < email_index && model_index_counter+2 < model.size){
                    model_index_counter += 2
                    model_index = model.get(model_index_counter)
            }
            if (model_index == email_index){
                    email_weight = email_weights(i)
                    model_weight = model.get(model_index_counter+1)
                    total += email_weight * model_weight
            }
	i += 1
    }
    return total
}

def run(email_filename: String, model_filename:String, DIM: Int,
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

    val distData = sc.sequenceFile[Int, String](email_filename)
    val reader =(new JAvroInter("res.avro", "args.avro")).readModel(model_filename)
    var models_arr = List[java.util.ArrayList[Float]]()
    while (reader.hasNext()){
        models_arr = models_arr :+ new ArrayList(reader.next().get(1).asInstanceOf[org.apache.avro.generic.GenericData.Array[Float]].asInstanceOf[java.util.List[Float]])
   }

    val models = sc.broadcast(models_arr)
    val data_count = distData.count().asInstanceOf[Int]
    val broadcast_data_count = sc.broadcast(data_count)
    val rand_prob = sc.broadcast(math.pow(data_count, subsample_len_exp)/data_count)

    var subsamp_estimates = distData.flatMap(item =>{
        val gen = new java.util.Random()
        var subsamp_count = 1
        var outputs = List[(Int, Email)]()
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
        btstrap_data.emails = btstrap_vec.toList
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

