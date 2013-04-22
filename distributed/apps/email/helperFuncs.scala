import java.util.ArrayList

object HelperFuncs {
    def formatInputItem(input: String): CompressedFeatureVec={
            var vector = input.split(" ")
            var featureVec = new CompressedFeatureVec()
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

    def formatOutput[A](input: A): A= {return input}

    def custom_dot_both_compressed(model: ArrayList[Float], featureVec: CompressedFeatureVec): Float ={
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

    //should probably change this to read just arrays .... like multimedia does ...
    // will require java serializing model and changing some types ..
    def readModels(modelFilename: String):List[java.util.ArrayList[Float]] ={
        val reader =(new JAvroInter("res.avro", "args.avro")).readModel(modelFilename)
        var models_arr = List[java.util.ArrayList[Float]]()
        while (reader.hasNext()){
            models_arr = models_arr :+ new ArrayList(reader.next().get(1).asInstanceOf[org.apache.avro.generic.GenericData.Array[Float]].asInstanceOf[java.util.List[Float]])
       }
    }
}

