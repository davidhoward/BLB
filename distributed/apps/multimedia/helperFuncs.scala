import java.util.ArrayList
import scala.collection.mutable.ListBuffer
import java.io.FileInputStream
import scala.collection.JavaConversions._
import java.io.ObjectInputStream

object HelperFuncs{
    def formatInputItem(input: String): FeatureVec={
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

    def formatOutput(arr: Array[Double]): java.util.List[Double] ={
        var result_java_list: java.util.List[Double] = ListBuffer( arr: _* )
        return result_java_list
    }    

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

    def readModels(filename: String): Array[Array[Array[Double]]]= {
        var f_in: FileInputStream = new FileInputStream(filename)
        var obj_in: ObjectInputStream = new ObjectInputStream(f_in)
        var modelMatrix: Array[Array[Array[Double]]] = obj_in.readObject().asInstanceOf[Array[Array[Array[Double]]]]
        return modelMatrix
    }
}